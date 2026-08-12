"""Framework-agnostic safe-extraction and formatting helpers.

Used by :mod:`transunion_pdf_engine.parser` (to defensively pull values out of the raw
TransUnion JSON) and by :mod:`transunion_pdf_engine.sections` (to format normalized
model values for display). Nothing here ever raises on bad input -- callers
get ``None``/``"-"`` and a logged warning instead.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from transunion_pdf_engine.constants import SENTINEL_STRINGS

logger = logging.getLogger("transunion_pdf_engine")

DASH = "-"


def safe_get(obj: Any, *keys: str, default: Any = None) -> Any:
    """Walk ``obj[keys[0]][keys[1]]...`` safely, returning ``default`` on any miss."""
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current


def as_list(value: Any) -> list:
    """Normalize a JSON value that should be a list.

    TransUnion's feed is XML-derived: a repeated element with exactly one
    occurrence is sometimes serialized as a bare object instead of a
    single-item array (seen on ``MonthlyPayStatus`` in this fixture). This
    normalizes ``None`` -> ``[]``, a lone ``dict`` -> ``[dict]``, and passes
    an existing list through unchanged. Anything else is dropped to ``[]``.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def safe_symbol(obj: Any) -> str | None:
    """Extract the ``symbol`` from a TransUnion coded object, e.g. ``{"symbol": "02", ...}``."""
    if isinstance(obj, dict):
        symbol = obj.get("symbol")
        return clean_str(symbol)
    return None


def clean_str(value: Any) -> str | None:
    """Return a stripped non-empty string, else ``None``."""
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or None


def is_sentinel(raw: Any) -> bool:
    if raw is None:
        return True
    if isinstance(raw, str):
        return raw.strip() in SENTINEL_STRINGS
    if isinstance(raw, (int, float)):
        return raw == -1
    return False


def to_decimal(raw: Any, *, field_name: str = "") -> Decimal | None:
    """Parse a bureau numeric string, collapsing sentinels/blanks to ``None``."""
    if is_sentinel(raw):
        return None
    try:
        return Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, TypeError):
        logger.warning("Could not parse decimal for %s: %r", field_name or "field", raw)
        return None


def to_int(raw: Any, *, field_name: str = "") -> int | None:
    dec = to_decimal(raw, field_name=field_name)
    if dec is None:
        return None
    try:
        return int(dec)
    except (ValueError, OverflowError):
        logger.warning("Could not parse int for %s: %r", field_name or "field", raw)
        return None


def parse_iso_date(raw: Any, *, field_name: str = "") -> date | None:
    """Parse TransUnion ISO-ish dates: ``YYYY-MM-DD+05:30`` or full timestamps."""
    text = clean_str(raw)
    if not text:
        return None
    # Strip a trailing timezone offset like "+05:30" if present.
    candidate = text
    for sep in ("+", "Z"):
        if sep in candidate:
            candidate = candidate.split(sep, 1)[0]
            break
    candidate = candidate.strip()
    if not candidate:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    logger.warning("Could not parse ISO date for %s: %r", field_name or "field", raw)
    return None


def parse_ddmmyyyy(raw: Any, *, field_name: str = "") -> date | None:
    """Parse the pre-flattened ``report_summary`` style ``DD/MM/YYYY`` dates."""
    text = clean_str(raw)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        logger.warning("Could not parse DD/MM/YYYY date for %s: %r", field_name or "field", raw)
        return None


def parse_iso_datetime(raw: Any, *, field_name: str = "") -> datetime | None:
    """Like :func:`parse_iso_date` but keeps the time-of-day (used only for
    the report generation timestamp shown in the running page header).
    """
    text = clean_str(raw)
    if not text:
        return None
    candidate = text
    for sep in ("+", "Z"):
        if sep in candidate:
            candidate = candidate.split(sep, 1)[0]
            break
    candidate = candidate.strip()
    if not candidate:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(candidate, fmt)
        except ValueError:
            continue
    logger.warning("Could not parse ISO datetime for %s: %r", field_name or "field", raw)
    return None


def parse_any_date(raw: Any, *, field_name: str = "") -> date | None:
    """Try ISO first (raw bureau format), then ``DD/MM/YYYY`` (summary format)."""
    text = clean_str(raw)
    if not text:
        return None
    if "/" in text:
        return parse_ddmmyyyy(text, field_name=field_name)
    return parse_iso_date(text, field_name=field_name)


def format_date(value: date | None) -> str:
    if value is None:
        return DASH
    return value.strftime("%d/%m/%Y")


def indian_number_format(n: int) -> str:
    """Format an integer using Indian digit grouping (lakh/crore), no symbol."""
    negative = n < 0
    s = str(abs(int(n)))
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts: list[str] = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        formatted = ",".join(parts) + "," + last3
    return ("-" + formatted) if negative else formatted


def format_currency(amount: Decimal | int | None) -> str:
    if amount is None:
        return DASH
    try:
        from transunion_pdf_engine import theme

        return theme.CURRENCY_SYMBOL + indian_number_format(int(amount))
    except (ValueError, TypeError, OverflowError):
        return DASH


