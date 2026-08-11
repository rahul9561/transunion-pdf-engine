"""Report section renderers.

Every module exposes a single ``render(story, report)`` function that
appends ReportLab flowables to ``story`` (a list) for the given
:class:`transunion_pdf_engine.models.CreditReport`. :func:`transunion_pdf_engine.generator.build_story`
calls them in the exact order required to reproduce the reference report
layout.
"""
