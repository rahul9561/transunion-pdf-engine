"""ReportLab paragraph and table styles built from :mod:`transunion_pdf_engine.theme`.

Visual system (matches ``docs/sample_report.pdf.pdf``):
- Section headings are plain cyan uppercase text (no filled banner).
- Detail sections render as a light-gray outer "card" wrapping a white
  bordered grid, with thin dividers between columns and between repeated
  entries (multiple addresses, identifiers, phones, enquiries).
- Account "ACCOUNT DETAILS" fields render as full-width label-left /
  value-right rows inside a bordered box.
- Montserrat carries the brand-ish titles and section headings, Poppins
  carries the big numeric score, Roboto carries everything else.
"""

from __future__ import annotations

from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import TableStyle

from transunion_pdf_engine import theme


def get_paragraph_styles() -> dict[str, ParagraphStyle]:
    return {
        "page_title": ParagraphStyle(
            "page_title",
            fontName=theme.FONT_TITLE,
            fontSize=theme.SIZE_TITLE,
            textColor=theme.TEXT_DARK,
            leading=theme.SIZE_TITLE + 3,
        ),
        "header_meta_label": ParagraphStyle(
            "header_meta_label",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_BODY,
            textColor=theme.TEXT_MUTED,
            alignment=TA_RIGHT,
            leading=12,
        ),
        "header_meta_value": ParagraphStyle(
            "header_meta_value",
            fontName=theme.FONT_BOLD,
            fontSize=theme.SIZE_BODY,
            textColor=theme.TEXT_DARK,
            alignment=TA_RIGHT,
            leading=12,
        ),
        "greeting": ParagraphStyle(
            "greeting",
            fontName=theme.FONT_TITLE,
            fontSize=theme.SIZE_SUBTITLE,
            textColor=theme.TEXT_DARK,
            spaceAfter=3,
        ),
        "score_statement": ParagraphStyle(
            "score_statement",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_BODY + 0.5,
            textColor=theme.TEXT_DARK,
            spaceAfter=3,
        ),
        "score_caption": ParagraphStyle(
            "score_caption",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_SMALL,
            textColor=theme.TEXT_MUTED,
            leading=10,
        ),
        "score_number": ParagraphStyle(
            "score_number",
            fontName=theme.FONT_SCORE,
            fontSize=24,
            textColor=theme.TEXT_DARK,
            alignment=TA_CENTER,
            leading=26,
        ),
        "score_endpoint": ParagraphStyle(
            "score_endpoint",
            fontName=theme.FONT_REGULAR,
            fontSize=7.5,
            textColor=theme.TEXT_MUTED,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_BODY,
            textColor=theme.TEXT_DARK,
            leading=12,
            spaceAfter=4,
        ),
        "body_small": ParagraphStyle(
            "body_small",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_SMALL,
            textColor=theme.TEXT_MUTED,
            leading=10.5,
        ),
        "note_list": ParagraphStyle(
            "note_list",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_SMALL,
            textColor=theme.TEXT_DARK,
            leading=11,
            leftIndent=10,
            spaceAfter=2,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            fontName=theme.FONT_TITLE_BOLD,
            fontSize=theme.SIZE_SECTION_HEADING,
            textColor=theme.CIBIL_CYAN,
            leading=13,
        ),
        "subsection_heading": ParagraphStyle(
            "subsection_heading",
            fontName=theme.FONT_MEDIUM,
            fontSize=theme.SIZE_SUBSECTION_HEADING,
            textColor=theme.TEXT_MUTED,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "bullet_heading": ParagraphStyle(
            "bullet_heading",
            fontName=theme.FONT_BOLD,
            fontSize=theme.SIZE_SUBSECTION_HEADING,
            textColor=theme.TEXT_DARK,
        ),
        "field_label": ParagraphStyle(
            "field_label",
            fontName=theme.FONT_BOLD,
            fontSize=theme.SIZE_LABEL,
            textColor=theme.TEXT_DARK,
            leading=10.5,
        ),
        "field_value": ParagraphStyle(
            "field_value",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_VALUE,
            textColor=theme.TEXT_MUTED,
            leading=11.5,
            spaceBefore=1,
        ),
        "row_label": ParagraphStyle(
            "row_label",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_VALUE,
            textColor=theme.TEXT_DARK,
        ),
        "row_value": ParagraphStyle(
            "row_value",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_VALUE,
            textColor=theme.TEXT_DARK,
            alignment=TA_RIGHT,
        ),
        "legend": ParagraphStyle(
            "legend",
            fontName=theme.FONT_REGULAR,
            fontSize=7.3,
            textColor=theme.TEXT_DARK,
            leading=12,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_FOOTER,
            textColor=theme.TEXT_MUTED,
            alignment=TA_LEFT,
        ),
        "footer_center": ParagraphStyle(
            "footer_center",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_FOOTER,
            textColor=theme.TEXT_MUTED,
            alignment=TA_CENTER,
        ),
        "footer_right": ParagraphStyle(
            "footer_right",
            fontName=theme.FONT_REGULAR,
            fontSize=theme.SIZE_FOOTER,
            textColor=theme.TEXT_MUTED,
            alignment=TA_RIGHT,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontName=theme.FONT_REGULAR,
            fontSize=7.2,
            textColor=theme.TEXT_MUTED,
            leading=10,
            spaceAfter=5,
        ),
        "end_of_report": ParagraphStyle(
            "end_of_report",
            fontName=theme.FONT_BOLD,
            fontSize=10,
            textColor=theme.TEXT_DARK,
            alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontName=theme.FONT_MEDIUM,
            fontSize=7.3,
            textColor=theme.TEXT_DARK,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontName=theme.FONT_REGULAR,
            fontSize=7.5,
            textColor=theme.TEXT_DARK,
            alignment=TA_CENTER,
        ),
    }


def grid_table_style(
    n_cols: int,
    n_rows: int,
    *,
    background=None,
    box: bool = False,
    divider_cols: bool = True,
    divider_rows: bool = True,
    pad: float = 8,
) -> TableStyle:
    """Shared style for the label/value grids used across detail sections."""
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad - 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 1),
    ]
    if background is not None:
        cmds.append(("BACKGROUND", (0, 0), (-1, -1), background))
    if box:
        cmds.append(("BOX", (0, 0), (-1, -1), 0.6, theme.BORDER_GRAY))
    if divider_cols and n_cols > 1:
        cmds.append(("LINEAFTER", (0, 0), (n_cols - 2, -1), 0.5, theme.DIVIDER_GRAY))
    if divider_rows and n_rows > 1:
        cmds.append(("LINEBELOW", (0, 0), (-1, -2), 0.5, theme.DIVIDER_GRAY))
    return TableStyle(cmds)


def card_outer_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), theme.CARD_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]
    )


def field_rows_style(n_rows: int) -> TableStyle:
    cmds = [
        ("BOX", (0, 0), (-1, -1), 0.6, theme.BORDER_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 5.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if n_rows > 1:
        cmds.append(("LINEBELOW", (0, 0), (-1, -2), 0.4, theme.DIVIDER_GRAY))
    return TableStyle(cmds)


def legend_box_style() -> TableStyle:
    return TableStyle(
        [
            ("BOX", (0, 0), (-1, -1), 0.6, theme.BORDER_GRAY),
            ("LEFTPADDING", (0, 0), (-1, -1), 11),
            ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )


def payment_grid_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), theme.TABLE_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), theme.TEXT_DARK),
            ("FONTNAME", (0, 0), (-1, 0), theme.FONT_MEDIUM),
            ("FONTNAME", (0, 1), (-1, -1), theme.FONT_REGULAR),
            ("FONTSIZE", (0, 0), (-1, -1), 7.3),
            ("BOX", (0, 0), (-1, -1), 0.6, theme.BORDER_GRAY),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, theme.DIVIDER_GRAY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
