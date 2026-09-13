"""Regression tests for sample-derived financial safety bugs."""

from datetime import date, timedelta
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_loader import DataLoader
from evidence import extract_message_evidence
from forecaster import find_earliest_full_date


DATASET = Path(__file__).resolve().parent.parent / "dataset"


def test_pending_payout_is_not_projected_as_income() -> None:
    data = DataLoader(DATASET).load()
    messages = data.messages_by_user["user_10"]
    evidence = extract_message_evidence("user_10", messages, date(2024, 12, 6))
    assert evidence.pending_income is True


def test_later_payment_cannot_hide_an_earlier_minimum_breach() -> None:
    data = DataLoader(DATASET).load()
    request = data.sample_requests_by_id["request_25"]
    profile = data.profiles_by_user[request.user_id]
    evidence = extract_message_evidence(
        request.user_id,
        data.messages_by_user.get(request.user_id, []),
        request.request_date,
    )
    result = find_earliest_full_date(
        profile,
        data.events_by_user[request.user_id],
        evidence,
        data.exchange_rates,
        request.request_date,
        request.requested_amount,
        request.desired_completion_date,
    )
    assert result is None


def test_scheduled_salary_with_new_description_is_not_double_counted() -> None:
    data = DataLoader(DATASET).load()
    request = data.sample_requests_by_id["request_25"]
    profile = data.profiles_by_user[request.user_id]
    evidence = extract_message_evidence(
        request.user_id,
        data.messages_by_user.get(request.user_id, []),
        request.request_date,
    )
    from forecaster import simulate_timeline
    timeline = simulate_timeline(
        profile,
        data.events_by_user[request.user_id],
        evidence,
        data.exchange_rates,
        request.request_date,
    )
    before = timeline[date(2024, 3, 14)]
    after = timeline[date(2024, 3, 15)]
    assert after - before < Decimal("40000000")


if __name__ == "__main__":
    test_pending_payout_is_not_projected_as_income()
    test_later_payment_cannot_hide_an_earlier_minimum_breach()
    test_scheduled_salary_with_new_description_is_not_double_counted()
    print("regression tests passed")
