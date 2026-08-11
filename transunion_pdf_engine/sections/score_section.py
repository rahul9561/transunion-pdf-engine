"""Report header: CIBIL logo, page title + control number/date, greeting,
and the semicircular score gauge card.
"""

from __future__ import annotations

import math

from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table

from transunion_pdf_engine import constants, theme
from transunion_pdf_engine.helpers import format_date, format_int, logo_drawing
from transunion_pdf_engine.models import CreditReport


def _angle_for_score(score: int) -> float:
    score = max(300, min(900, score))
    return 180 - (score - 300) / 600 * 180


def _ring_segment(cx: float, cy: float, outer_r: float, inner_r: float, start_deg: float, end_deg: float, color):
    """A filled donut-ring segment built from raw polygon points.

    ReportLab's ``Wedge(..., annular=True)`` has a known bug where
    ``asPolygon()`` raises ``IndexError`` for some angle spans, so the ring
    is built by hand here instead: N points along the outer arc followed by
    N points back along the inner arc, forming one closed polygon.
    """
    from reportlab.graphics.shapes import Polygon

    span = end_deg - start_deg
    steps = max(2, int(24 * abs(span) / 180))
    points: list[float] = []
    for i in range(steps + 1):
        angle = math.radians(start_deg + span * i / steps)
        points.extend([cx + outer_r * math.cos(angle), cy + outer_r * math.sin(angle)])
    for i in range(steps + 1):
        angle = math.radians(end_deg - span * i / steps)
        points.extend([cx + inner_r * math.cos(angle), cy + inner_r * math.sin(angle)])
    return Polygon(points, fillColor=color, strokeColor=theme.WHITE, strokeWidth=0.8)


def _score_gauge(score_value: int | None, width: float, height: float = 96):
    from reportlab.graphics.shapes import Circle, Drawing, Line, String

    drawing = Drawing(width, height)
    cx = width / 2
    cy = height * 0.56
    radius = min(width / 2, height * 0.62) * 0.92
    inner_radius = radius * 0.6

    for lo, hi, color in theme.SCORE_GAUGE_BANDS:
        start_angle = _angle_for_score(hi)
        end_angle = _angle_for_score(lo)
        drawing.add(_ring_segment(cx, cy, radius, inner_radius, start_angle, end_angle, color))

    drawing.add(
        String(cx - radius, cy - 11, "300", fontName=theme.FONT_REGULAR, fontSize=7.5,
               fillColor=theme.TEXT_MUTED, textAnchor="start")
    )
    drawing.add(
        String(cx + radius, cy - 11, "900", fontName=theme.FONT_REGULAR, fontSize=7.5,
               fillColor=theme.TEXT_MUTED, textAnchor="end")
    )

    if score_value is not None:
        angle = math.radians(_angle_for_score(score_value))
        needle_len = radius * 0.82
        tip_x = cx + needle_len * math.cos(angle)
        tip_y = cy + needle_len * math.sin(angle)
        drawing.add(Line(cx, cy, tip_x, tip_y, strokeColor=theme.TEXT_DARK, strokeWidth=2.2))
        drawing.add(Circle(cx, cy, 4.2, fillColor=theme.TEXT_DARK, strokeColor=None))
        drawing.add(
            String(cx, max(cy - 34, 4), str(score_value), fontName=theme.FONT_SCORE, fontSize=21,
                   fillColor=theme.TEXT_DARK, textAnchor="middle")
        )
    return drawing


def _brand_block(styles: dict):
    logo = logo_drawing(3.6 * cm)
    if logo is not None:
        return logo
    # Defensive fallback if the SVG asset can't be loaded for any reason.
    return Table(
        [[Paragraph(constants.BUREAU_BRAND, styles["page_title"])],
         [Paragraph(constants.BUREAU_TAGLINE, styles["body_small"])]],
        colWidths=[3.6 * cm],
        style=[("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0),
               ("BOTTOMPADDING", (0, 0), (-1, -1), 0)],
    )


def _title_row(report: CreditReport, styles: dict) -> Table:
    control_number = report.meta.control_number or "-"
    report_date = format_date(report.meta.report_date)

    title = Paragraph(constants.PAGE_TITLE, styles["page_title"])
    meta = Table(
        [
            [Paragraph(f"Control Number : <b>{control_number}</b>", styles["header_meta_label"])],
            [Paragraph(f"Date : <b>{report_date}</b>", styles["header_meta_label"])],
        ],
        colWidths=[theme.CONTENT_WIDTH * 0.45],
        style=[
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ],
    )
    row = Table(
        [[title, meta]],
        colWidths=[theme.CONTENT_WIDTH * 0.55, theme.CONTENT_WIDTH * 0.45],
    )
    row.setStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    return row


def _score_card(report: CreditReport, styles: dict) -> Table:
    report_date = format_date(report.meta.report_date)
    gauge_width = theme.CONTENT_WIDTH * 0.30
    gauge = _score_gauge(report.score.value, gauge_width)

    text_block = [
        Paragraph(f"Hello, {report.customer.name}", styles["greeting"]),
        Paragraph(
            f"Your CIBIL Score is <b>{format_int(report.score.value)}</b> as of Date : {report_date}",
            styles["score_statement"],
        ),
        Paragraph(
            "CIBIL Score is a 3 digit numeric summary of your credit history &amp; "
            "ranges from 300 to 900.",
            styles["score_caption"],
        ),
    ]

    card = Table(
        [[gauge, text_block]],
        colWidths=[gauge_width, theme.CONTENT_WIDTH - gauge_width],
    )
    card.setStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), theme.CARD_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, -1), 10),
            ("RIGHTPADDING", (0, 0), (0, -1), 4),
            ("LEFTPADDING", (1, 0), (1, -1), 14),
            ("RIGHTPADDING", (1, 0), (1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]
    )
    return card


def render(story: list, report: CreditReport, styles: dict) -> None:
    story.append(_brand_block(styles))
    story.append(Spacer(1, 10))
    story.append(_title_row(report, styles))
    story.append(Spacer(1, 8))
    story.append(_score_card(report, styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph(constants.SCORE_EXPLANATION_TEXT, styles["body"]))
    story.append(Paragraph(constants.SCORE_NH_NOTE_TITLE, styles["body"]))
    for idx, note in enumerate(constants.SCORE_NH_NOTES, start=1):
        story.append(Paragraph(f"{idx}. {note}", styles["note_list"]))
    story.append(Spacer(1, 12))
