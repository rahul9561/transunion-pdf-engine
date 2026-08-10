"""ENQUIRY DETAILS section."""

from __future__ import annotations

from reportlab.platypus import KeepTogether, Paragraph, Spacer

from pdf_engine import constants
from pdf_engine.helpers import card_grid_from_entries, format_currency, format_date, format_text, section_heading
from pdf_engine.models import CreditReport


def render(story: list, report: CreditReport, styles: dict) -> None:
    if not report.enquiries:
        return

    entries = [
        [
            ("Member Name", format_text(enquiry.subscriber_name)),
            ("Date Of Enquiry", format_date(enquiry.inquiry_date)),
            ("Enquiry Purpose", format_text(enquiry.purpose_label)),
            ("Enquiry Amount", format_currency(enquiry.amount)),
        ]
        for enquiry in report.enquiries
    ]
    card = card_grid_from_entries(entries, styles)
    story.append(
        KeepTogether(
            [
                section_heading("ENQUIRY DETAILS", styles),
                Spacer(1, 3),
                Paragraph(constants.ENQUIRY_NOTE, styles["body_small"]),
                Spacer(1, 5),
                card,
                Spacer(1, 10),
            ]
        )
    )
