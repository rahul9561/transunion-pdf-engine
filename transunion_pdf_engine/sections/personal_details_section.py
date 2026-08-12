"""PERSONAL DETAILS section: Name / Date of Birth / Gender."""

from __future__ import annotations

from transunion_pdf_engine.helpers import card_grid_from_pairs, format_date, format_text, heading_with_card
from transunion_pdf_engine.models import CreditReport


def render(story: list, report: CreditReport, styles: dict) -> None:
    customer = report.customer
    pairs = [
        ("Name", format_text(customer.name)),
        ("Date Of Birth", format_date(customer.date_of_birth)),
        ("Gender", format_text(customer.gender)),
    ]
    card = card_grid_from_pairs(pairs, styles, n_cols=3)
    story.extend(heading_with_card("PERSONAL DETAILS", styles, card))
