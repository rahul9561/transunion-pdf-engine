"""End-of-report marker and the static regulatory disclaimer / copyright text.

None of this text is derived from the JSON feed -- it is static regulatory
copy owned by the engine (see ``transunion_pdf_engine.constants``), reproduced verbatim
from the reference report.
"""

from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer

from transunion_pdf_engine import constants
from transunion_pdf_engine.helpers import hr_rule
from transunion_pdf_engine.models import CreditReport


def render(story: list, report: CreditReport, styles: dict) -> None:
    story.append(Spacer(1, 10))
    story.append(hr_rule(space_before=0, space_after=8))
    story.append(Paragraph(constants.END_OF_REPORT_TEXT, styles["end_of_report"]))
    story.append(hr_rule(space_before=8, space_after=12))

    story.append(Paragraph(constants.DISCLAIMER_TEXT, styles["disclaimer"]))

    year = report.meta.report_date.year if report.meta.report_date else "-"
    story.append(Paragraph(constants.COPYRIGHT_TEXT.format(year=year), styles["disclaimer"]))
