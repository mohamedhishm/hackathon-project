"""Evidence reconciliation layer for Buy or Wait? financial agent.

Reconciles message and OCR evidence into clean, immutable user financial context
without mutating the raw LoadedData or domain objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from decimal import Decimal
import re
from typing import Mapping, Sequence

from data_loader import FinancialEvent, ImageRecord, Message, Profile, Request


@dataclass(frozen=True)
class ExtractedImageEvidence:
    """Structured evidence extracted from receipt/bill images."""
    image_id: str
    event_id: str | None
    amount: Decimal | None
    currency: str | None
    statement_date: date | None


@dataclass(frozen=True)
class ExtractedMessageEvidence:
    """Structured financial directives extracted from messages."""
    user_id: str
    salary_override: Decimal | None = None
    salary_effective_date: date | None = None
    rent_increase_pct: Decimal | None = None
    one_time_arrears: tuple[tuple[date, Decimal], ...] = ()
    contract_ended: bool = False
    pending_income: bool = False
    confirmed_invoices: tuple[tuple[date, Decimal, str], ...] = ()


def resolve_event_amounts(
    events: Sequence[FinancialEvent],
    images_by_event: Mapping[str, Sequence[ImageRecord]],
    image_evidence: Mapping[str, ExtractedImageEvidence],
) -> tuple[list[FinancialEvent], tuple[str, ...]]:
    """Return copied events with only explicitly extracted image amounts filled.

    Missing amounts remain missing. The second return value lists unresolved
    event IDs so callers cannot silently treat absent OCR/vision evidence as 0.
    """
    resolved: list[FinancialEvent] = []
    unresolved: list[str] = []
    for event in events:
        if event.amount is not None:
            resolved.append(event)
            continue
        evidence = None
        for image in images_by_event.get(event.event_id, ()):
            evidence = image_evidence.get(image.image_id)
            if evidence is not None and evidence.amount is not None:
                break
        if evidence is None or evidence.amount is None:
            unresolved.append(event.event_id)
            resolved.append(event)
            continue
        if evidence.event_id and evidence.event_id != event.event_id:
            unresolved.append(event.event_id)
            resolved.append(event)
            continue
        resolved.append(replace(event, amount=evidence.amount))
    return resolved, tuple(unresolved)


def extract_image_evidence_with_ocr(
    images: Sequence[ImageRecord],
) -> dict[str, ExtractedImageEvidence]:
    """Best-effort local OCR adapter; returns no facts when OCR is unavailable.

    This adapter deliberately emits only visible amount/currency patterns and
    never makes an affordability decision. Production callers must report any
    image that remains unresolved after this step.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return {}

    extracted: dict[str, ExtractedImageEvidence] = {}
    for record in images:
        if not record.exists:
            continue
        text = pytesseract.image_to_string(Image.open(record.image_path))
        matches = re.findall(r"\b(IDR|INR|USD|EUR|ZAR)\s*([\d,]+(?:\.\d+)?)", text, re.I)
        if not matches:
            continue
        currency, raw_amount = matches[-1]
        extracted[record.image_id] = ExtractedImageEvidence(
            image_id=record.image_id,
            event_id=record.related_event_id,
            amount=Decimal(raw_amount.replace(",", "")),
            currency=currency.upper(),
            statement_date=None,
        )
    return extracted