def format_percent(value: Decimal | int | None) -> str:
    if value is None:
        return DASH
    return f"{value}%"


def format_rate(value: Decimal | None) -> str:
    if value is None:
        return DASH
    return f"{value}%"


def format_text(value: str | None) -> str:
    return value if value else DASH


def format_int(value: int | None) -> str:
    if value is None:
        return DASH
    return str(value)


def mask_account_number(number: str | None, *, visible: int = 4) -> str:
    if not number:
        return DASH
    if len(number) <= visible:
        return number
    return ("X" * (len(number) - visible)) + number[-visible:]


# ---------------------------------------------------------------------------
# ReportLab flowable builders (shared layout primitives used by every section)
# ---------------------------------------------------------------------------

def section_heading(text: str, styles):
    """Plain cyan uppercase section label (no filled banner), matching the
    reference report's "PERSONAL DETAILS" / "ADDRESS DETAILS" style.
    """
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["section_heading"])


def heading_with_card(text: str, styles, card, *, space_after: int = 10) -> list:
    """A section heading glued to a small lead-in spacer, so the heading
    never gets orphaned alone at the bottom of a page.

    ``card`` is deliberately kept *outside* that KeepTogether and returned
    as a separate list item: cards built from a list of entries (addresses,
    phones, identifiers, enquiries) have one row per entry and can grow
    taller than a page, and KeepTogether forces its whole contents to fit
    in a single frame -- which raises LayoutError once they can't. Left as
    a bare flowable in the story, the card is free to split across pages
    via its own Table row-splitting.

    Returns a list of flowables -- callers must ``story.extend(...)`` the
    result rather than ``story.append(...)`` it.
    """
    from reportlab.platypus import KeepTogether, Spacer

    return [KeepTogether([section_heading(text, styles), Spacer(1, 4)]), card, Spacer(1, space_after)]


def _grid_rows(rows, styles):
    """rows: list[list[(label, value) | None]] -> Table cell matrix, each
    populated cell stacking a bold label Paragraph over a muted value
    Paragraph.
    """
    from reportlab.platypus import Paragraph

    data = []
    for row in rows:
        cells = []
        for item in row:
            if item is None:
                cells.append("")
            else:
                label, value = item
                cells.append(
                    [Paragraph(str(label), styles["field_label"]), Paragraph(str(value), styles["field_value"])]
                )
        data.append(cells)
    return data


def _chunk_pairs(pairs, n_cols):
    rows = [pairs[i : i + n_cols] for i in range(0, len(pairs), n_cols)]
    if rows:
        last = rows[-1]
        rows[-1] = last + [None] * (n_cols - len(last))
    return rows


def card_grid_from_pairs(pairs, styles, n_cols: int = 3, col_widths=None):
    """Light-gray card wrapping a white bordered grid of flat ``(label, value)``
    pairs, wrapped ``n_cols`` per row (used for Personal Details, Employment
    Details, and the plain account header row).
    """
    rows = _chunk_pairs(list(pairs), n_cols)
    return _card_grid(rows, styles, n_cols, col_widths)


def card_grid_from_entries(entries, styles, col_widths=None):
    """White bordered grid where each ``entry`` (a list of ``(label, value)``
    pairs, all the same length) is its own row, separated by a divider --
    used for multiple identifiers/addresses/phones/enquiries.

    Unlike ``card_grid_from_pairs``, this returns the grid ``Table`` directly
    instead of nesting it inside a 1-row/1-col outer "card" wrapper Table.
    The number of rows here is one per entry and is not bounded (a report
    can have dozens of enquiries, for example), and a 1-row outer wrapper
    can never split across pages -- ReportLab's Table.split() only splits
    at row boundaries, so a table with exactly one row either fits a frame
    whole or raises LayoutError. Returning a genuine multi-row Table lets
    it split by row like any other table once it's taller than a page.
    """
    from reportlab.platypus import Table

    from transunion_pdf_engine import theme
    from transunion_pdf_engine.styles import grid_table_style

    entries = list(entries)
    n_cols = len(entries[0]) if entries else 1
    table = Table(_grid_rows(entries, styles), colWidths=col_widths)
    table.setStyle(
        grid_table_style(
            n_cols, len(entries), background=theme.CARD_INNER_BG, box=True, divider_cols=True, divider_rows=True
        )
    )
    return table


def _card_grid(rows, styles, n_cols, col_widths):
    from reportlab.platypus import Table

    from transunion_pdf_engine import theme
    from transunion_pdf_engine.styles import card_outer_style, grid_table_style

    inner = Table(_grid_rows(rows, styles), colWidths=col_widths)
    inner.setStyle(
        grid_table_style(
            n_cols, len(rows), background=theme.CARD_INNER_BG, box=True, divider_cols=True, divider_rows=True
        )
    )
    outer = Table([[inner]], colWidths=[theme.CONTENT_WIDTH])
    outer.setStyle(card_outer_style())
    return outer


