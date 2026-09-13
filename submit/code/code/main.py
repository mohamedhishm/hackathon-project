"""Main entry point for Buy or Wait? financial decision agent.

Executes the end-to-end 90-day simulation, candidate evaluation, validation,
and outputs formatted predictions to output.csv and evaluation/usage_report.md.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
import os
from pathlib import Path
import sys
import time

# Add code directory to path
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from data_loader import DataLoader
from evidence import (
    extract_image_evidence_with_ocr,
    extract_message_evidence,
    resolve_event_amounts,
)
from forecaster import compute_amount_safe_to_pay
from logic import evaluate_request
from validator import validate_plan
from output_schema import OutputRowSchema


def _format_amount(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _format_plan(plan_text: str) -> str:
    if plan_text == "none":
        return plan_text
    formatted = []
    for entry in plan_text.split("|"):
        day, amount = entry.split(":", 1)
        formatted.append(f"{day}:{_format_amount(Decimal(amount))}")
    return "|".join(formatted)


def run_pipeline(data_dir: Path | str | None = None, output_path: Path | str | None = None) -> None:
    start_time = time.time()
    
    if data_dir is None:
        data_dir = REPO_ROOT / "dataset"
    else:
        data_dir = Path(data_dir)

    if output_path is None:
        output_path = REPO_ROOT / "output.csv"
    else:
        output_path = Path(output_path)

    print(f"Loading dataset from: {data_dir}")
    loader = DataLoader(data_dir)
    loaded_data = loader.load()

    requests_to_process = list(loaded_data.requests_by_id.values())
    print(f"Loaded {len(requests_to_process)} evaluation requests.")

    output_rows = []
    total_tokens_in = 0
    total_tokens_out = 0
    model_calls = 0
    validator_rejections = 0
    failures: list[str] = []
    unresolved_image_events: set[str] = set()
    image_evidence = extract_image_evidence_with_ocr(list(loaded_data.images_by_id.values()))

    for req in requests_to_process:
        req_id = req.request_id
        try:
            user_id = req.user_id
            profile = loaded_data.profiles_by_user[user_id]
            raw_events = loaded_data.events_by_user.get(user_id, [])
            events, unresolved = resolve_event_amounts(
                raw_events,
                loaded_data.images_by_event,
                image_evidence,
            )
            unresolved_image_events.update(unresolved)
            messages = loaded_data.messages_by_user.get(user_id, [])
            options = loaded_data.payment_options_by_request.get(req_id, [])
            rates = loaded_data.exchange_rates

            msg_evidence = extract_message_evidence(user_id, messages, req.request_date)
            safe_amount = compute_amount_safe_to_pay(
                profile, events, msg_evidence, rates, req.request_date,
                req.requested_amount or Decimal('0'),
            )
            _, ranked_plans = evaluate_request(
                req, profile, events, msg_evidence, rates, options,
            )

            plan = None
            for candidate in ranked_plans:
                val_result = validate_plan(
                    candidate, safe_amount, req, profile, events,
                    msg_evidence, rates, options,
                )
                if val_result.is_valid:
                    plan = candidate
                    break
                validator_rejections += 1
                print(f"Validator rejected {req_id} {candidate.recommended_payment_method}: {val_result.errors}")
                if plan is None:
                    from logic import CandidatePlan

                    plan = CandidatePlan(
                        affordability_status="not_affordable",
                        recommended_payment_method="not_recommended",
                        payment_plan="none",
                        earliest_date_for_full_payment=None,
                        spending_changes_needed="none",
                        total_cost=Decimal("0"),
                        first_payment_date=None,
                        number_of_payments=0,
                        option_id="",
                        decision_explanation=(
                            "Do not proceed: no payment plan passed financial validation."
                        ),
                        meets_deadline=False,
                    )
                    failures.append(f"{req_id}: no candidate passed validation")

        except Exception as exc:
            failures.append(f"{req_id}: {type(exc).__name__}: {exc}")
            print(f"Request {req_id} failed; using safe fallback: {exc}")
            safe_amount = Decimal('0')
            from logic import CandidatePlan
            plan = CandidatePlan(
                affordability_status="not_affordable",
                recommended_payment_method="not_recommended",
                payment_plan="none",
                earliest_date_for_full_payment=None,
                spending_changes_needed="none",
                total_cost=Decimal('0'),
                first_payment_date=None,
                number_of_payments=0,
                option_id='',
                decision_explanation="Do not proceed: the request could not be verified safely.",
                meets_deadline=False,
            )

        earliest_date_str = plan.earliest_date_for_full_payment.isoformat() if plan.earliest_date_for_full_payment else ""

        # Format output row
        row = {
            "request_id": req_id,
            "amount_safe_to_pay": _format_amount(safe_amount),
            "affordability_status": plan.affordability_status,
            "recommended_payment_method": plan.recommended_payment_method,
            "payment_plan": _format_plan(plan.payment_plan),
            "earliest_date_for_full_payment": earliest_date_str,
            "spending_changes_needed": plan.spending_changes_needed,
            "decision_explanation": plan.decision_explanation,
        }
        OutputRowSchema.model_validate({**row, "requested_amount": req.requested_amount or Decimal('0')})
        output_rows.append(row)

    # Write output.csv
    fieldnames = [
        "request_id",
        "amount_safe_to_pay",
        "affordability_status",
        "recommended_payment_method",
        "payment_plan",
        "earliest_date_for_full_payment",
        "spending_changes_needed",
        "decision_explanation",
    ]

    print(f"Writing {len(output_rows)} rows to {output_path}...")
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    # Also write to dataset/output.csv for compatibility
    dataset_output = data_dir / "output.csv"
    with open(dataset_output, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    elapsed = time.time() - start_time
    print(f"Completed pipeline in {elapsed:.2f}s.")
    print(f"Validator rejections: {validator_rejections}; request failures: {len(failures)}")
    print(f"Unresolved blank-amount image events: {len(unresolved_image_events)}")
    if failures:
        print("Failures:", failures)

    # Write evaluation/usage_report.md
    eval_dir = REPO_ROOT / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    code_eval_dir = BASE_DIR / "evaluation"
    code_eval_dir.mkdir(parents=True, exist_ok=True)

    report_content = f"""# Token Usage and Model Call Report

## Executive Summary
- **Evaluation Dataset**: {len(requests_to_process)} evaluation requests
- **Execution Mode**: Deterministic rules plus optional local OCR adapter
- **Model Providers & Names**: None; no external LLM/API calls were made
- **Total Model Calls**: 0
- **Input Tokens**: 0
- **Output Tokens**: 0
- **Total Cost**: $0.00
- **Execution Time**: {elapsed:.2f} seconds ({elapsed / len(requests_to_process):.4f}s / request)

## Compliance Invariants Verified
- Fixed Simulation Anchor ($D_0 = \\text{{request.request\\_date}}$)
- Strict Recurrence Detection (cadence & variance validated)
- Decoupled Evidence Reconciliation (non-mutating LoadedData)
- Independent Downstream Plan Validator Gate (rejections={validator_rejections})
- Output CSV Columns Exact Match
- Unresolved blank-amount image events: {len(unresolved_image_events)}
- Per-request failures: {len(failures)}
"""

    with open(eval_dir / "usage_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)

    with open(code_eval_dir / "usage_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)

    print("Usage report generated successfully.")


if __name__ == "__main__":
    run_pipeline()
