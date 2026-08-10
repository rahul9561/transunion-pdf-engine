"""EMPLOYMENT DETAILS section."""

from __future__ import annotations

from pdf_engine.helpers import card_grid_from_pairs, format_date, format_text, heading_with_card
from pdf_engine.models import CreditReport


def render(story: list, report: CreditReport, styles: dict) -> None:
    employment = report.customer.employment
    if employment is None:
        return

    pairs = [
        ("Account Type", format_text(employment.account_type_label)),
        ("Date Reported", format_date(employment.date_reported)),
        ("Occupation", format_text(employment.occupation)),
        ("Income", format_text(employment.income)),
        ("Monthly / Annual Income Indicator", format_text(employment.income_frequency_indicator)),
        ("Net / Gross Income Indicator", format_text(employment.net_gross_indicator)),
    ]
    card = card_grid_from_pairs(pairs, styles, n_cols=4)
    story.append(heading_with_card("EMPLOYMENT DETAILS", styles, card))