def plain_header_grid(pairs, styles, n_cols: int = 4, col_widths=None):
    """No background, no border -- just the label/value columns, used for the
    account "Member Name / Account Type / Account Number / Ownership" row.
    """
    from reportlab.platypus import Table

    from transunion_pdf_engine.styles import grid_table_style

    rows = _chunk_pairs(list(pairs), n_cols)
    table = Table(_grid_rows(rows, styles), colWidths=col_widths)
    table.setStyle(grid_table_style(n_cols, len(rows), background=None, box=False, divider_cols=False, divider_rows=False, pad=0))
    return table


def bordered_grid(pairs, styles, n_cols: int = 2, col_widths=None):
    """White bordered grid with no gray outer card, used for the account
    "Payment Start Date / Payment End Date" box.
    """
    from reportlab.platypus import Table

    from transunion_pdf_engine import theme
    from transunion_pdf_engine.styles import grid_table_style

    rows = _chunk_pairs(list(pairs), n_cols)
    table = Table(_grid_rows(rows, styles), colWidths=col_widths)
    table.setStyle(
        grid_table_style(
            n_cols, len(rows), background=theme.CARD_INNER_BG, box=True, divider_cols=True, divider_rows=True
        )
    )
    return table


def field_rows_table(pairs, styles, col_widths=None):
    """Full-width ``Label ................ Value`` rows inside a bordered
    box, one field per row, divided by thin rules -- used for "ACCOUNT
    DETAILS".
    """
    from reportlab.platypus import Paragraph, Table

    from transunion_pdf_engine import theme
    from transunion_pdf_engine.styles import field_rows_style

    if col_widths is None:
        col_widths = [theme.CONTENT_WIDTH * 0.62, theme.CONTENT_WIDTH * 0.38]

    data = [
        [Paragraph(str(label), styles["row_label"]), Paragraph(str(value), styles["row_value"])]
        for label, value in pairs
    ]
    table = Table(data, colWidths=col_widths)
    table.setStyle(field_rows_style(len(data)))
    return table


def legend_box(styles):
    """Bordered two-column box for the STD/SUB/DBT/LSS/SMA/XXX/### legend."""
    from reportlab.platypus import Paragraph, Table

    from transunion_pdf_engine import constants, theme
    from transunion_pdf_engine.styles import legend_box_style

    legend = constants.PAY_STATUS_LEGEND
    left_items = legend[0::2]
    right_items = legend[1::2]

    rows = []
    for i in range(max(len(left_items), len(right_items))):
        left = f"<b>{left_items[i][0]}</b>: {left_items[i][1]}" if i < len(left_items) else ""
        right = f"<b>{right_items[i][0]}</b>: {right_items[i][1]}" if i < len(right_items) else ""
        rows.append([Paragraph(left, styles["legend"]), Paragraph(right, styles["legend"])])

    table = Table(rows, colWidths=[theme.CONTENT_WIDTH * 0.5, theme.CONTENT_WIDTH * 0.5])
    table.setStyle(legend_box_style())
    return table


def bullet_heading(text: str, dot_color, styles):
    """A small colored dot followed by a bold uppercase label, used for the
    "OPEN ACCOUNTS" / "CLOSED ACCOUNTS" group headings (green / red dot).
    """
    from reportlab.graphics.shapes import Circle, Drawing
    from reportlab.platypus import Paragraph, Table

    from transunion_pdf_engine import theme

    dot = Drawing(12, 12)
    dot.add(Circle(5, 5, 4, fillColor=dot_color, strokeColor=None))
    label = Paragraph(text, styles["bullet_heading"])

    table = Table([[dot, label]], colWidths=[14, theme.CONTENT_WIDTH - 14])
    table.setStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    return table


def hr_rule(color=None, thickness: float = 0.6, space_before: float = 4, space_after: float = 4):
    """A thin full-width horizontal divider rule."""
    from reportlab.platypus import HRFlowable

    from transunion_pdf_engine import theme

    return HRFlowable(
        width="100%",
        thickness=thickness,
        color=color or theme.DIVIDER_GRAY,
        spaceBefore=space_before,
        spaceAfter=space_after,
        lineCap="butt",
    )


_LOGO_DRAWING_CACHE: dict = {}


def logo_drawing(target_width: float):
    """Load ``transunion_pdf_engine/assets/cibil-logo.svg`` as a ReportLab Drawing
    flowable, scaled to ``target_width`` with aspect ratio preserved. Returns
    ``None`` if the asset can't be loaded (caller should fall back to text).
    Cached by target width since the logo is a static local asset.
    """
    if target_width in _LOGO_DRAWING_CACHE:
        return _LOGO_DRAWING_CACHE[target_width]

    from transunion_pdf_engine import theme

    try:
        from svglib.svglib import svg2rlg

        drawing = svg2rlg(theme.LOGO_SVG_PATH)
        if not drawing or not drawing.width:
            _LOGO_DRAWING_CACHE[target_width] = None
            return None
        scale = target_width / drawing.width
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)
    except Exception:
        logger.warning("Could not load logo SVG from %s; falling back to text brand", theme.LOGO_SVG_PATH)
        drawing = None

    _LOGO_DRAWING_CACHE[target_width] = drawing
    return drawing
