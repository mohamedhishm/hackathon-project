"""Produce an evidence-first diagnostic for all labeled sample requests.

This tool intentionally does not change financial logic or labels. It exposes the
inputs, projected timeline, candidates, and validator decisions used by the
current implementation so model/spec mismatches can be diagnosed.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from data_loader import DataLoader  # noqa: E402
from evidence import extract_message_evidence  # noqa: E402
from forecaster import (  # noqa: E402
    compute_amount_safe_to_pay,
    detect_recurring_streams,
    find_earliest_full_date,
    simulate_timeline,
)
from logic import evaluate_request  # noqa: E402
from validator import validate_plan  # noqa: E402


def _decimal(value):
    return str(value) if isinstance(value, Decimal) else value


def _event(event):
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "description": event.description,
        "category": event.category,
        "direction": event.direction,
        "amount": _decimal(event.amount),
        "currency": event.currency,
        "event_date": event.event_date.isoformat(),
        "settlement_date": event.settlement_date.isoformat() if event.settlement_date else None,
        "status": event.status,
        "flexibility": event.flexibility,
        "minimum_allowed_amount": _decimal(event.minimum_allowed_amount),
    }


def diagnose(data_dir: Path) -> list[dict]:
    data = DataLoader(data_dir).load()
    result = []
    for sample in data.sample_requests_by_id.values():
        profile = data.profiles_by_user[sample.user_id]
        events = data.events_by_user.get(sample.user_id, [])
        messages = data.messages_by_user.get(sample.user_id, [])
        options = data.payment_options_by_request.get(sample.request_id, [])
        evidence = extract_message_evidence(sample.user_id, messages, sample.request_date)
        timeline = simulate_timeline(
            profile, events, evidence, data.exchange_rates, sample.request_date,
        )
        minimum_date = min(timeline, key=timeline.get)
        safe_amount = compute_amount_safe_to_pay(
            profile, events, evidence, data.exchange_rates,
            sample.request_date, sample.requested_amount or Decimal("0"),
        )
        earliest = find_earliest_full_date(
            profile, events, evidence, data.exchange_rates,
            sample.request_date, sample.requested_amount or Decimal("0"),
            sample.desired_completion_date,
        )
        best, ranked = evaluate_request(
            sample, profile, events, evidence, data.exchange_rates, options,
        )
        candidate_rows = []
        for candidate in ranked:
            validation = validate_plan(
                candidate, safe_amount, sample, profile, events,
                evidence, data.exchange_rates, options,
            )
            candidate_rows.append({
                "method": candidate.recommended_payment_method,
                "status": candidate.affordability_status,
                "payment_plan": candidate.payment_plan,
                "earliest_date": candidate.earliest_date_for_full_payment.isoformat()
                if candidate.earliest_date_for_full_payment else None,
                "spending_changes": candidate.spending_changes_needed,
                "total_cost": _decimal(candidate.total_cost),
                "option_id": candidate.option_id,
                "meets_deadline": candidate.meets_deadline,
                "valid": validation.is_valid,
                "validation_errors": list(validation.errors),
            })
        horizon_end = sample.request_date + timedelta(days=90)
        relevant_events = [
            _event(event)
            for event in events
            if sample.request_date <= (event.settlement_date or event.event_date) <= horizon_end
        ]
        timeline_window = []
        for offset in range(-3, 4):
            day = minimum_date + timedelta(days=offset)
            if day not in timeline:
                continue
            day_events = [
                _event(event)
                for event in events
                if (event.settlement_date or event.event_date) == day
            ]
            timeline_window.append({
                "date": day.isoformat(),
                "balance": _decimal(timeline[day]),
                "buffer": _decimal(timeline[day] - profile.minimum_balance_to_keep),
                "dataset_events": day_events,
            })
        streams = [
            {
                "event_id": stream.last_event.event_id,
                "event_type": stream.event_type,
                "category": stream.category,
                "description": stream.description,
                "direction": stream.direction,
                "cadence": stream.cadence,
                "interval_days": stream.interval_days,
                "last_date": stream.last_date.isoformat(),
                "base_amount": _decimal(stream.base_amount),
                "terminal_date": stream.terminal_date.isoformat() if stream.terminal_date else None,
            }
            for stream in detect_recurring_streams(events, sample.request_date)
        ]
        income_dates = []
        for stream in detect_recurring_streams(events, sample.request_date):
            if stream.direction != "credit":
                continue
            next_date = stream.last_date
            while next_date <= sample.request_date:
                next_date += timedelta(days=stream.interval_days)
            income_dates.append(next_date)
        next_income = min(income_dates) if income_dates else None
        buffers_before_income = [
            timeline[day] - profile.minimum_balance_to_keep
            for day in timeline
            if next_income is None or day < next_income
        ]
        deadline = sample.desired_completion_date
        buffers_to_deadline = [
            timeline[day] - profile.minimum_balance_to_keep
            for day in timeline
            if deadline is None or day <= deadline
        ]
        result.append({
            "request_id": sample.request_id,
            "user_id": sample.user_id,
            "request": {
                "request_date": sample.request_date.isoformat(),
                "request_type": sample.request_type,
                "requested_amount": _decimal(sample.requested_amount),
                "desired_completion_date": sample.desired_completion_date.isoformat()
                if sample.desired_completion_date else None,
                "allows_partial_payment": sample.allows_partial_payment,
            },
            "profile": {
                "home_currency": profile.home_currency,
                "current_balance": _decimal(profile.current_available_balance),
                "minimum_balance": _decimal(profile.minimum_balance_to_keep),
                "accepted_methods": profile.payment_methods_user_will_consider,
                "max_installment_months": profile.max_installment_months,
                "protected": profile.expense_categories_to_protect,
                "reducible": profile.expense_categories_user_is_willing_to_reduce,
                "stoppable": profile.expense_categories_user_is_willing_to_stop,
            },
            "expected": {
                "amount_safe_to_pay": _decimal(sample.amount_safe_to_pay),
                "affordability_status": sample.affordability_status,
                "method": sample.recommended_payment_method,
                "payment_plan": sample.payment_plan,
                "earliest_date": sample.earliest_date_for_full_payment.isoformat()
                if sample.earliest_date_for_full_payment else None,
                "spending_changes": sample.spending_changes_needed,
            },
            "evidence": {
                "salary_override": _decimal(evidence.salary_override),
                "salary_effective_date": evidence.salary_effective_date.isoformat()
                if evidence.salary_effective_date else None,
                "contract_ended": evidence.contract_ended,
                "pending_income": evidence.pending_income,
                "rent_increase_pct": _decimal(evidence.rent_increase_pct),
            },
            "relevant_events": relevant_events,
            "recurring_streams": streams,
            "timeline": {
                "minimum_date": minimum_date.isoformat(),
                "minimum_balance": _decimal(timeline[minimum_date]),
                "minimum_buffer": _decimal(timeline[minimum_date] - profile.minimum_balance_to_keep),
                "window": timeline_window,
            },
            "interpretations": {
                "A_current_margin": _decimal(
                    profile.current_available_balance - profile.minimum_balance_to_keep
                ),
                "B_before_next_detected_income": _decimal(min(buffers_before_income)),
                "C_full_91_day_buffer": _decimal(
                    min(timeline.values()) - profile.minimum_balance_to_keep
                ),
                "D_current_engine_safe_amount": _decimal(safe_amount),
                "E_buffer_to_deadline": _decimal(min(buffers_to_deadline)),
                "next_detected_income": next_income.isoformat() if next_income else None,
            },
            "actual_current": {
                "amount_safe_to_pay": _decimal(safe_amount),
                "earliest_date": earliest.isoformat() if earliest else None,
                "selected_method": best.recommended_payment_method,
                "selected_status": best.affordability_status,
            },
            "payment_options": [
                {
                    "id": option.payment_option_id,
                    "method": option.payment_method,
                    "amount": _decimal(option.payment_amount),
                    "count": option.number_of_payments,
                    "first_date": option.first_payment_date.isoformat()
                    if option.first_payment_date else None,
                    "frequency_days": option.payment_frequency_days,
                    "fee": _decimal(option.financing_fee),
                    "total": _decimal(option.total_payable_amount),
                }
                for option in options
            ],
            "candidates": candidate_rows,
        })
    return result


def write_markdown(output: list[dict], path: Path) -> None:
    lines = [
        "# Sample Semantics Diagnosis v2",
        "",
        "Diagnostic only. No financial engine or sample labels are changed here.",
        "",
        "## Safe-Amount Interpretations",
        "",
        "A=current balance margin; B=minimum buffer before next detected income; "
        "C=minimum 91-day buffer; D=current engine result; E=minimum buffer through deadline.",
        "",
        "| Request | Expected | A | B | C | D | E | Next income | Classification |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|---|")
    for item in output:
        exp = item["expected"]["amount_safe_to_pay"]
        interp = item["interpretations"]
        classification = "MATCH" if str(exp) == str(interp["D_current_engine_safe_amount"]) else "UNRESOLVED"
        lines.append(
            f"| {item['request_id']} | {exp} | {interp['A_current_margin']} | "
            f"{interp['B_before_next_detected_income']} | {interp['C_full_91_day_buffer']} | "
            f"{interp['D_current_engine_safe_amount']} | {interp['E_buffer_to_deadline']} | "
            f"{interp['next_detected_income'] or ''} | {classification} |"
        )
    lines.extend(["", "## Recurrence Evidence", "", "| Request | Stream | Evidence | Current interpretation | Label interpretation | Confidence |", "|---|---|---|---|---|---|"])
    for item in output:
        for stream in item["recurring_streams"]:
            evidence = f"{stream['event_id']}; {stream['cadence']}/{stream['interval_days']}d; last={stream['last_date']}; amount={stream['base_amount']}"
            if stream["category"] in {"groceries", "transport", "dining", "shopping", "entertainment"}:
                current = "category-level variable stream"
                label = "not inferable from label alone"
                confidence = "LOW"
            else:
                current = "description/category stream"
                label = "not inferable from label alone"
                confidence = "MEDIUM"
            lines.append(f"| {item['request_id']} | {stream['category']} ({stream['direction']}) | {evidence} | {current} | {label} | {confidence} |")
    lines.extend(["", "## Spending Changes and Candidates", ""])
    for item in output:
        expected = item["expected"]["spending_changes"]
        candidates = item["candidates"]
        lines.append(f"### {item['request_id']}")
        lines.append(f"Expected spending changes: `{expected}`; candidates generated: `{len(candidates)}`.")
        for candidate in candidates[:25]:
            lines.append(
                f"- `{candidate['method']}` `{candidate['payment_plan']}` "
                f"changes=`{candidate['spending_changes']}` deadline={candidate['meets_deadline']} "
                f"valid={candidate['valid']} option=`{candidate['option_id']}` errors={candidate['validation_errors']}"
            )
        if len(candidates) > 25:
            lines.append(f"- ... {len(candidates) - 25} additional candidates in sample_diagnostics.json")
    lines.extend(["", "## Classification", "", "- Confirmed bugs are documented separately from unresolved recurrence/evidence semantics.", "- A positive expected label while C is negative is evidence that current event reconstruction differs from the label construction; it is not a justification for changing the formula alone.", "- No sample-specific rules are inferred or applied."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    output = diagnose(ROOT / "dataset")
    path = ROOT / "evaluation" / "sample_diagnostics.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    write_markdown(output, ROOT / "evaluation" / "mismatch_diagnosis_v2.md")
    print(f"wrote {path} ({len(output)} samples)")
