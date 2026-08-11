"""IDENTIFICATION DETAILS section: one row per identifier (PAN, CKYC, ...)."""

from __future__ import annotations

from transunion_pdf_engine.constants import IDENTIFIER_TYPES_HIDDEN
from transunion_pdf_engine.helpers import card_grid_from_entries, format_date, format_text, heading_with_card
from transunion_pdf_engine.models import CreditReport


def render(story: list, report: CreditReport, styles: dict) -> None:
    identifiers = [i for i in report.customer.identifiers if i.id_type not in IDENTIFIER_TYPES_HIDDEN]
    if not identifiers:
        return

    entries = [
        [
            ("Identification Type", format_text(identifier.label)),
            ("ID Number", format_text(identifier.id_number)),
            ("Issue Date", format_date(identifier.issue_date)),
            ("Expiry Date", format_date(identifier.expiry_date)),
        ]
        for identifier in identifiers
    ]
    card = card_grid_from_entries(entries, styles)
    story.append(heading_with_card("IDENTIFICATION DETAILS", styles, card))
