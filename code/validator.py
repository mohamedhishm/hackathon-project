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

    # 4. Spending changes constraints
    if plan.spending_changes_needed != 'none':
        changes = plan.spending_changes_needed.split("|")
        if len(changes) > 3:
            errors.append(f"At most 3 spending changes allowed, got {len(changes)}")

        protected = set(profile.expense_categories_to_protect)
        stop_allowed = set(profile.expense_categories_user_is_willing_to_stop)
        red_allowed = set(profile.expense_categories_user_is_willing_to_reduce)
        events_by_id = {e.event_id: e for e in user_events}

        for c in changes:
            if c.startswith("stop:"):
                eid = c.split(":")[1]
                ev = events_by_id.get(eid)
                if ev:
                    if ev.category in protected:
                        errors.append(f"Cannot stop protected category: {ev.category}")
                    if ev.category not in stop_allowed:
                        errors.append(f"Category {ev.category} not in willing_to_stop")
            elif c.startswith("reduce_to:"):
                parts = c.split(":")
                eid = parts[1]
                new_amt = Decimal(parts[2])
                ev = events_by_id.get(eid)
                if ev:
                    if ev.category in protected:
                        errors.append(f"Cannot reduce protected category: {ev.category}")
                    if ev.category not in red_allowed:
                        errors.append(f"Category {ev.category} not in willing_to_reduce")
                    if ev.minimum_allowed_amount is not None and new_amt < ev.minimum_allowed_amount:
                        errors.append(f"Reduction {new_amt} below minimum_allowed_amount {ev.minimum_allowed_amount}")

    # 5. Installment constraint
    if plan.recommended_payment_method == 'installments':
        if profile.max_installment_months is None:
            errors.append("User does not accept installments (max_installment_months is None)")
        opt_ids = {opt.payment_option_id for opt in payment_options}
        if plan.option_id and plan.option_id not in opt_ids:
            errors.append(f"Option {plan.option_id} not in supplied payment options")

    # 6. Safety check throughout 90 days
    if plan.payment_plan != 'none':
        spending_list = plan.spending_changes_needed.split("|") if plan.spending_changes_needed != 'none' else None
        timeline = simulate_timeline(profile, user_events, msg_evidence, exchange_rates, d0, spending_list)
        
        # Parse payments
        pmts: dict[date, Decimal] = {}
        for item in plan.payment_plan.split("|"):
            if ":" in item:
                dt_str, amt_str = item.split(":")
                pmts[date.fromisoformat(dt_str)] = Decimal(amt_str)

        cum_ded = Decimal('0')
        for i in range(91):
            day = d0 + timedelta(days=i)
            if day in pmts:
                cum_ded += pmts[day]
            if timeline[day] - cum_ded < min_bal:
                errors.append(f"Balance breaches minimum on {day}: {timeline[day] - cum_ded} < {min_bal}")
                break

    return ValidationResult(is_valid=(len(errors) == 0), errors=tuple(errors))