def extract_message_evidence(
    user_id: str,
    messages: Sequence[Message],
    request_date: date,
) -> ExtractedMessageEvidence:
    """Deterministically extracts financial updates from user messages."""
    salary_override: Decimal | None = None
    salary_effective_date: date | None = None
    rent_increase_pct: Decimal | None = None
    arrears_list: list[tuple[date, Decimal]] = []
    contract_ended = False
    pending_income = False
    confirmed_invoices_list: list[tuple[date, Decimal, str]] = []

    # Sort messages by sent_at
    sorted_msgs = sorted(messages, key=lambda m: m.sent_at)

    for m in sorted_msgs:
        text = m.message_text
        if not text:
            continue

        # 1. Salary change / increase / reduction
        # Handles English and Indonesian payroll notifications
        m_sal = re.search(
            r'(?:gaji|salary|monthly pay|gaji pokok).*?(?:naik menjadi|is|resumes|reduced to|pokok adalah|dikonfirmasi adalah|akan berupa)\s*([A-Z]{3})?\s*([\d,\.]+)',
            text,
            re.IGNORECASE,
        )
        m_date = re.search(
            r'(?:mulai|effective|starting|from|expected on|dikonfirmasi untuk|date is)\s*(\d{4}-\d{2}-\d{2})',
            text,
            re.IGNORECASE,
        )
        if m_sal:
            amt_str = m_sal.group(2).replace(',', '')
            try:
                amt = Decimal(amt_str)
                eff_d = date.fromisoformat(m_date.group(1)) if m_date else None
                salary_override = amt
                salary_effective_date = eff_d
            except Exception:
                pass

        # 2. First salary from new job
        m_first = re.search(
            r'(?:first salary will be|gaji pertama.*?adalah)\s*([A-Z]{3})?\s*([\d,\.]+)',
            text,
            re.IGNORECASE,
        )
        if m_first:
            amt_str = m_first.group(2).replace(',', '')
            try:
                amt = Decimal(amt_str)
                eff_d = date.fromisoformat(m_date.group(1)) if m_date else None
                salary_override = amt
                salary_effective_date = eff_d
            except Exception:
                pass

        # 3. One-time arrears / backpay adjustment
        m_arr = re.search(
            r'(?:arrears adjustment of|penyesuaian tunggakan.*?sebesar)\s*([A-Z]{3})?\s*([\d,\.]+)',
            text,
            re.IGNORECASE,
        )
        if m_arr:
            amt_str = m_arr.group(2).replace(',', '')
            try:
                arr_amt = Decimal(amt_str)
                arr_d = salary_effective_date or request_date
                arrears_list.append((arr_d, arr_amt))
            except Exception:
                pass

        # 4. Employment / seasonal contract ended
        if re.search(
            r'(?:seasonal contract has ended|sumber pendapatan.*?telah berakhir|employment record has ended|employment has ended)',
            text,
            re.IGNORECASE,
        ):
            contract_ended = True
            m_rem = re.search(
                r'(?:remaining confirmed monthly salary is|sisa gaji bulanan.*?adalah)\s*([A-Z]{3})?\s*([\d,\.]+)',
                text,
                re.IGNORECASE,
            )
            if m_rem:
                amt_str = m_rem.group(2).replace(',', '')
                try:
                    salary_override = Decimal(amt_str)
                except Exception:
                    pass

        if re.search(
            r'(?:payout|earnings|income).*(?:still pending|not withdrawable|belum dapat ditarik)',
            text,
            re.IGNORECASE,
        ):
            pending_income = True

        # 5. Rent increase
        m_rent = re.search(r'increases monthly rent by (\d+)%', text, re.IGNORECASE)
        if m_rent:
            try:
                rent_increase_pct = Decimal(m_rent.group(1)) / Decimal(100)
            except Exception:
                pass

        # 6. Approved client invoices
        m_inv = re.search(
            r'(?:client approved an invoice payment of|klien menyetujui pembayaran faktur sebesar)\s*([A-Z]{3})?\s*([\d,\.]+)',
            text,
            re.IGNORECASE,
        )
        if m_inv:
            amt_str = m_inv.group(2).replace(',', '')
            curr = m_inv.group(1) or ""
            try:
                inv_amt = Decimal(amt_str)
                inv_d = date.fromisoformat(m_date.group(1)) if m_date else request_date
                confirmed_invoices_list.append((inv_d, inv_amt, curr))
            except Exception:
                pass

    return ExtractedMessageEvidence(
        user_id=user_id,
        salary_override=salary_override,
        salary_effective_date=salary_effective_date,
        rent_increase_pct=rent_increase_pct,
        one_time_arrears=tuple(arrears_list),
        contract_ended=contract_ended,
        pending_income=pending_income,
        confirmed_invoices=tuple(confirmed_invoices_list),
    )
