"""Focused tests for the Phase 3 extraction contract.

Not a full suite — covers the interview-critical rules:
  * valid extraction object
  * Decimal preserved (not float)
  * missing stays None (not 0 / not False)
  * partial_payment_intent is bool | None
  * evidence requires the matching source id
  * nested evidence on mentions
  * extra="forbid" rejects decision fields
  * invalid monetary types are rejected
"""

from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from extraction_schema import (
    Evidence,
    FutureIncomeMention,
    MentionedDate,
    RequestExtraction,
    SpendingChangeMention,
)


def _request_evidence() -> Evidence:
    return Evidence(source_type="request", request_id="request_01")


def test_valid_extraction_object() -> None:
    extraction = RequestExtraction(
        item="laptop",
        item_evidence=[_request_evidence()],
        amount=Decimal("2000"),
        amount_evidence=[_request_evidence()],
        currency="USD",
        currency_evidence=[_request_evidence()],
        partial_payment_intent=True,
        partial_payment_intent_evidence=[_request_evidence()],
    )
    assert extraction.item == "laptop"
    assert extraction.amount == Decimal("2000")
    assert extraction.currency == "USD"
    assert extraction.partial_payment_intent is True
    print("valid extraction object: ok")


def test_decimal_preservation() -> None:
    extraction = RequestExtraction(amount=Decimal("1999.50"))
    assert type(extraction.amount) is Decimal
    assert extraction.amount == Decimal("1999.50")
    print("Decimal preserved:", extraction.amount)


def test_none_preservation() -> None:
    extraction = RequestExtraction()
    assert extraction.item is None
    assert extraction.amount is None
    assert extraction.currency is None
    assert extraction.partial_payment_intent is None
    assert extraction.mentioned_dates == []
    assert extraction.future_income_mentions == []
    assert extraction.spending_change_mentions == []
    print("missing fields stay None / empty: ok")


def test_partial_payment_intent_three_states() -> None:
    omitted = RequestExtraction()
    wants_partial = RequestExtraction(partial_payment_intent=True)
    wants_full = RequestExtraction(partial_payment_intent=False)

    assert omitted.partial_payment_intent is None
    assert wants_partial.partial_payment_intent is True
    assert wants_full.partial_payment_intent is False
    assert omitted.partial_payment_intent is not False
    print("partial_payment_intent True/False/None: ok")


def test_evidence_validation() -> None:
    request_ev = Evidence(source_type="request", request_id="request_26")
    message_ev = Evidence(source_type="message", message_id="message_01")
    image_ev = Evidence(source_type="image", image_id="image_07")
    assert request_ev.request_id == "request_26"
    assert message_ev.message_id == "message_01"
    assert image_ev.image_id == "image_07"

    try:
        Evidence(source_type="message", request_id="request_26")
    except ValidationError:
        print("message evidence without message_id rejected: ok")
    else:
        raise AssertionError("Expected message evidence to require message_id")

    try:
        Evidence(source_type="request", request_id="  ")
    except ValidationError:
        print("blank request_id rejected: ok")
    else:
        raise AssertionError("Expected blank request_id to be rejected")


def test_nested_evidence_on_mentions() -> None:
    salary_date = MentionedDate(
        exact_date=date(2025, 9, 15),
        raw_expression="September 15",
        evidence=[Evidence(source_type="message", message_id="message_10")],
    )
    income = FutureIncomeMention(
        description="salary",
        amount=None,
        currency=None,
        date_mention=salary_date,
        evidence=[Evidence(source_type="message", message_id="message_10")],
    )
    spending = SpendingChangeMention(
        kind="reduce",
        target="entertainment",
        new_amount=None,
        currency=None,
        evidence=[Evidence(source_type="request", request_id="request_02")],
    )
    extraction = RequestExtraction(
        mentioned_dates=[
            MentionedDate(
                exact_date=None,
                raw_expression="next month",
                evidence=[_request_evidence()],
            )
        ],
        future_income_mentions=[income],
        spending_change_mentions=[spending],
    )
    assert extraction.mentioned_dates[0].exact_date is None
    assert extraction.future_income_mentions[0].amount is None
    assert extraction.future_income_mentions[0].date_mention is not None
    assert extraction.future_income_mentions[0].date_mention.exact_date == date(
        2025, 9, 15
    )
    assert extraction.spending_change_mentions[0].kind == "reduce"
    print("nested mention evidence: ok")


def test_extra_forbid_rejects_decision_fields() -> None:
    try:
        RequestExtraction.model_validate(
            {
                "item": "laptop",
                "affordability_status": "affordable_now",
            }
        )
    except ValidationError as exc:
        print("decision field affordability_status rejected: ok")
        print(exc)
    else:
        raise AssertionError("Expected extra decision field to be rejected")


def test_invalid_amount_type_rejected() -> None:
    try:
        RequestExtraction.model_validate({"amount": "not-a-number"})
    except ValidationError:
        print("invalid amount type rejected: ok")
    else:
        raise AssertionError("Expected non-numeric amount to be rejected")


def test_missing_is_not_zero_or_false() -> None:
    extraction = RequestExtraction.model_validate({"item": "laptop"})
    assert extraction.item == "laptop"
    assert extraction.amount is None
    assert extraction.amount != 0
    assert extraction.currency is None
    assert extraction.partial_payment_intent is None
    print("I want a laptop -> amount None, currency None: ok")


def main() -> None:
    test_valid_extraction_object()
    test_decimal_preservation()
    test_none_preservation()
    test_partial_payment_intent_three_states()
    test_evidence_validation()
    test_nested_evidence_on_mentions()
    test_extra_forbid_rejects_decision_fields()
    test_invalid_amount_type_rejected()
    test_missing_is_not_zero_or_false()
    print("all extraction schema tests passed")


if __name__ == "__main__":
    main()
