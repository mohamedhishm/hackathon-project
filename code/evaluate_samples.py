"""Evaluate the deterministic pipeline against labeled sample requests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from data_loader import DataLoader  # noqa: E402
from evidence import extract_message_evidence  # noqa: E402
from forecaster import compute_amount_safe_to_pay  # noqa: E402
from logic import evaluate_request  # noqa: E402
from validator import validate_plan  # noqa: E402

FIELDS = (
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
)


def _equal(field: str, expected, actual) -> bool:
    if field == "amount_safe_to_pay":
        return expected is not None and actual is not None and abs(expected - actual) <= Decimal("0.01")
    return expected == actual


def evaluate(data_dir: Path) -> tuple[str, dict[str, int], list[str]]:
    data = DataLoader(data_dir).load()
    mismatches = {field: 0 for field in FIELDS}
    details: list[str] = []
    for sample in data.sample_requests_by_id.values():
        profile = data.profiles_by_user[sample.user_id]
        events = data.events_by_user.get(sample.user_id, [])
        messages = data.messages_by_user.get(sample.user_id, [])
        options = data.payment_options_by_request.get(sample.request_id, [])
        evidence = extract_message_evidence(sample.user_id, messages, sample.request_date)
        safe = compute_amount_safe_to_pay(
            profile, events, evidence, data.exchange_rates,
            sample.request_date, sample.requested_amount or Decimal("0"),
        )
        _, ranked = evaluate_request(
            sample, profile, events, evidence, data.exchange_rates, options,
        )
        chosen = None
        rejection_notes = []
        for candidate in ranked:
            result = validate_plan(
                candidate, safe, sample, profile, events, evidence,
                data.exchange_rates, options,
            )
            if result.is_valid:
                chosen = candidate
                break
            rejection_notes.extend(result.errors)
        if chosen is None:
            chosen = ranked[-1]
        actual = {
            "amount_safe_to_pay": safe,
            "affordability_status": chosen.affordability_status,
            "recommended_payment_method": chosen.recommended_payment_method,
            "payment_plan": chosen.payment_plan,
            "earliest_date_for_full_payment": chosen.earliest_date_for_full_payment,
            "spending_changes_needed": chosen.spending_changes_needed,
        }
        for field in FIELDS:
            expected = getattr(sample, field)
            if not _equal(field, expected, actual[field]):
                mismatches[field] += 1
                details.append(
                    f"- `{sample.request_id}` `{field}`: expected `{expected}`, "
                    f"predicted `{actual[field]}`"
                )
    total = len(data.sample_requests_by_id)
    lines = [
        "# Sample Evaluation Report",
        "",
        f"Evaluated `{total}` labeled sample requests.",
        "",
        "## Mismatches by Field",
        "",
    ]
    for field in FIELDS:
        lines.append(f"- `{field}`: {mismatches[field]} mismatches; {total - mismatches[field]}/{total} within target")
    lines.extend(["", "## Detailed Diffs", ""])
    lines.extend(details or ["No mismatches."])
    return "\n".join(lines) + "\n", mismatches, details


if __name__ == "__main__":
    report, mismatches, _ = evaluate(REPO_ROOT / "dataset")
    output_path = REPO_ROOT / "evaluation" / "sample_eval_report.md"
    output_path.write_text(report, encoding="utf-8")
    (BASE_DIR / "evaluation").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "evaluation" / "sample_eval_report.md").write_text(report, encoding="utf-8")
    print(report)
    print("total mismatches:", sum(mismatches.values()))
