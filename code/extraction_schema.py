"""LLM extraction contract (Phase 3): language -> structured facts.

This is NOT the dataset domain schema (that lives in ``schemas.py``).
This is NOT a decision / affordability / simulation model.

Architectural split:

    LLM understands language and fills this contract.
    Python later calculates, simulates, and decides.
    A later validator checks the final recommendation.

The models below only answer:

    "What did the user say, or what is explicitly present in the evidence?"

They must not answer:

    "What should the system do?"

Missing financial facts stay ``None``. missing != zero, missing != false.
Extracted ``amount`` never overwrites ``Request.requested_amount``; that
reconciliation belongs to a later application layer.

No Groq / prompt / client code lives here.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceType = Literal["request", "message", "image"]
SpendingChangeKind = Literal["reduce", "stop"]


class _ExtractionModel(BaseModel):
    """Strict JSON contract for LLM output. Unexpected fields are rejected."""

    model_config = ConfigDict(extra="forbid")


class Evidence(_ExtractionModel):
    """Provenance for one extracted fact. Evidence is not a decision.

    ``source_type`` selects which ID is required:
    - request -> request_id
    - message -> message_id
    - image   -> image_id

    Other IDs stay optional so we do not invent identifiers.
    """

    source_type: SourceType
    request_id: str | None = None
    message_id: str | None = None
    image_id: str | None = None

    @model_validator(mode="after")
    def matching_source_id_is_present(self) -> Self:
        required = {
            "request": ("request_id", self.request_id),
            "message": ("message_id", self.message_id),
            "image": ("image_id", self.image_id),
        }
        field_name, field_value = required[self.source_type]
        if field_value is None or field_value.strip() == "":
            raise ValueError(
                f"{self.source_type} evidence requires a non-empty {field_name}"
            )
        return self


class MentionedDate(_ExtractionModel):
    """A date expression found in language or visible evidence.

    ``exact_date`` is set only when a calendar date is explicit.
    ``raw_expression`` keeps relative/ambiguous phrases such as
    "next month" or "when my salary arrives".

    Do not compute earliest-safe-payment or any other financial date here.
    """

    exact_date: date | None = None
    raw_expression: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class FutureIncomeMention(_ExtractionModel):
    """The user/evidence mentioned future income.

    This is not a confirmation that Python should treat the income as
    settled cash. Amount/date stay None unless they were stated explicitly.
    """

    description: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    date_mention: MentionedDate | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class SpendingChangeMention(_ExtractionModel):
    """The user/evidence mentioned reducing or stopping some spending.

    This is not a recommended spending change. Python will decide later
    whether any change is allowed or needed.
    """

    kind: SpendingChangeKind | None = None
    target: str | None = None
    new_amount: Decimal | None = None
    currency: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class RequestExtraction(_ExtractionModel):
    """Facts extracted from request_text, relevant messages, and images.

    Core scalars keep their own evidence lists so we can answer
    "where did this amount come from?" without mixing dataset fields
    and language-derived fields.
    """

    item: str | None = None
    item_evidence: list[Evidence] = Field(default_factory=list)

    amount: Decimal | None = None
    amount_evidence: list[Evidence] = Field(default_factory=list)

    currency: str | None = None
    currency_evidence: list[Evidence] = Field(default_factory=list)

    # True / False only when the user stated a preference. None = not mentioned.
    partial_payment_intent: bool | None = None
    partial_payment_intent_evidence: list[Evidence] = Field(default_factory=list)

    mentioned_dates: list[MentionedDate] = Field(default_factory=list)
    future_income_mentions: list[FutureIncomeMention] = Field(default_factory=list)
    spending_change_mentions: list[SpendingChangeMention] = Field(default_factory=list)
