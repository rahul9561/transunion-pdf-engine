"""Visual theme constants: page geometry, colors, fonts, local asset paths.

Tuned to match ``docs/sample_report.pdf.pdf``: A4, generous margins, a cyan
CIBIL brand accent, light-gray section cards, and a clean corporate
typographic system built entirely from the fonts shipped in
``transunion_pdf_engine/assets/`` (Montserrat, Poppins, Roboto). No system fonts and no
network font downloads are used -- every font is embedded from a local TTF.
"""

from __future__ import annotations

import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
PAGE_SIZE = A4
MARGIN_LEFT = 1.5 * cm
MARGIN_RIGHT = 1.5 * cm
MARGIN_TOP = 1.6 * cm
MARGIN_BOTTOM = 1.7 * cm

CONTENT_WIDTH = PAGE_SIZE[0] - MARGIN_LEFT - MARGIN_RIGHT

# ---------------------------------------------------------------------------
# Local assets
# ---------------------------------------------------------------------------
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
LOGO_SVG_PATH = os.path.join(ASSETS_DIR, "cibil-logo.svg")

# ---------------------------------------------------------------------------
# Colors -- cyan brand accent matches the CIBIL wordmark in cibil-logo.svg
# ---------------------------------------------------------------------------
CIBIL_CYAN = colors.HexColor("#00A2D1")
CIBIL_GRAY = colors.HexColor("#6D6E71")  # matches the logo's "Part of TransUnion" tagline

NAVY = colors.HexColor("#16232E")
TEXT_DARK = colors.HexColor("#26282B")
TEXT_MUTED = colors.HexColor("#6B7280")
TEXT_FAINT = colors.HexColor("#8A9099")

CARD_BG = colors.HexColor("#F4F6F8")  # outer card wash
CARD_INNER_BG = colors.white  # nested white sub-card
TABLE_HEADER_BG = colors.HexColor("#EEF1F4")
BORDER_GRAY = colors.HexColor("#DFE3E8")
DIVIDER_GRAY = colors.HexColor("#E7EAED")
WHITE = colors.white

BULLET_OPEN = colors.HexColor("#2FA84F")
BULLET_CLOSED = colors.HexColor("#D64545")

SCORE_EXCELLENT = colors.HexColor("#1E8E3E")
SCORE_VERY_GOOD = colors.HexColor("#43A047")
SCORE_GOOD = colors.HexColor("#7CB342")
SCORE_FAIR = colors.HexColor("#F9A825")
SCORE_POOR = colors.HexColor("#D93025")

SCORE_BAND_COLORS = {
    "Excellent": SCORE_EXCELLENT,
    "Very Good": SCORE_VERY_GOOD,
    "Good": SCORE_GOOD,
    "Fair": SCORE_FAIR,
    "Poor": SCORE_POOR,
}

SCORE_GAUGE_BANDS = (
    (300, 579, SCORE_POOR),
    (580, 669, SCORE_FAIR),
    (670, 739, SCORE_GOOD),
    (740, 799, SCORE_VERY_GOOD),
    (800, 900, SCORE_EXCELLENT),
)


def color_for_band(band: str) -> colors.Color:
    return SCORE_BAND_COLORS.get(band, CIBIL_CYAN)


# ---------------------------------------------------------------------------
# Fonts -- embedded from transunion_pdf_engine/assets/, never system fonts, never
# downloaded. All three families ship the Indian Rupee glyph (U+20B9), so
# currency always renders with the real "₹" symbol.
# ---------------------------------------------------------------------------
CURRENCY_SYMBOL = "₹"

_MONTSERRAT_DIR = os.path.join(ASSETS_DIR, "Montserrat", "static")
_POPPINS_DIR = os.path.join(ASSETS_DIR, "Poppins")
_ROBOTO_DIR = os.path.join(ASSETS_DIR, "Roboto", "static")

# Registered font names (role-based). Populated by _register_fonts(); the
# literal strings below are the fallback if a TTF is somehow missing, so the
# engine still renders (with base-14 fonts) rather than crashing.
FONT_TITLE = "Helvetica-Bold"          # Montserrat SemiBold -- page/greeting titles
FONT_TITLE_BOLD = "Helvetica-Bold"     # Montserrat Bold -- section headings
FONT_SCORE = "Helvetica-Bold"          # Poppins Bold -- the big numeric score
FONT_REGULAR = "Helvetica"             # Roboto Regular -- body/values
FONT_MEDIUM = "Helvetica"              # Roboto Medium -- table headers, sub-labels
FONT_BOLD = "Helvetica-Bold"           # Roboto Bold -- field labels


def _register(name: str, path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        pdfmetrics.registerFont(TTFont(name, path))
        return True
    except Exception:
        return False


def _register_fonts() -> None:
    global FONT_TITLE, FONT_TITLE_BOLD, FONT_SCORE, FONT_REGULAR, FONT_MEDIUM, FONT_BOLD

    ok = True
    ok &= _register("Montserrat-SemiBold", os.path.join(_MONTSERRAT_DIR, "Montserrat-SemiBold.ttf"))
    ok &= _register("Montserrat-Bold", os.path.join(_MONTSERRAT_DIR, "Montserrat-Bold.ttf"))
    ok &= _register("Poppins-Bold", os.path.join(_POPPINS_DIR, "Poppins-Bold.ttf"))
    ok &= _register("Roboto-Regular", os.path.join(_ROBOTO_DIR, "Roboto-Regular.ttf"))
    ok &= _register("Roboto-Medium", os.path.join(_ROBOTO_DIR, "Roboto-Medium.ttf"))
    ok &= _register("Roboto-Bold", os.path.join(_ROBOTO_DIR, "Roboto-Bold.ttf"))

    if not ok:
        # A local asset is missing -- keep the base-14 fallback assigned
        # above rather than referencing an unregistered font name.
        return

    FONT_TITLE = "Montserrat-SemiBold"
    FONT_TITLE_BOLD = "Montserrat-Bold"
    FONT_SCORE = "Poppins-Bold"
    FONT_REGULAR = "Roboto-Regular"
    FONT_MEDIUM = "Roboto-Medium"
    FONT_BOLD = "Roboto-Bold"


_register_fonts()

SIZE_TITLE = 17
SIZE_SUBTITLE = 12.5
SIZE_SECTION_HEADING = 11
SIZE_SUBSECTION_HEADING = 9.5
SIZE_LABEL = 8.5
SIZE_VALUE = 9
SIZE_BODY = 8.5
SIZE_SMALL = 7.8
SIZE_FOOTER = 7.3
