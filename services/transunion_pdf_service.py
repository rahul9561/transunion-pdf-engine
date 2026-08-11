"""Django-facing wrapper around :mod:`transunion_pdf_engine`.

This is the ONLY file in this project allowed to import Django. Everything
under ``transunion_pdf_engine/`` is framework-agnostic: it knows nothing about Django
settings, models, storage, or HTTP. This module exists purely to adapt
``transunion_pdf_engine.generate_report`` to a Django project's conventions (resolving
``MEDIA_ROOT``, accepting a model instance to derive a filename, etc.).

If Django is not installed or not configured, this module still imports
cleanly -- ``MEDIA_ROOT`` resolution degrades to a local ``output/``
directory so it stays usable in plain-Python contexts (e.g. a management
script or a test run without ``DJANGO_SETTINGS_MODULE`` set).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from transunion_pdf_engine import generate_report

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_SUBDIR = "cibil_reports"
DEFAULT_FALLBACK_DIR = "output"


class TransUnionPDFService:
    """Generates TransUnion CIBIL report PDFs for a Django application.

    Wraps :func:`transunion_pdf_engine.generate_report`, resolving the output path
    against Django's ``MEDIA_ROOT`` when available.
    """

    def __init__(self, output_subdir: str = DEFAULT_OUTPUT_SUBDIR):
        self.output_subdir = output_subdir

    def _media_root(self) -> str:
        try:
            from django.conf import settings

            media_root = getattr(settings, "MEDIA_ROOT", None)
            if media_root:
                return str(media_root)
        except Exception:
            logger.debug(
                "Django settings unavailable or unconfigured; "
                "falling back to local '%s/' directory",
                DEFAULT_FALLBACK_DIR,
            )
        return DEFAULT_FALLBACK_DIR

    def generate(
        self,
        raw_json: dict[str, Any],
        filename: str,
        *,
        mask_account_numbers: bool = False,
    ) -> str:
        """Generate a PDF for ``raw_json`` and return the file path."""
        output_dir = os.path.join(self._media_root(), self.output_subdir)
        output_path = os.path.join(output_dir, filename)
        logger.info("Generating TransUnion CIBIL PDF at %s", output_path)
        return generate_report(raw_json, output_path, mask_account_numbers=mask_account_numbers)

    def generate_for_customer(
        self,
        customer: Any,
        raw_json: dict[str, Any],
        *,
        mask_account_numbers: bool = False,
    ) -> str:
        """Convenience wrapper for a Django model instance (or any object
        exposing ``pk``/``id``), deriving a stable filename from it.
        """
        identifier = getattr(customer, "pk", None) or getattr(customer, "id", None) or "report"
        filename = f"transunion_{identifier}.pdf"
        return self.generate(raw_json, filename, mask_account_numbers=mask_account_numbers)


def generate_transunion_pdf(raw_json: dict[str, Any], output_path: str, **kwargs: Any) -> str:
    """Module-level convenience function for call sites that don't need the
    service class (e.g. a Celery task or a Django management command).
    """
    return generate_report(raw_json, output_path, **kwargs)
