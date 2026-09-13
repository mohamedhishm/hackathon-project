"""Isolation layer: raw dataset files -> typed, indexed Python objects.

Public consumers should use indexes such as ``events_by_user[user_id]`` and
``events_by_id[event_id]``. They must not call ``pd.read_csv`` or filter
DataFrames. A request does not own the user's full event history.

Pandas is an internal CSV reader only. It is not part of the LoadedData API.

Interview rule preserved here:
    Preserve missingness instead of silently converting missing financial values
    to zero, because zero is a real financial value and would change downstream
    decisions. missing ≠ zero.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

# ---------------------------------------------------------------------------
# Dataclasses (schemas / Pydantic belong to a later stage)
# ---------------------------------------------------------------------------


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
    # Blank in CSV means the user will not consider installments (None, not 0).
    max_installment_months: int | None


@dataclass
class FinancialEvent:
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


@dataclass
class PaymentOption:
    """Seller/provider option copied from the CSV. Never expand installment rows."""

    payment_option_id: str
    request_id: str
    payment_method: str
    payment_amount: Decimal | None
    number_of_payments: int | None
    first_payment_date: date | None
    payment_frequency_days: int | None
    financing_fee: Decimal | None
    total_payable_amount: Decimal | None


@dataclass
class Message:
    message_id: str
    user_id: str
    request_id: str | None
    related_event_id: str | None
    sent_at: datetime
    source_type: str
    # Raw text only. Do not parse amounts or amend events in this layer.
    message_text: str


@dataclass
class ImageRecord:
    image_id: str
    user_id: str
    request_id: str | None
    related_event_id: str | None
    exists: bool


@dataclass
class Request:
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal | None
    desired_completion_date: date | None
    allows_partial_payment: bool
    request_text: str
    payment_options: list[PaymentOption] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    images: list[ImageRecord] = field(default_factory=list)


@dataclass
class SampleRequest(Request):
    """Labeled reference rows. Labels are data, not loader control flow."""

    amount_safe_to_pay: Decimal | None = None
    affordability_status: str = ""
    recommended_payment_method: str = ""
    payment_plan: str = ""
    earliest_date_for_full_payment: date | None = None
    spending_changes_needed: str = ""
    decision_explanation: str = ""


@dataclass
class LoadedData:
    requests_by_id: dict[str, Request]
    sample_requests_by_id: dict[str, SampleRequest]
    profiles_by_user: dict[str, Profile]
    events_by_user: dict[str, list[FinancialEvent]]
    events_by_id: dict[str, FinancialEvent]
    payment_options_by_request: dict[str, list[PaymentOption]]
    # Key = (rate_date, from_currency, to_currency). Rates are stored, not applied.
    exchange_rates: dict[tuple[date, str, str], Decimal]
    messages_by_request: dict[str, list[Message]]
    messages_by_event: dict[str, list[Message]]
    messages_by_user: dict[str, list[Message]]
    images_by_event: dict[str, list[ImageRecord]]
    images_by_request: dict[str, list[ImageRecord]]
    images_by_id: dict[str, ImageRecord]
    images_by_user: dict[str, list[ImageRecord]]

    def get_user_data(self, user_id: str) -> dict[str, Any]:
        return {
            "profile": self.profiles_by_user[user_id],
            "events": self.events_by_user.get(user_id, []),
            "messages": self.messages_by_user.get(user_id, []),
            "images": self.images_by_user.get(user_id, []),
        }


# ---------------------------------------------------------------------------
# Private parsers
# ---------------------------------------------------------------------------


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return False


def _cell(row: Mapping[str, Any], column: str) -> Any:
    if column not in row:
        raise KeyError(f"Missing CSV column: {column}")
    return row[column]


def _parse_str(value: Any, *, required: bool = True) -> str | None:
    if _is_blank(value):
        if required:
            raise ValueError("Expected a non-empty string")
        return None
    return str(value).strip()


def _parse_date(value: Any) -> date | None:
    """CSV ``2025-08-08`` -> date(2025, 8, 8). Empty -> None."""
    if _is_blank(value):
        return None
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    return date.fromisoformat(text)


def _parse_datetime(value: Any) -> datetime:
    """Timezone-aware when the CSV uses a trailing ``Z``."""
    if _is_blank(value):
        raise ValueError("Expected a datetime value")
    text = str(value).strip()
    if text.endswith("Z"):
        return datetime.fromisoformat(text[:-1]).replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(text)
    return parsed


def _parse_optional_number(value: Any) -> Decimal | None:
    """Blank/NaN -> None. Explicit 0 stays 0. missing ≠ zero."""
    if _is_blank(value):
        return None
    text = str(value).strip().replace(",", "")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid number: {value!r}") from exc


def _parse_required_number(value: Any) -> Decimal:
    parsed = _parse_optional_number(value)
    if parsed is None:
        raise ValueError("Expected a number, got a blank cell")
    return parsed


def _parse_optional_int(value: Any) -> int | None:
    if _is_blank(value):
        return None
    text = str(value).strip()
    parsed = Decimal(text)
    if parsed != parsed.to_integral_value():
        raise ValueError(f"Expected a whole number, got {value!r}")
    return int(parsed)


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if _is_blank(value):
        raise ValueError("Expected a boolean, got a blank cell")
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise ValueError(f"Invalid boolean: {value!r}")


def _split_list(value: Any) -> list[str]:
    """Pipe-separated lists. Empty cell -> [] (not None)."""
    if _is_blank(value):
        return []
    return [token.strip() for token in str(value).split("|") if token.strip()]


def _csv_path(data_dir: Path, filename: str) -> Path:
    path = data_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    return path


def _read_csv(data_dir: Path, filename: str) -> list[dict[str, Any]]:
    path = _csv_path(data_dir, filename)
    # Read as strings so blank financial cells stay blank instead of becoming 0/NaN.
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    return frame.to_dict(orient="records")


def _sort_events(events: list[FinancialEvent]) -> list[FinancialEvent]:
    return sorted(events, key=lambda event: (event.event_date, event.event_id))


def _sort_messages(messages: list[Message]) -> list[Message]:
    return sorted(messages, key=lambda message: (message.sent_at, message.message_id))


def _sort_images(images: list[ImageRecord]) -> list[ImageRecord]:
    return sorted(images, key=lambda image: image.image_id)


def _sort_options(options: list[PaymentOption]) -> list[PaymentOption]:
    return sorted(options, key=lambda option: option.payment_option_id)


def _set_unique(index: dict, key: Any, value: Any, dataset: str) -> None:
    if key in index:
        raise ValueError(f"Duplicate key in {dataset}: {key!r}")
    index[key] = value


def _require_known(key: str, known: Mapping[str, Any], *, dataset: str, field: str) -> None:
    if key not in known:
        raise ValueError(
            f"Unknown {field} {key!r} referenced by {dataset}"
        )


def _index_image_files(media_dir: Path) -> dict[str, Path]:
    """Map image_id (file stem) -> on-disk path, using whatever extension exists."""
    by_stem: dict[str, Path] = {}
    if not media_dir.is_dir():
        return by_stem
    for path in sorted(media_dir.iterdir()):
        if not path.is_file():
            continue
        stem = path.stem
        if stem in by_stem:
            raise ValueError(
                f"Duplicate image file for {stem!r} in media/images: "
                f"{by_stem[stem].name} and {path.name}"
            )
        by_stem[stem] = path
    return by_stem


# ---------------------------------------------------------------------------
# Row mappers
# ---------------------------------------------------------------------------


def _profile_from_row(row: Mapping[str, Any]) -> Profile:
    return Profile(
        user_id=_parse_str(_cell(row, "user_id")),  # type: ignore[arg-type]
        home_currency=_parse_str(_cell(row, "home_currency")),  # type: ignore[arg-type]
        current_available_balance=_parse_required_number(
            _cell(row, "current_available_balance")
        ),
        minimum_balance_to_keep=_parse_required_number(
            _cell(row, "minimum_balance_to_keep")
        ),
        financial_priorities=_split_list(_cell(row, "financial_priorities")),
        expense_categories_to_protect=_split_list(
            _cell(row, "expense_categories_to_protect")
        ),
        expense_categories_user_is_willing_to_reduce=_split_list(
            _cell(row, "expense_categories_user_is_willing_to_reduce")
        ),
        expense_categories_user_is_willing_to_stop=_split_list(
            _cell(row, "expense_categories_user_is_willing_to_stop")
        ),
        payment_methods_user_will_consider=_split_list(
            _cell(row, "payment_methods_user_will_consider")
        ),
        max_installment_months=_parse_optional_int(
            _cell(row, "max_installment_months")
        ),
    )


def _event_from_row(row: Mapping[str, Any]) -> FinancialEvent:
    event_date = _parse_date(_cell(row, "event_date"))
    if event_date is None:
        raise ValueError(f"Event {_cell(row, 'event_id')!r} is missing event_date")
    return FinancialEvent(
        event_id=_parse_str(_cell(row, "event_id")),  # type: ignore[arg-type]
        user_id=_parse_str(_cell(row, "user_id")),  # type: ignore[arg-type]
        event_type=_parse_str(_cell(row, "event_type")),  # type: ignore[arg-type]
        description=_parse_str(_cell(row, "description"), required=False) or "",
        category=_parse_str(_cell(row, "category"), required=False) or "",
        direction=_parse_str(_cell(row, "direction")),  # type: ignore[arg-type]
        amount=_parse_optional_number(_cell(row, "amount")),
        currency=_parse_str(_cell(row, "currency")),  # type: ignore[arg-type]
        event_date=event_date,
        settlement_date=_parse_date(_cell(row, "settlement_date")),
        status=_parse_str(_cell(row, "status")),  # type: ignore[arg-type]
        linked_event_id=_parse_str(_cell(row, "linked_event_id"), required=False),
        flexibility=_parse_str(_cell(row, "flexibility"), required=False),
        minimum_allowed_amount=_parse_optional_number(
            _cell(row, "minimum_allowed_amount")
        ),
    )


def _request_core(row: Mapping[str, Any]) -> dict[str, Any]:
    request_date = _parse_date(_cell(row, "request_date"))
    if request_date is None:
        raise ValueError(f"Request {_cell(row, 'request_id')!r} is missing request_date")
    return {
        "request_id": _parse_str(_cell(row, "request_id")),
        "user_id": _parse_str(_cell(row, "user_id")),
        "request_date": request_date,
        "request_type": _parse_str(_cell(row, "request_type")),
        "requested_amount": _parse_optional_number(_cell(row, "requested_amount")),
        "desired_completion_date": _parse_date(_cell(row, "desired_completion_date")),
        "allows_partial_payment": _parse_bool(_cell(row, "allows_partial_payment")),
        "request_text": _parse_str(_cell(row, "request_text"), required=False) or "",
    }


def _request_from_row(row: Mapping[str, Any]) -> Request:
    return Request(**_request_core(row))


def _sample_request_from_row(row: Mapping[str, Any]) -> SampleRequest:
    return SampleRequest(
        **_request_core(row),
        amount_safe_to_pay=_parse_optional_number(_cell(row, "amount_safe_to_pay")),
        affordability_status=_parse_str(
            _cell(row, "affordability_status"), required=False
        )
        or "",
        recommended_payment_method=_parse_str(
            _cell(row, "recommended_payment_method"), required=False
        )
        or "",
        payment_plan=_parse_str(_cell(row, "payment_plan"), required=False) or "",
        earliest_date_for_full_payment=_parse_date(
            _cell(row, "earliest_date_for_full_payment")
        ),
        spending_changes_needed=_parse_str(
            _cell(row, "spending_changes_needed"), required=False
        )
        or "",
        decision_explanation=_parse_str(
            _cell(row, "decision_explanation"), required=False
        )
        or "",
    )


def _payment_option_from_row(row: Mapping[str, Any]) -> PaymentOption:
    return PaymentOption(
        payment_option_id=_parse_str(_cell(row, "payment_option_id")),  # type: ignore[arg-type]
        request_id=_parse_str(_cell(row, "request_id")),  # type: ignore[arg-type]
        payment_method=_parse_str(_cell(row, "payment_method")),  # type: ignore[arg-type]
        payment_amount=_parse_optional_number(_cell(row, "payment_amount")),
        number_of_payments=_parse_optional_int(_cell(row, "number_of_payments")),
        first_payment_date=_parse_date(_cell(row, "first_payment_date")),
        payment_frequency_days=_parse_optional_int(
            _cell(row, "payment_frequency_days")
        ),
        financing_fee=_parse_optional_number(_cell(row, "financing_fee")),
        total_payable_amount=_parse_optional_number(
            _cell(row, "total_payable_amount")
        ),
    )


def _message_from_row(row: Mapping[str, Any]) -> Message:
    return Message(
        message_id=_parse_str(_cell(row, "message_id")),  # type: ignore[arg-type]
        user_id=_parse_str(_cell(row, "user_id")),  # type: ignore[arg-type]
        request_id=_parse_str(_cell(row, "request_id"), required=False),
        related_event_id=_parse_str(_cell(row, "related_event_id"), required=False),
        sent_at=_parse_datetime(_cell(row, "sent_at")),
        source_type=_parse_str(_cell(row, "source_type")),  # type: ignore[arg-type]
        message_text=_parse_str(_cell(row, "message_text"), required=False) or "",
    )


def _image_from_row(
    row: Mapping[str, Any],
    media_dir: Path,
    files_by_id: Mapping[str, Path],
) -> ImageRecord:
    image_id = _parse_str(_cell(row, "image_id"))
    assert image_id is not None
    return ImageRecord(
        image_id=image_id,
        user_id=_parse_str(_cell(row, "user_id")),  # type: ignore[arg-type]
        request_id=_parse_str(_cell(row, "request_id"), required=False),
        related_event_id=_parse_str(_cell(row, "related_event_id"), required=False),
        exists=image_id in files_by_id,
    )


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class DataLoader:
    """Converts raw heterogeneous dataset files into indexed Python data."""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def load(self) -> LoadedData:
        profiles_by_user: dict[str, Profile] = {}
        for row in _read_csv(self.data_dir, "financial_profiles.csv"):
            profile = _profile_from_row(row)
            _set_unique(
                profiles_by_user, profile.user_id, profile, "financial_profiles.csv"
            )

        events_by_id: dict[str, FinancialEvent] = {}
        events_by_user_acc: dict[str, list[FinancialEvent]] = defaultdict(list)
        for row in _read_csv(self.data_dir, "financial_events.csv"):
            event = _event_from_row(row)
            _set_unique(events_by_id, event.event_id, event, "financial_events.csv")
            events_by_user_acc[event.user_id].append(event)
        events_by_user = {
            user_id: _sort_events(events)
            for user_id, events in events_by_user_acc.items()
        }

        payment_options_by_id: dict[str, PaymentOption] = {}
        payment_options_acc: dict[str, list[PaymentOption]] = defaultdict(list)
        for row in _read_csv(self.data_dir, "request_payment_options.csv"):
            option = _payment_option_from_row(row)
            _set_unique(
                payment_options_by_id,
                option.payment_option_id,
                option,
                "request_payment_options.csv",
            )
            payment_options_acc[option.request_id].append(option)
        payment_options_by_request = {
            request_id: _sort_options(options)
            for request_id, options in payment_options_acc.items()
        }

        exchange_rates: dict[tuple[date, str, str], Decimal] = {}
        for row in _read_csv(self.data_dir, "exchange_rates.csv"):
            rate_date = _parse_date(_cell(row, "rate_date"))
            if rate_date is None:
                raise ValueError("exchange_rates.csv row is missing rate_date")
            from_currency = _parse_str(_cell(row, "from_currency"))
            to_currency = _parse_str(_cell(row, "to_currency"))
            assert from_currency is not None and to_currency is not None
            rate_key = (rate_date, from_currency, to_currency)
            _set_unique(
                exchange_rates,
                rate_key,
                _parse_required_number(_cell(row, "rate")),
                "exchange_rates.csv",
            )

        messages_by_id: dict[str, Message] = {}
        messages_by_request_acc: dict[str, list[Message]] = defaultdict(list)
        messages_by_event_acc: dict[str, list[Message]] = defaultdict(list)
        messages_by_user_acc: dict[str, list[Message]] = defaultdict(list)
        for row in _read_csv(self.data_dir, "messages.csv"):
            message = _message_from_row(row)
            _set_unique(messages_by_id, message.message_id, message, "messages.csv")
            messages_by_user_acc[message.user_id].append(message)
            if message.request_id:
                messages_by_request_acc[message.request_id].append(message)
            if message.related_event_id:
                messages_by_event_acc[message.related_event_id].append(message)
        messages_by_request = {
            key: _sort_messages(value) for key, value in messages_by_request_acc.items()
        }
        messages_by_event = {
            key: _sort_messages(value) for key, value in messages_by_event_acc.items()
        }
        messages_by_user = {
            key: _sort_messages(value) for key, value in messages_by_user_acc.items()
        }

        media_dir = self.data_dir / "media" / "images"
        files_by_id = _index_image_files(media_dir)
        images_by_id: dict[str, ImageRecord] = {}
        images_by_event_acc: dict[str, list[ImageRecord]] = defaultdict(list)
        images_by_request_acc: dict[str, list[ImageRecord]] = defaultdict(list)
        images_by_user_acc: dict[str, list[ImageRecord]] = defaultdict(list)
        for row in _read_csv(self.data_dir, "images.csv"):
            image = _image_from_row(row, media_dir, files_by_id)
            _set_unique(images_by_id, image.image_id, image, "images.csv")
            images_by_user_acc[image.user_id].append(image)
            if image.request_id:
                images_by_request_acc[image.request_id].append(image)
            if image.related_event_id:
                images_by_event_acc[image.related_event_id].append(image)
        images_by_event = {
            key: _sort_images(value) for key, value in images_by_event_acc.items()
        }
        images_by_request = {
            key: _sort_images(value) for key, value in images_by_request_acc.items()
        }
        images_by_user = {
            key: _sort_images(value) for key, value in images_by_user_acc.items()
        }

        # requests.csv is the production list. sample_requests.csv is labeled
        # reference only — never substituted for requests.csv here.
        requests_by_id: dict[str, Request] = {}
        for row in _read_csv(self.data_dir, "requests.csv"):
            request = _request_from_row(row)
            _set_unique(requests_by_id, request.request_id, request, "requests.csv")

        sample_requests_by_id: dict[str, SampleRequest] = {}
        for row in _read_csv(self.data_dir, "sample_requests.csv"):
            sample = _sample_request_from_row(row)
            _set_unique(
                sample_requests_by_id,
                sample.request_id,
                sample,
                "sample_requests.csv",
            )

        known_request_ids = dict(requests_by_id)
        known_request_ids.update(sample_requests_by_id)
        self._validate_references(
            profiles_by_user=profiles_by_user,
            events_by_id=events_by_id,
            known_request_ids=known_request_ids,
            payment_options_by_request=payment_options_by_request,
            messages_by_user=messages_by_user,
            images_by_id=images_by_id,
        )

        for request in requests_by_id.values():
            self._attach_request_views(
                request,
                payment_options_by_request=payment_options_by_request,
                messages_by_request=messages_by_request,
                images_by_request=images_by_request,
            )
        for sample in sample_requests_by_id.values():
            self._attach_request_views(
                sample,
                payment_options_by_request=payment_options_by_request,
                messages_by_request=messages_by_request,
                images_by_request=images_by_request,
            )

        return LoadedData(
            requests_by_id=requests_by_id,
            sample_requests_by_id=sample_requests_by_id,
            profiles_by_user=profiles_by_user,
            events_by_user=events_by_user,
            events_by_id=events_by_id,
            payment_options_by_request=payment_options_by_request,
            exchange_rates=exchange_rates,
            messages_by_request=messages_by_request,
            messages_by_event=messages_by_event,
            messages_by_user=messages_by_user,
            images_by_event=images_by_event,
            images_by_request=images_by_request,
            images_by_id=images_by_id,
            images_by_user=images_by_user,
        )

    @staticmethod
    def _validate_references(
        *,
        profiles_by_user: dict[str, Profile],
        events_by_id: dict[str, FinancialEvent],
        known_request_ids: Mapping[str, Request],
        payment_options_by_request: dict[str, list[PaymentOption]],
        messages_by_user: dict[str, list[Message]],
        images_by_id: dict[str, ImageRecord],
    ) -> None:
        """Check FK presence only. No affordability or cash-flow decisions."""
        for event in events_by_id.values():
            _require_known(
                event.user_id,
                profiles_by_user,
                dataset="financial_events.csv",
                field="user_id",
            )
            if event.linked_event_id:
                _require_known(
                    event.linked_event_id,
                    events_by_id,
                    dataset=f"financial_events.csv ({event.event_id})",
                    field="linked_event_id",
                )

        for request in known_request_ids.values():
            dataset = (
                "sample_requests.csv"
                if isinstance(request, SampleRequest)
                else "requests.csv"
            )
            _require_known(
                request.user_id,
                profiles_by_user,
                dataset=dataset,
                field="user_id",
            )

        for request_id, options in payment_options_by_request.items():
            _require_known(
                request_id,
                known_request_ids,
                dataset="request_payment_options.csv",
                field="request_id",
            )
            for option in options:
                _require_known(
                    option.request_id,
                    known_request_ids,
                    dataset=f"request_payment_options.csv ({option.payment_option_id})",
                    field="request_id",
                )

        for user_id, messages in messages_by_user.items():
            _require_known(
                user_id,
                profiles_by_user,
                dataset="messages.csv",
                field="user_id",
            )
            for message in messages:
                if message.request_id:
                    _require_known(
                        message.request_id,
                        known_request_ids,
                        dataset=f"messages.csv ({message.message_id})",
                        field="request_id",
                    )
                if message.related_event_id:
                    _require_known(
                        message.related_event_id,
                        events_by_id,
                        dataset=f"messages.csv ({message.message_id})",
                        field="related_event_id",
                    )

        for image in images_by_id.values():
            _require_known(
                image.user_id,
                profiles_by_user,
                dataset=f"images.csv ({image.image_id})",
                field="user_id",
            )
            if image.request_id:
                _require_known(
                    image.request_id,
                    known_request_ids,
                    dataset=f"images.csv ({image.image_id})",
                    field="request_id",
                )
            if image.related_event_id:
                _require_known(
                    image.related_event_id,
                    events_by_id,
                    dataset=f"images.csv ({image.image_id})",
                    field="related_event_id",
                )

    @staticmethod
    def _attach_request_views(
        request: Request,
        *,
        payment_options_by_request: dict[str, list[PaymentOption]],
        messages_by_request: dict[str, list[Message]],
        images_by_request: dict[str, list[ImageRecord]],
    ) -> None:
        request.payment_options = payment_options_by_request.get(request.request_id, [])
        request.messages = messages_by_request.get(request.request_id, [])
        request.images = images_by_request.get(request.request_id, [])


if __name__ == "__main__":
    dataset_dir = Path(__file__).resolve().parent.parent / "dataset"
    data = DataLoader(dataset_dir).load()

    print(f"n profiles: {len(data.profiles_by_user)}")
    print(f"n events: {len(data.events_by_id)}")
    print(f"n requests: {len(data.requests_by_id)}")
    print(f"n sample requests: {len(data.sample_requests_by_id)}")

    example_user_id = "user_01"
    user_bundle = data.get_user_data(example_user_id)
    print(
        "user lookup:",
        example_user_id,
        "events=",
        len(user_bundle["events"]),
        "messages=",
        len(user_bundle["messages"]),
        "images=",
        len(user_bundle["images"]),
        "max_installment_months=",
        user_bundle["profile"].max_installment_months,
    )

    fx_key = next(iter(data.exchange_rates))
    print("fx lookup:", fx_key, "->", data.exchange_rates[fx_key])

    example_request_id = next(iter(data.requests_by_id))
    options = data.payment_options_by_request.get(example_request_id, [])
    print(
        "payment options:",
        example_request_id,
        "count=",
        len(options),
        "methods=",
        [option.payment_method for option in options],
    )
    print(
        "events_by_user count:",
        len(data.events_by_user[data.requests_by_id[example_request_id].user_id]),
    )
