"""Final CSV row contract for the Buy or Wait output."""

from __future__ import annotations

from decimal import Decimal
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_STATUS = {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"}
_METHOD = {"full_payment", "partial_payment", "installments", "wait", "not_recommended"}
_PLAN_ENTRY = re.compile(r"^\d{4}-\d{2}-\d{2}:-?\d+(?:\.\d+)?$")
_STOP = re.compile(r"^stop:[^:|]+$")
_REDUCE = re.compile(r"^reduce_to:[^:|]+:-?\d+(?:\.\d+)?$")


class OutputRowSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    requested_amount: Decimal = Field(exclude=True)
    amount_safe_to_pay: Decimal
    affordability_status: str
    recommended_payment_method: str
    payment_plan: str
    earliest_date_for_full_payment: str
    spending_changes_needed: str
    decision_explanation: str

    @field_validator("affordability_status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in _STATUS:
            raise ValueError(f"invalid affordability_status: {value}")
        return value

    @field_validator("recommended_payment_method")
    @classmethod
    def valid_method(cls, value: str) -> str:
        if value not in _METHOD:
            raise ValueError(f"invalid recommended_payment_method: {value}")
        return value

    @field_validator("payment_plan")
    @classmethod
    def valid_plan(cls, value: str) -> str:
        if value != "none" and not all(_PLAN_ENTRY.fullmatch(item) for item in value.split("|")):
            raise ValueError("invalid payment_plan")
        return value

    @field_validator("spending_changes_needed")
    @classmethod
    def valid_changes(cls, value: str) -> str:
        if value != "none":
            entries = value.split("|")
            if len(entries) > 3 or not all(_STOP.fullmatch(item) or _REDUCE.fullmatch(item) for item in entries):
                raise ValueError("invalid spending_changes_needed")
        return value

    @field_validator("earliest_date_for_full_payment")
    @classmethod
    def valid_date(cls, value: str) -> str:
        if value:
            from datetime import date
            date.fromisoformat(value)
        return value

    @field_validator("decision_explanation")
    @classmethod
    def nonempty_explanation(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("decision_explanation must not be empty")
        return value

    @field_validator("amount_safe_to_pay")
    @classmethod
    def bounds(cls, value: Decimal, info) -> Decimal:
        requested = info.data.get("requested_amount")
        if requested is not None and not Decimal("0") <= value <= requested:
            raise ValueError("amount_safe_to_pay is outside requested amount bounds")
        return value
