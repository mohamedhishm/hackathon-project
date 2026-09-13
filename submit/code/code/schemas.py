"""Pydantic v2 schema layer for the domain objects produced by ``data_loader.py``.

This module defines validated data *contracts* for the dataclasses already
declared in ``data_loader.py``. It does not parse CSV files, does not touch
pandas, and does not implement any financial/business logic. It exists so
that other layers of the system (API boundaries, LLM tool schemas, request
validation, etc.) can validate or serialize the same domain objects the
loader already produces, without changing how the loader itself works.

Interview rule preserved here too:
    missing != zero. Optional financial fields stay ``None`` when the
    source value is missing; they are never silently coerced to ``0``.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Shared model configuration
# ---------------------------------------------------------------------------
#
# - `from_attributes=True` lets these models validate directly from the
#   existing dataclass instances (or any object exposing the same
#   attributes), e.g. ProfileSchema.model_validate(profile_dataclass).
# - `extra="forbid"` is used for the leaf/domain records (Profile,
#   FinancialEvent, PaymentOption, Message, ImageRecord) because these
#   correspond 1:1 to known CSV columns via the loader's row parsers; an
#   unexpected extra field most likely means a schema/loader drift bug we
#   want to catch early, not silently ignore.
# - Request / SampleRequest also use `extra="forbid"`: their field set is
#   fully known (the dataclass fields plus the loader-attached nested
#   lists), so the same drift-detection argument applies.


class _DomainModel(BaseModel):
    """Common base: attribute-based validation + strict extra-field policy."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ---------------------------------------------------------------------------
# Domain schemas
# ---------------------------------------------------------------------------


class ProfileSchema(_DomainModel):
    user_id: str
    home_currency: str
    current_available_balance: Decimal
    minimum_balance_to_keep: Decimal
    financial_priorities: list[str]
    expense_categories_to_protect: list[str]
    expense_categories_user_is_willing_to_reduce: list[str]
    expense_categories_user_is_willing_to_stop: list[str]
    payment_methods_user_will_consider: list[str]
    # Blank in CSV means the user will not consider installments (None, not 0).
    max_installment_months: int | None


class FinancialEventSchema(_DomainModel):
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: str
    # Blank amount stays None. Do not invent 0 because an image or message exists.
    amount: Decimal | None
    # Keep the stated currency. Do not convert or infer USD/home currency here.
    currency: str
    event_date: date
    settlement_date: date | None
    status: str
    linked_event_id: str | None
    flexibility: str | None
    minimum_allowed_amount: Decimal | None


class PaymentOptionSchema(_DomainModel):
    """Seller/provider option as copied from the CSV. Never expand installment rows."""

    payment_option_id: str
    request_id: str
    payment_method: str
    payment_amount: Decimal | None
    number_of_payments: int | None
    first_payment_date: date | None
    payment_frequency_days: int | None
    financing_fee: Decimal | None
    total_payable_amount: Decimal | None


class MessageSchema(_DomainModel):
    message_id: str
    user_id: str
    request_id: str | None
    related_event_id: str | None
    sent_at: datetime
    source_type: str
    # Raw text only. Do not parse amounts or amend events in this layer.
    message_text: str


class ImageRecordSchema(_DomainModel):
    """Metadata about an image record and whether it exists.

    This schema does not open, read, or otherwise process the underlying
    image file.
    """

    image_id: str
    user_id: str
    request_id: str | None
    related_event_id: str | None
    exists: bool


class RequestSchema(_DomainModel):
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal | None
    desired_completion_date: date | None
    allows_partial_payment: bool
    request_text: str
    payment_options: list[PaymentOptionSchema] = Field(default_factory=list)
    messages: list[MessageSchema] = Field(default_factory=list)
    images: list[ImageRecordSchema] = Field(default_factory=list)


class SampleRequestSchema(RequestSchema):
    """Labeled reference rows. Labels are data, not loader control flow."""

    amount_safe_to_pay: Decimal | None = None
    affordability_status: str = ""
    recommended_payment_method: str = ""
    payment_plan: str = ""
    earliest_date_for_full_payment: date | None = None
    spending_changes_needed: str = ""
    decision_explanation: str = ""


# ---------------------------------------------------------------------------
# Deliberately NOT modeled here
# ---------------------------------------------------------------------------
#
# `LoadedData` (and its indexes such as events_by_user, events_by_id,
# messages_by_user, messages_by_event, images_by_user, images_by_event,
# payment_options_by_request, exchange_rates, ...) is the loader's internal
# repository/container, not a domain schema. Those dicts/lists are lookup
# structures built for convenient in-process access; they don't correspond
# to a single validated "thing" a downstream consumer would receive as one
# unit. Turning every index into a Pydantic model would just be modeling
# the loader's implementation detail (which dict shape it happens to use
# for lookups), not the domain. If a future stage needs, say, a validated
# "bundle of data for one user" contract, that should be introduced
# explicitly and deliberately then, not auto-generated from LoadedData now.