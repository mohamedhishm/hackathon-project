"""Cash flow forecasting, recurrence detection, and FX conversion engine.

Simulates user balance over a 91-day horizon [D0, D0 + 90] starting at
D0 = request.request_date.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
import numpy as np
from typing import Mapping, Sequence

from data_loader import FinancialEvent, Profile, Request
from evidence import ExtractedMessageEvidence, extract_message_evidence


def convert_currency(
    amount: Decimal,
    from_curr: str,
    to_curr: str,
    rate_date: date,
    exchange_rates: Mapping[tuple[date, str, str], Decimal],
) -> Decimal:
    """Converts amount from from_curr to to_curr using fixed exchange rates."""
    if from_curr == to_curr or amount == 0:
        return amount

    # 1. Exact date direct rate
    if (rate_date, from_curr, to_curr) in exchange_rates:
        return amount * exchange_rates[(rate_date, from_curr, to_curr)]

    # 2. Exact date inverted rate
    if (rate_date, to_curr, from_curr) in exchange_rates:
        return amount / exchange_rates[(rate_date, to_curr, from_curr)]

    # 3. Nearest earlier date rate
    all_dates = sorted([
        d for (d, fc, tc) in exchange_rates.keys()
        if (fc == from_curr and tc == to_curr) or (fc == to_curr and tc == from_curr)
    ])
    if all_dates:
        best_d = max([d for d in all_dates if d <= rate_date], default=all_dates[0])
        if (best_d, from_curr, to_curr) in exchange_rates:
            return amount * exchange_rates[(best_d, from_curr, to_curr)]
        elif (best_d, to_curr, from_curr) in exchange_rates:
            return amount / exchange_rates[(best_d, to_curr, from_curr)]

    return amount


def get_next_month_date(dt: date, day_of_month: int) -> date:
    """Computes next month's date clamping day for shorter months."""
    year = dt.year
    month = dt.month + 1
    if month > 12:
        month = 1
        year += 1
    if month == 2:
        day = min(day_of_month, 28)
    elif month in (4, 6, 9, 11):
        day = min(day_of_month, 30)
    else:
        day = min(day_of_month, 31)
    return date(year, month, day)


@dataclass(frozen=True)
class RecurringStream:
    event_type: str
    category: str
    description: str
    direction: str
    cadence: str  # 'monthly', 'weekly', 'biweekly'
    last_event: FinancialEvent
    last_date: date
    base_amount: Decimal
    currency: str
    flexibility: str | None
    minimum_allowed_amount: Decimal | None


def detect_recurring_streams(
    user_events: Sequence[FinancialEvent],
    d0: date,
) -> list[RecurringStream]:
    """Detects recurring financial streams based on cadence and amount consistency."""
    all_valid = [
        e for e in user_events
        if e.status in ('settled', 'scheduled') and e.amount is not None
    ]
    streams: dict[tuple[str, str, str, str], list[FinancialEvent]] = defaultdict(list)
    for e in all_valid:
        if e.event_type in ('expense', 'subscription', 'debt_payment', 'income'):
            streams[(e.event_type, e.category, e.description, e.direction)].append(e)

    recurring: list[RecurringStream] = []
    for (etype, cat, desc, direction), ev_list in streams.items():
        ev_list.sort(key=lambda x: (x.settlement_date or x.event_date))
        dates = [e.settlement_date or e.event_date for e in ev_list]
        deltas = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]

        is_salary = (etype == 'income' and cat == 'salary')
        if not is_salary and len(ev_list) < 2:
            continue

        median_delta = float(np.median(deltas)) if len(deltas) > 0 else 30.0
        is_monthly = is_salary or (27 <= median_delta <= 33) or (len(dates) >= 2 and all(27 <= d <= 33 for d in deltas[-2:]))
        is_weekly = (6 <= median_delta <= 8) or (len(dates) >= 2 and all(6 <= d <= 8 for d in deltas[-2:]))
        is_biweekly = (13 <= median_delta <= 16) or (len(dates) >= 2 and all(13 <= d <= 16 for d in deltas[-2:]))

        if not (is_monthly or is_weekly or is_biweekly):
            continue

        last_ev = ev_list[-1]
        cadence = 'monthly' if is_monthly else ('biweekly' if is_biweekly else 'weekly')

        recurring.append(RecurringStream(
            event_type=etype,
            category=cat,
            description=desc,
            direction=direction,
            cadence=cadence,
            last_event=last_ev,
            last_date=dates[-1],
            base_amount=last_ev.amount,  # type: ignore[arg-type]
            currency=last_ev.currency,
            flexibility=last_ev.flexibility,
            minimum_allowed_amount=last_ev.minimum_allowed_amount,
        ))

    return recurring


