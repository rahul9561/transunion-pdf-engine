"""CONTACT DETAILS and EMAIL DETAILS sections."""

from __future__ import annotations

from transunion_pdf_engine.helpers import card_grid_from_entries, card_grid_from_pairs, format_text, heading_with_card
from transunion_pdf_engine.models import CreditReport


def render(story: list, report: CreditReport, styles: dict) -> None:
    phones = report.customer.phones
    if phones:
        entries = [
            [
                ("Telephone Number Type", format_text(phone.type_label)),
                ("Telephone Number", format_text(phone.number)),
                ("Telephone Extension", format_text(phone.extension)),
            ]
            for phone in phones
        ]
        card = card_grid_from_entries(entries, styles)
        story.extend(heading_with_card("CONTACT DETAILS", styles, card))

    if report.customer.email:
        card = card_grid_from_pairs([("Email ID", format_text(report.customer.email))], styles, n_cols=1)
        story.extend(heading_with_card("EMAIL DETAILS", styles, card))
