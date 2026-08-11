"""Builds the ReportLab flowable story and renders it to a PDF file.

This module (together with the rest of ``transunion_transunion_pdf_engine``) is framework-agnostic
-- it knows nothing about Django, HTTP, or any calling application. The only
inputs are a :class:`~transunion_transunion_pdf_engine.models.CreditReport` and an output path.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from reportlab.pdfgen import canvas as reportlab_canvas
from reportlab.platypus import PageBreak, SimpleDocTemplate

from transunion_pdf_engine import constants, theme
from transunion_pdf_engine.helpers import mask_account_number
from transunion_pdf_engine.models import CreditReport
from transunion_pdf_engine.parser import parse_credit_report
from transunion_pdf_engine.sections import (
    accounts_section,
    address_section,
    contact_section,
    disclaimer_section,
    employment_section,
    enquiries_section,
    identification_section,
    personal_details_section,
    score_section,
)
from transunion_pdf_engine.styles import get_paragraph_styles

logger = logging.getLogger("transunion_pdf_engine")


def build_story(report: CreditReport) -> list:
    """Assemble the ordered list of ReportLab flowables for ``report``.

    Section order mirrors the reference report layout:
    score/header -> personal -> identification -> address -> (page break)
    -> contact -> email -> employment -> accounts -> (page break)
    -> enquiries -> disclaimer.
    """
    styles = get_paragraph_styles()
    story: list = []

    score_section.render(story, report, styles)
    personal_details_section.render(story, report, styles)
    identification_section.render(story, report, styles)
    address_section.render(story, report, styles)

    story.append(PageBreak())
    contact_section.render(story, report, styles)
    employment_section.render(story, report, styles)
    accounts_section.render(story, report, styles)

    story.append(PageBreak())
    enquiries_section.render(story, report, styles)
    disclaimer_section.render(story, report, styles)

    return story


def render_pdf(story: list, output_path: str, *, report: CreditReport | None = None) -> str:
    """Render ``story`` to ``output_path`` and return that path."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=theme.PAGE_SIZE,
        leftMargin=theme.MARGIN_LEFT,
        rightMargin=theme.MARGIN_RIGHT,
        topMargin=theme.MARGIN_TOP,
        bottomMargin=theme.MARGIN_BOTTOM,
        title=constants.REPORT_TITLE,
    )

    canvas_maker = _build_page_decoration_canvas_class(report)
    doc.build(story, canvasmaker=canvas_maker)
    logger.info("Rendered PDF to %s", output_path)
    return output_path


def generate_report(
    raw_json: Any,
    output_path: str,
    *,
    mask_account_numbers: bool = False,
) -> str:
    """Public one-call API: raw TransUnion JSON -> rendered PDF file path."""
    report = parse_credit_report(raw_json)

    if mask_account_numbers:
        for account in report.accounts:
            account.account_number = mask_account_number(account.account_number)

    story = build_story(report)
    return render_pdf(story, output_path, report=report)


def _build_page_decoration_canvas_class(report: CreditReport | None):
    """Return a Canvas subclass that draws a running page header (generation
    timestamp + report title) and a running footer (generator credit + page
    X/Y), matching the reference report's split header/footer layout.

    ReportLab does not know the total page count until the whole document
    has been laid out, so this defers drawing to ``save()`` using the
    standard two-pass "numbered canvas" technique.
    """

    def timestamp_text() -> str:
        if report is None:
            return "-"
        if report.meta.generated_at_time:
            return report.meta.generated_at_time.strftime("%d/%m/%Y %H:%M")
        if report.meta.generated_at or report.meta.report_date:
            return (report.meta.generated_at or report.meta.report_date).strftime("%d/%m/%Y")
        return "-"

    def draw_header(c: reportlab_canvas.Canvas) -> None:
        c.saveState()
        c.setFont(theme.FONT_REGULAR, theme.SIZE_FOOTER)
        c.setFillColor(theme.TEXT_MUTED)

        y = theme.PAGE_SIZE[1] - theme.MARGIN_TOP + 14
        c.drawString(theme.MARGIN_LEFT, y, timestamp_text())
        c.drawCentredString(theme.PAGE_SIZE[0] / 2, y, constants.REPORT_TITLE)
        c.restoreState()

    def draw_footer(c: reportlab_canvas.Canvas, page_number: int, total_pages: int) -> None:
        c.saveState()
        c.setFont(theme.FONT_REGULAR, theme.SIZE_FOOTER)
        c.setFillColor(theme.TEXT_MUTED)

        y = theme.MARGIN_BOTTOM - 14
        c.drawString(theme.MARGIN_LEFT, y, constants.FOOTER_CREDIT_TEXT)
        c.drawRightString(theme.PAGE_SIZE[0] - theme.MARGIN_RIGHT, y, f"{page_number}/{total_pages}")
        c.restoreState()

    class _DecoratedCanvas(reportlab_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states: list[dict] = []

        def showPage(self) -> None:
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            total_pages = len(self._saved_page_states)
            for index, state in enumerate(self._saved_page_states, start=1):
                self.__dict__.update(state)
                draw_header(self)
                draw_footer(self, index, total_pages)
                reportlab_canvas.Canvas.showPage(self)
            reportlab_canvas.Canvas.save(self)

    return _DecoratedCanvas