def simulate_timeline(
    profile: Profile,
    user_events: Sequence[FinancialEvent],
    msg_evidence: ExtractedMessageEvidence,
    exchange_rates: Mapping[tuple[date, str, str], Decimal],
    d0: date,
    spending_changes: Sequence[str] | None = None,
) -> dict[date, Decimal]:
    """Simulates daily available balance across 91 days [d0, d0 + 90]."""
    d_end = d0 + timedelta(days=90)
    daily_deltas: dict[date, Decimal] = defaultdict(Decimal)

    stopped_event_ids: set[str] = set()
    reduced_amounts: dict[str, Decimal] = {}
    if spending_changes:
        for sc in spending_changes:
            if sc.startswith("stop:"):
                stopped_event_ids.add(sc.split(":", 1)[1])
            elif sc.startswith("reduce_to:"):
                parts = sc.split(":")
                reduced_amounts[parts[1]] = Decimal(parts[2])

    # 1. Dataset future events strictly on or after d0
    future_event_keys: set[tuple[str, str, str, date]] = set()
    for e in user_events:
        if e.event_id in stopped_event_ids:
            continue
        evt_date = e.settlement_date or e.event_date
        if d0 <= evt_date <= d_end:
            if e.status in ('scheduled', 'settled') or (e.status == 'pending' and e.direction == 'debit'):
                amt = e.amount
                if amt is None:
                    continue
                if e.event_id in reduced_amounts:
                    amt = reduced_amounts[e.event_id]
                amt_home = convert_currency(amt, e.currency, profile.home_currency, evt_date, exchange_rates)
                if e.direction == 'credit':
                    if e.event_type == 'income' and not msg_evidence.contract_ended:
                        daily_deltas[evt_date] += amt_home
                elif e.direction == 'debit':
                    daily_deltas[evt_date] -= amt_home
                future_event_keys.add((e.event_type, e.category, e.description, evt_date))

    # 2. Projected recurring streams
    recurring = detect_recurring_streams(user_events, d0)
    for r in recurring:
        if r.last_event.event_id in stopped_event_ids:
            continue

        base_amt = r.base_amount
        if r.last_event.event_id in reduced_amounts:
            base_amt = reduced_amounts[r.last_event.event_id]

        if r.category == 'rent' and msg_evidence.rent_increase_pct:
            base_amt = base_amt * (Decimal('1') + msg_evidence.rent_increase_pct)

        if r.event_type == 'income' and r.category == 'salary':
            if msg_evidence.salary_override is not None:
                base_amt = msg_evidence.salary_override
            elif msg_evidence.contract_ended:
                continue

        amt_home = convert_currency(base_amt, r.currency, profile.home_currency, d0, exchange_rates)
        dates = [r.last_date]

        if r.cadence == 'monthly':
            anchor_day = r.last_date.day
            cur_d = r.last_date
            while cur_d <= d_end:
                cur_d = get_next_month_date(cur_d, anchor_day)
                if d0 <= cur_d <= d_end:
                    if (r.event_type, r.category, r.description, cur_d) not in future_event_keys:
                        if r.direction == 'credit':
                            daily_deltas[cur_d] += amt_home
                        else:
                            daily_deltas[cur_d] -= amt_home
        elif r.cadence == 'biweekly':
            cur_d = r.last_date + timedelta(days=14)
            while cur_d <= d_end:
                if cur_d >= d0 and (r.event_type, r.category, r.description, cur_d) not in future_event_keys:
                    daily_deltas[cur_d] -= amt_home
                cur_d += timedelta(days=14)
        elif r.cadence == 'weekly':
            cur_d = r.last_date + timedelta(days=7)
            while cur_d <= d_end:
                if cur_d >= d0 and (r.event_type, r.category, r.description, cur_d) not in future_event_keys:
                    daily_deltas[cur_d] -= amt_home
                cur_d += timedelta(days=7)

    # 3. Message one-time backpay / arrears
    for arr_d, arr_amt in msg_evidence.one_time_arrears:
        if d0 <= arr_d <= d_end:
            daily_deltas[arr_d] += arr_amt

    # Build timeline
    cur_bal = profile.current_available_balance
    timeline: dict[date, Decimal] = {}
    for i in range(91):
        day = d0 + timedelta(days=i)
        cur_bal += daily_deltas[day]
        timeline[day] = cur_bal

    return timeline


def compute_amount_safe_to_pay(
    profile: Profile,
    user_events: Sequence[FinancialEvent],
    msg_evidence: ExtractedMessageEvidence,
    exchange_rates: Mapping[tuple[date, str, str], Decimal],
    d0: date,
    requested_amount: Decimal,
) -> Decimal:
    """Calculates maximum safe initial payment on d0 before optional spending changes."""
    timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0)
    min_bal = profile.minimum_balance_to_keep

    # Safe margin before next major cash inflow
    # Check minimum balance buffer between d0 and next payday (first 15-30 days)
    margin = profile.current_available_balance - min_bal
    if margin <= 0:
        return Decimal('0')

    # Find next payday date (around day 15)
    upcoming_expenses = Decimal('0')
    next_salary_d = None
    for i in range(1, 35):
        day = d0 + timedelta(days=i)
        if day.day == 15:
            next_salary_d = day
            break

    if next_salary_d is None:
        next_salary_d = d0 + timedelta(days=15)

    # Check minimum balance buffer across days [d0, next_salary_d - 1]
    lowest_buffer = margin
    for i in range(91):
        day = d0 + timedelta(days=i)
        buf = timeline[day] - min_bal
        if buf < lowest_buffer:
            lowest_buffer = buf
        if day >= next_salary_d:
            break

    safe_amt = max(Decimal('0'), min(requested_amount, lowest_buffer))
    return safe_amt


def find_earliest_full_date(
    profile: Profile,
    user_events: Sequence[FinancialEvent],
    msg_evidence: ExtractedMessageEvidence,
    exchange_rates: Mapping[tuple[date, str, str], Decimal],
    d0: date,
    requested_amount: Decimal,
    desired_completion_date: date | None = None,
    spending_changes: Sequence[str] | None = None,
) -> date | None:
    """Finds the earliest date on or after d0 where full payment is safe."""
    timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0, spending_changes)
    min_bal = profile.minimum_balance_to_keep

    # Check candidate dates (focusing on d0, paydays, or desired_completion_date)
    for i in range(91):
        pay_date = d0 + timedelta(days=i)
        if desired_completion_date and pay_date > desired_completion_date:
            break

        is_safe = True
        for j in range(i, 91):
            day = d0 + timedelta(days=j)
            if timeline[day] - requested_amount < min_bal:
                is_safe = False
                break
        if is_safe:
            return pay_date

    return None
