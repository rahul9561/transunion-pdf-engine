"""ADDRESS DETAILS section: one row per reported address."""

from __future__ import annotations

from transunion_pdf_engine import theme
from transunion_pdf_engine.helpers import card_grid_from_entries, format_date, format_text, heading_with_card
from transunion_pdf_engine.models import CreditReport


def render(story: list, report: CreditReport, styles: dict) -> None:
    addresses = report.customer.addresses
    if not addresses:
        return

    entries = [
        [
            ("Address", format_text(address.full_line)),
            ("Category", format_text(address.category)),
            ("Residence Code", format_text(address.ownership_label)),
            ("Date Reported", format_date(address.date_reported)),
        ]
        for address in addresses
    ]
    # The address column carries the longest text, so it gets extra width
    # relative to the other three columns.
    inner_width = theme.CONTENT_WIDTH - 18
    col_widths = [inner_width * 0.40, inner_width * 0.22, inner_width * 0.18, inner_width * 0.20]
    card = card_grid_from_entries(entries, styles, col_widths=col_widths)
    story.append(heading_with_card("ADDRESS DETAILS", styles, card))
