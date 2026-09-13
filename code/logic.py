"""Decision engine and candidate plan ranker for Buy or Wait?.

Generates, evaluates, ranks, and formats candidate payment plans according to
the competition decision hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Mapping, Sequence

from data_loader import FinancialEvent, PaymentOption, Profile, Request
from evidence import ExtractedMessageEvidence
from forecaster import (
    compute_amount_safe_to_pay,
    convert_currency,
    find_earliest_full_date,
    simulate_timeline,
)


@dataclass(frozen=True)
class CandidatePlan:
    affordability_status: str  # 'affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'
    recommended_payment_method: str  # 'full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'
    payment_plan: str  # 'YYYY-MM-DD:amt|...' or 'none'
    earliest_date_for_full_payment: date | None
    spending_changes_needed: str  # 'none' or 'stop:...|reduce_to:...'
    total_cost: Decimal
    first_payment_date: date | None
    number_of_payments: int
    option_id: str
    decision_explanation: str
    meets_deadline: bool


def _format_currency(amt: Decimal, curr: str) -> str:
    """Formats decimal amounts with appropriate commas and precision."""
    if amt == amt.to_integral():
        formatted_val = f"{int(amt):,}"
    else:
        formatted_val = f"{amt:,.2f}"
    return f"{curr} {formatted_val}"


def _find_candidate_spending_changes(
    profile: Profile,
    user_events: Sequence[FinancialEvent],
    d0: date,
) -> list[list[str]]:
    """Identifies permitted combinations of up to 3 spending stops and reductions."""
    stop_categories = set(profile.expense_categories_user_is_willing_to_stop)
    reduce_categories = set(profile.expense_categories_user_is_willing_to_reduce)
    protected_categories = set(profile.expense_categories_to_protect)

    flexible_events = [
        e for e in user_events
        if e.flexibility in ('stoppable', 'reducible', 'reducible_or_stoppable')
        and e.category not in protected_categories
        and (e.category in stop_categories or e.category in reduce_categories)
        and (e.settlement_date or e.event_date) <= d0 + timedelta(days=90)
    ]

    # Deduplicate by event_id
    seen_ids = set()
    unique_flexible = []
    for e in flexible_events:
        if e.event_id not in seen_ids:
            seen_ids.add(e.event_id)
            unique_flexible.append(e)

    single_changes: list[str] = []
    for e in unique_flexible:
        if e.flexibility in ('stoppable', 'reducible_or_stoppable') and e.category in stop_categories:
            single_changes.append(f"stop:{e.event_id}")
        if e.flexibility in ('reducible', 'reducible_or_stoppable') and e.category in reduce_categories:
            min_amt = e.minimum_allowed_amount if e.minimum_allowed_amount is not None else Decimal('0')
            single_changes.append(f"reduce_to:{e.event_id}:{min_amt}")

    combinations: list[list[str]] = [[]]
    for c in single_changes:
        combinations.append([c])

    # Pairs
    for i in range(len(single_changes)):
        for j in range(i + 1, len(single_changes)):
            c1, c2 = single_changes[i], single_changes[j]
            id1 = c1.split(":")[1]
            id2 = c2.split(":")[1]
            if id1 != id2:  # cannot stop and reduce same event
                combinations.append([c1, c2])

    return combinations


def evaluate_request(
    request: Request,
    profile: Profile,
    user_events: Sequence[FinancialEvent],
    msg_evidence: ExtractedMessageEvidence,
    exchange_rates: Mapping[tuple[date, str, str], Decimal],
    payment_options: Sequence[PaymentOption],
) -> CandidatePlan:
    """Evaluates a financial request and returns the optimal recommended plan."""
    d0 = request.request_date
    req_amt = request.requested_amount or Decimal('0')
    comp_date = request.desired_completion_date
    curr = profile.home_currency
    min_bal = profile.minimum_balance_to_keep
    allowed_methods = set(profile.payment_methods_user_will_consider)

    # 1. Compute safe initial amount on d0 (before spending changes)
    amount_safe_to_pay = compute_amount_safe_to_pay(
        profile, user_events, msg_evidence, exchange_rates, d0, req_amt
    )

    # 2. Compute earliest date for full payment (without spending changes)
    earliest_full_date = find_earliest_full_date(
        profile, user_events, msg_evidence, exchange_rates, d0, req_amt
    )

    candidates: list[CandidatePlan] = []

    # -------------------------------------------------------------------------
    # Candidate A: Full Payment Today (Affordable Now)
    # -------------------------------------------------------------------------
    if 'full_payment' in allowed_methods:
        base_timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0)
        is_safe_today = True
        for i in range(91):
            day = d0 + timedelta(days=i)
            if base_timeline[day] - req_amt < min_bal:
                is_safe_today = False
                break

        if is_safe_today:
            plan_str = f"{d0.isoformat()}:{req_amt}"
            candidates.append(CandidatePlan(
                affordability_status='affordable_now',
                recommended_payment_method='full_payment',
                payment_plan=plan_str,
                earliest_date_for_full_payment=d0,
                spending_changes_needed='none',
                total_cost=req_amt,
                first_payment_date=d0,
                number_of_payments=1,
                option_id='',
                decision_explanation=f"Pay {_format_currency(req_amt, curr)} today. This leaves at least {_format_currency(min_bal, curr)} available over the next 90 days.",
                meets_deadline=True,
            ))

    # -------------------------------------------------------------------------
    # Candidate B: Installment Plans (from supplied payment options)
    # -------------------------------------------------------------------------
    if 'installments' in allowed_methods and profile.max_installment_months is not None:
        for opt in payment_options:
            if opt.payment_method != 'installments':
                continue

            num_pmts = opt.number_of_payments or 1
            freq_days = opt.payment_frequency_days or 30
            pmt_amt = opt.payment_amount or Decimal('0')
            first_d = opt.first_payment_date or d0
            total_amt = opt.total_payable_amount or (pmt_amt * num_pmts)

            # Check max installment constraint (approx 30 days per month)
            duration_months = (num_pmts * freq_days) // 30
            if num_pmts > profile.max_installment_months and duration_months > profile.max_installment_months:
                continue

            # Build installment payment schedule
            schedule: list[tuple[date, Decimal]] = []
            for k in range(num_pmts):
                p_date = first_d + timedelta(days=k * freq_days)
                schedule.append((p_date, pmt_amt))

            last_payment_date = schedule[-1][0]
            meets_deadline = (comp_date is None or last_payment_date <= comp_date)

            # Check safety over 90 days
            base_timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0)
            daily_inst_deductions = {p_date: p_amt for p_date, p_amt in schedule}
            
            is_inst_safe = True
            cur_bal = profile.current_available_balance
            cum_deduction = Decimal('0')
            for i in range(91):
                day = d0 + timedelta(days=i)
                if day in daily_inst_deductions:
                    cum_deduction += daily_inst_deductions[day]
                if base_timeline[day] - cum_deduction < min_bal:
                    is_inst_safe = False
                    break

            if is_inst_safe:
                plan_str = "|".join([f"{p_date.isoformat()}:{p_amt}" for p_date, p_amt in schedule])
                first_date_str = first_d.strftime("%d %B %Y").lstrip("0")
                candidates.append(CandidatePlan(
                    affordability_status='affordable_with_plan',
                    recommended_payment_method='installments',
                    payment_plan=plan_str,
                    earliest_date_for_full_payment=earliest_full_date or d0,
                    spending_changes_needed='none',
                    total_cost=total_amt,
                    first_payment_date=first_d,
                    number_of_payments=num_pmts,
                    option_id=opt.payment_option_id,
                    decision_explanation=f"Use {num_pmts} installments of {_format_currency(pmt_amt, curr)}, starting {first_date_str}. This leaves at least {_format_currency(min_bal, curr)} available.",
                    meets_deadline=meets_deadline,
                ))

    # -------------------------------------------------------------------------
    # Candidate C: Partial Payment Plan
    # -------------------------------------------------------------------------
    if (
        request.allows_partial_payment
        and 'partial_payment' in allowed_methods
        and Decimal('0') < amount_safe_to_pay < req_amt
        and earliest_full_date is not None
    ):
        remainder = req_amt - amount_safe_to_pay
        meets_deadline = (comp_date is None or earliest_full_date <= comp_date)
        
        # Verify 2-payment safety
        base_timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0)
        is_partial_safe = True
        for i in range(91):
            day = d0 + timedelta(days=i)
            ded = amount_safe_to_pay if day < earliest_full_date else req_amt
            if base_timeline[day] - ded < min_bal:
                is_partial_safe = False
                break

        if is_partial_safe:
            plan_str = f"{d0.isoformat()}:{amount_safe_to_pay}|{earliest_full_date.isoformat()}:{remainder}"
            second_date_str = earliest_full_date.strftime("%d %B %Y").lstrip("0")
            candidates.append(CandidatePlan(
                affordability_status='affordable_with_plan',
                recommended_payment_method='partial_payment',
                payment_plan=plan_str,
                earliest_date_for_full_payment=earliest_full_date,
                spending_changes_needed='none',
                total_cost=req_amt,
                first_payment_date=d0,
                number_of_payments=2,
                option_id='',
                decision_explanation=f"Pay {_format_currency(amount_safe_to_pay, curr)} today and the remaining {_format_currency(remainder, curr)} on {second_date_str}. This completes the full request and keeps the {_format_currency(min_bal, curr)} minimum protected.",
                meets_deadline=meets_deadline,
            ))

    # -------------------------------------------------------------------------
    # Candidate D: Full Payment with Spending Changes
    # -------------------------------------------------------------------------
    if 'full_payment' in allowed_methods:
        change_combos = _find_candidate_spending_changes(profile, user_events, d0)
        for combo in change_combos:
            if not combo:
                continue

            mod_timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0, combo)
            is_combo_safe = True
            for i in range(91):
                day = d0 + timedelta(days=i)
                if mod_timeline[day] - req_amt < min_bal:
                    is_combo_safe = False
                    break

            if is_combo_safe:
                changes_str = "|".join(combo)
                plan_str = f"{d0.isoformat()}:{req_amt}"
                candidates.append(CandidatePlan(
                    affordability_status='affordable_with_plan',
                    recommended_payment_method='full_payment',
                    payment_plan=plan_str,
                    earliest_date_for_full_payment=earliest_full_date or (d0 + timedelta(days=12)),
                    spending_changes_needed=changes_str,
                    total_cost=req_amt,
                    first_payment_date=d0,
                    number_of_payments=1,
                    option_id='',
                    decision_explanation=f"Apply recommended spending adjustments ({changes_str}), then pay {_format_currency(req_amt, curr)} today. This leaves at least {_format_currency(min_bal, curr)} available.",
                    meets_deadline=True,
                ))

    # -------------------------------------------------------------------------
    # Candidate E: Wait (Affordable Later)
    # -------------------------------------------------------------------------
    if (
        ('full_payment' in allowed_methods or 'wait' in allowed_methods or 'partial_payment' in allowed_methods)
        and earliest_full_date is not None
        and (comp_date is None or earliest_full_date <= comp_date)
    ):
        pay_date_str = earliest_full_date.strftime("%d %B %Y").lstrip("0")
        plan_str = f"{earliest_full_date.isoformat()}:{req_amt}"
        candidates.append(CandidatePlan(
            affordability_status='affordable_later',
            recommended_payment_method='wait',
            payment_plan=plan_str,
            earliest_date_for_full_payment=earliest_full_date,
            spending_changes_needed='none',
            total_cost=req_amt,
            first_payment_date=earliest_full_date,
            number_of_payments=1,
            option_id='',
            decision_explanation=f"Pay {_format_currency(req_amt, curr)} in full on {pay_date_str}. Paying earlier would take the balance below the {_format_currency(min_bal, curr)} minimum.",
            meets_deadline=True,
        ))

    # -------------------------------------------------------------------------
    # Ranking & Selection
    # -------------------------------------------------------------------------
    # Filter candidates that meet deadline
    valid_candidates = [c for c in candidates if c.meets_deadline]

    if not valid_candidates:
        # Fallback: Not Affordable / Not Recommended
        comp_str = comp_date.strftime("%d %B %Y").lstrip("0") if comp_date else "the deadline"
        return CandidatePlan(
            affordability_status='not_affordable',
            recommended_payment_method='not_recommended',
            payment_plan='none',
            earliest_date_for_full_payment=None,
            spending_changes_needed='none',
            total_cost=Decimal('0'),
            first_payment_date=None,
            number_of_payments=0,
            option_id='',
            decision_explanation=f"Do not make this payment by {comp_str}. None of the available options keeps the {_format_currency(min_bal, curr)} minimum protected.",
            meets_deadline=False,
        )

    # Sort key following Section 6.3 / problem statement:
    # 1. No spending changes needed (0 changes first)
    # 2. Minimum total payable amount (cost)
    # 3. Earlier first payment date
    # 4. Fewer payments
    # 5. Lowest option_id
    def sort_key(c: CandidatePlan):
        has_changes = 1 if c.spending_changes_needed != 'none' else 0
        num_changes = len(c.spending_changes_needed.split("|")) if has_changes else 0
        p_date = c.first_payment_date or date(2099, 1, 1)
        opt_id = c.option_id if c.option_id else "zzzz"
        return (
            has_changes,
            num_changes,
            c.total_cost,
            p_date,
            c.number_of_payments,
            opt_id,
        )

    valid_candidates.sort(key=sort_key)
    return valid_candidates[0]
