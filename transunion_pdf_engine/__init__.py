"""Framework-agnostic TransUnion CIBIL PDF generation engine.

Public API::

    from transunion_pdf_engine import generate_report

    pdf_path = generate_report(raw_json, "output/report.pdf")

Lower-level entry points are exposed for callers that want to inspect or
customize the pipeline stages individually:

- ``parse_credit_report(raw_json) -> CreditReport``
- ``build_story(report) -> list[Flowable]``
- ``render_pdf(story, output_path, *, report=None) -> str``

This package has no dependency on Django or any web framework -- Django
integration lives entirely in ``services/transunion_pdf_service.py``, outside
this package.
"""

from transunion_pdf_engine.generator import build_story, generate_report, render_pdf
from transunion_pdf_engine.parser import parse_credit_report

__all__ = [
    "generate_report",
    "parse_credit_report",
    "build_story",
    "render_pdf",
]

__version__ = "1.0.0"
