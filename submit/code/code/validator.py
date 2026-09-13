"""Independent downstream validator for Buy or Wait? decisions.

Hard safety gate enforcing financial invariants, user policy constraints,
and competition rules before final output generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Mapping, Sequence

from data_loader import FinancialEvent, PaymentOption, Profile, Request
from evidence import ExtractedMessageEvidence
from forecaster import simulate_timeline
from logic import CandidatePlan


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[str, ...] = ()


def validate_plan(
    plan: CandidatePlan,
    amount_safe_to_pay: Decimal,
    request: Request,
    profile: Profile,
    user_events: Sequence[FinancialEvent],
    msg_evidence: ExtractedMessageEvidence,
    exchange_rates: Mapping[tuple[date, str, str], Decimal],
    payment_options: Sequence[PaymentOption],
) -> ValidationResult:
    """Performs comprehensive invariant and policy validation on a proposed plan."""
    errors: list[str] = []
    d0 = request.request_date
    req_amt = request.requested_amount or Decimal('0')
    min_bal = profile.minimum_balance_to_keep
    allowed_methods = set(profile.payment_methods_user_will_consider)

    allowed_statuses = {
        'affordable_now', 'affordable_with_plan', 'affordable_later',
        'not_affordable',
    }
    allowed_plan_methods = {
        'full_payment', 'partial_payment', 'installments', 'wait',
        'not_recommended',
    }
    if plan.affordability_status not in allowed_statuses:
        errors.append(f"Unknown affordability status: {plan.affordability_status}")
    if plan.recommended_payment_method not in allowed_plan_methods:
        errors.append(f"Unknown payment method: {plan.recommended_payment_method}")

    # 1. Safe amount bounds: 0 <= amount_safe_to_pay <= requested_amount
    if not (Decimal('0') <= amount_safe_to_pay <= req_amt):
        errors.append(f"Safe amount {amount_safe_to_pay} out of bounds [0, {req_amt}]")

    # 2. Method considered by user
    if plan.recommended_payment_method not in ('not_recommended', 'wait'):
        if plan.recommended_payment_method not in allowed_methods:
            errors.append(f"Method {plan.recommended_payment_method} not in user allowed methods {allowed_methods}")

    # 3. Status and method coherence
    if plan.affordability_status == 'affordable_now':
        if plan.recommended_payment_method != 'full_payment':
            errors.append(f"affordable_now must use full_payment, got {plan.recommended_payment_method}")
        if plan.earliest_date_for_full_payment != d0:
            errors.append(f"affordable_now must have earliest_date = request_date {d0}, got {plan.earliest_date_for_full_payment}")

    if plan.affordability_status == 'not_affordable':
        if plan.recommended_payment_method != 'not_recommended':
            errors.append(f"not_affordable must use not_recommended, got {plan.recommended_payment_method}")
        if plan.payment_plan != 'none':
            errors.append(f"not_affordable must have payment_plan = 'none', got {plan.payment_plan}")

    if plan.affordability_status == 'affordable_with_plan' and plan.recommended_payment_method not in {
        'partial_payment', 'installments', 'full_payment'
    }:
        errors.append("affordable_with_plan requires partial_payment, installments, or full_payment with changes")

    if not plan.decision_explanation.strip():
        errors.append("decision_explanation must not be empty")

    # 4. Spending changes constraints
    if plan.spending_changes_needed != 'none':
        changes = plan.spending_changes_needed.split("|")
        if len(changes) > 3:
            errors.append(f"At most 3 spending changes allowed, got {len(changes)}")

        protected = set(profile.expense_categories_to_protect)
        stop_allowed = set(profile.expense_categories_user_is_willing_to_stop)
        red_allowed = set(profile.expense_categories_user_is_willing_to_reduce)
        events_by_id = {e.event_id: e for e in user_events}

        stopped_ids: set[str] = set()
        reduced_ids: set[str] = set()
        for c in changes:
            if c.startswith("stop:"):
                parts = c.split(":")
                if len(parts) != 2 or not parts[1]:
                    errors.append(f"Malformed stop change: {c}")
                    continue
                eid = parts[1]
                stopped_ids.add(eid)
                ev = events_by_id.get(eid)
                if ev is None:
                    errors.append(f"Unknown spending-change event: {eid}")
                else:
                    if ev.category in protected:
                        errors.append(f"Cannot stop protected category: {ev.category}")
                    if ev.category not in stop_allowed:
                        errors.append(f"Category {ev.category} not in willing_to_stop")
                    if ev.flexibility not in ('stoppable', 'reducible_or_stoppable'):
                        errors.append(f"Event {eid} is not stoppable")
            elif c.startswith("reduce_to:"):
                parts = c.split(":")
                if len(parts) != 3:
                    errors.append(f"Malformed reduction change: {c}")
                    continue
                eid = parts[1]
                try:
                    new_amt = Decimal(parts[2])
                except Exception:
                    errors.append(f"Invalid reduction amount: {c}")
                    continue
                reduced_ids.add(eid)
                ev = events_by_id.get(eid)
                if ev is None:
                    errors.append(f"Unknown spending-change event: {eid}")
                else:
                    if ev.category in protected:
                        errors.append(f"Cannot reduce protected category: {ev.category}")
                    if ev.category not in red_allowed:
                        errors.append(f"Category {ev.category} not in willing_to_reduce")
                    if ev.flexibility not in ('reducible', 'reducible_or_stoppable'):
                        errors.append(f"Event {eid} is not reducible")
                    if ev.amount is not None and new_amt > ev.amount:
                        errors.append(f"Reduction {new_amt} exceeds original amount {ev.amount}")
                    if ev.minimum_allowed_amount is not None and new_amt < ev.minimum_allowed_amount:
                        errors.append(f"Reduction {new_amt} below minimum_allowed_amount {ev.minimum_allowed_amount}")
            else:
                errors.append(f"Malformed spending change: {c}")
        overlap = stopped_ids & reduced_ids
        if overlap:
            errors.append(f"Event cannot be both stopped and reduced: {sorted(overlap)}")

    # 5. Installment constraint
    if plan.recommended_payment_method == 'installments':
        if profile.max_installment_months is None:
            errors.append("User does not accept installments (max_installment_months is None)")
        opt_ids = {opt.payment_option_id for opt in payment_options}
        if plan.option_id and plan.option_id not in opt_ids:
            errors.append(f"Option {plan.option_id} not in supplied payment options")
        option = next((opt for opt in payment_options if opt.payment_option_id == plan.option_id), None)
        if option is not None:
            expected = []
            first = option.first_payment_date
            amount = option.payment_amount
            count = option.number_of_payments
            frequency = option.payment_frequency_days
            if first is None or amount is None or count is None:
                errors.append("Installment option is missing schedule fields")
            else:
                expected = [
                    (first + timedelta(days=index * (frequency or 0)), amount)
                    for index in range(count)
                ]
                actual = _parse_payment_plan(plan.payment_plan, errors)
                if actual != expected:
                    errors.append("Installment payment_plan does not match supplied option")

    if plan.recommended_payment_method == 'partial_payment':
        if not request.allows_partial_payment:
            errors.append("Request does not allow partial payment")
        actual = _parse_payment_plan(plan.payment_plan, errors)
        if len(actual) != 2:
            errors.append("Partial payment requires exactly two payments")
        else:
            first_date, first_amount = actual[0]
            second_date, second_amount = actual[1]
            if first_date != d0:
                errors.append("Partial payment must start on request_date")
            if second_date <= first_date:
                errors.append("Partial payment dates must be chronological")
            if first_amount <= 0 or second_amount <= 0 or first_amount + second_amount != req_amt:
                errors.append("Partial payment amounts must be positive and sum to requested_amount")
            if plan.earliest_date_for_full_payment != second_date:
                errors.append("Partial payment second date must equal earliest full-payment date")

    # 6. Safety check throughout 90 days
    if plan.payment_plan != 'none':
        spending_list = plan.spending_changes_needed.split("|") if plan.spending_changes_needed != 'none' else None
        timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0, spending_list)
        
        # Parse payments
        pmts = dict(_parse_payment_plan(plan.payment_plan, errors))
        if request.desired_completion_date is not None:
            late_dates = [
                payment_date
                for payment_date in pmts
                if payment_date > request.desired_completion_date
            ]
            if late_dates:
                errors.append(
                    f"Payment plan exceeds desired completion date: {sorted(late_dates)}"
                )

        cum_ded = Decimal('0')
        for i in range(91):
            day = d0 + timedelta(days=i)
            if day in pmts:
                cum_ded += pmts[day]
            if timeline[day] - cum_ded < min_bal:
                errors.append(f"Balance breaches minimum on {day}: {timeline[day] - cum_ded} < {min_bal}")
                break

    return ValidationResult(is_valid=(len(errors) == 0), errors=tuple(errors))


def _parse_payment_plan(
    payment_plan: str,
    errors: list[str],
) -> list[tuple[date, Decimal]]:
    if payment_plan == 'none':
        return []
    parsed: list[tuple[date, Decimal]] = []
    for item in payment_plan.split('|'):
        parts = item.split(':')
        if len(parts) != 2:
            errors.append(f"Malformed payment-plan entry: {item}")
            continue
        try:
            amount = Decimal(parts[1])
            if amount <= 0:
                errors.append(f"Payment amount must be positive: {item}")
                continue
            parsed.append((date.fromisoformat(parts[0]), amount))
        except Exception:
            errors.append(f"Invalid payment-plan entry: {item}")
    if any(parsed[index][0] >= parsed[index + 1][0] for index in range(len(parsed) - 1)):
        errors.append("Payment-plan entries must be strictly chronological")
    return parsed
