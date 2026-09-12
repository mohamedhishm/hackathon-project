"""Quick validation/test example for schemas.py.

Not a full test suite — just enough to demonstrate:
  * Decimal is preserved (not silently turned into float)
  * None stays None for optional financial fields (missing != zero)
  * list fields (including nested request lists) work
  * invalid structural data is rejected
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from schemas import (
    ImageRecordSchema,
    PaymentOptionSchema,
    ProfileSchema,
    RequestSchema,
)


# --- Stand-in for the loader's real Profile dataclass, just for this demo ---
@dataclass
class Profile:
    user_id: str
    home_currency: str
    current_available_balance: Decimal
    minimum_balance_to_keep: Decimal
    financial_priorities: list[str]
    expense_categories_to_protect: list[str]
    expense_categories_user_is_willing_to_reduce: list[str]
    expense_categories_user_is_willing_to_stop: list[str]
    payment_methods_user_will_consider: list[str]
    max_installment_months: int | None


def main() -> None:
    # 1. Construct a dataclass instance the way the loader would.
    profile = Profile(
        user_id="user_01",
        home_currency="USD",
        current_available_balance=Decimal("1523.40"),
        minimum_balance_to_keep=Decimal("200.00"),
        financial_priorities=["rent", "groceries"],
        expense_categories_to_protect=["rent"],
        expense_categories_user_is_willing_to_reduce=["entertainment"],
        expense_categories_user_is_willing_to_stop=["subscriptions"],
        payment_methods_user_will_consider=["credit_card", "installments"],
        max_installment_months=None,  # blank in CSV -> None, not 0
    )

    # 2. Validate directly from the dataclass instance (attribute-based).
    profile_schema = ProfileSchema.model_validate(profile, from_attributes=True)

    # Decimal preserved (not coerced to float)
    assert isinstance(profile_schema.current_available_balance, Decimal)
    assert profile_schema.current_available_balance == Decimal("1523.40")
    print("Decimal preserved:", profile_schema.current_available_balance)

    # None stays None (missing != zero)
    assert profile_schema.max_installment_months is None
    print("Optional field stays None:", profile_schema.max_installment_months)

    # List fields work
    assert profile_schema.financial_priorities == ["rent", "groceries"]
    print("List field preserved:", profile_schema.financial_priorities)

    # 3. Nested lists: a Request with payment options and an image record.
    payment_option = PaymentOptionSchema(
        payment_option_id="po_1",
        request_id="req_1",
        payment_method="installments",
        payment_amount=Decimal("100.00"),
        number_of_payments=3,
        first_payment_date=date(2025, 9, 1),
        payment_frequency_days=30,
        financing_fee=None,  # missing stays None, not 0
        total_payable_amount=Decimal("300.00"),
    )
    image = ImageRecordSchema(
        image_id="img_1",
        user_id="user_01",
        request_id="req_1",
        related_event_id=None,
        exists=True,
    )
    request = RequestSchema(
        request_id="req_1",
        user_id="user_01",
        request_date=date(2025, 8, 1),
        request_type="purchase",
        requested_amount=Decimal("300.00"),
        desired_completion_date=None,
        allows_partial_payment=True,
        request_text="Need to pay for a laptop repair",
        payment_options=[payment_option],
        messages=[],
        images=[image],
    )
    assert request.payment_options[0].financing_fee is None
    assert request.images[0].exists is True
    print("Nested list fields work:", len(request.payment_options), "payment option(s)")

    # 4. Invalid structural data is rejected (extra field not in the contract).
    try:
        ProfileSchema.model_validate(
            {
                "user_id": "user_02",
                "home_currency": "USD",
                "current_available_balance": Decimal("10"),
                "minimum_balance_to_keep": Decimal("0"),
                "financial_priorities": [],
                "expense_categories_to_protect": [],
                "expense_categories_user_is_willing_to_reduce": [],
                "expense_categories_user_is_willing_to_stop": [],
                "payment_methods_user_will_consider": [],
                "max_installment_months": None,
                "unexpected_field": "should not be allowed",
            }
        )
    except ValidationError as exc:
        print("Correctly rejected invalid/extra data:")
        print(exc)
    else:
        raise AssertionError("Expected extra field to be rejected")


if __name__ == "__main__":
    main()