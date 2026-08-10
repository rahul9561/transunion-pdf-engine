"""Tests for pdf_engine.generator: story assembly and PDF rendering."""

from __future__ import annotations

import os

from reportlab.platypus import PageBreak

from pdf_engine.generator import build_story, generate_report, render_pdf
from pdf_engine.models import CreditReport
from pdf_engine.parser import parse_credit_report


def test_build_story_returns_nonempty_flowable_list(parsed_report: CreditReport):
    story = build_story(parsed_report)
    assert isinstance(story, list)
    assert len(story) > 10


def test_build_story_has_page_breaks(parsed_report: CreditReport):
    story = build_story(parsed_report)
    assert any(isinstance(flowable, PageBreak) for flowable in story)


def test_build_story_handles_empty_report():
    empty_report = parse_credit_report({})
    story = build_story(empty_report)
    assert isinstance(story, list)
    # Score/personal-details header content should still render even with
    # no accounts/enquiries.
    assert len(story) > 0


def test_render_pdf_writes_file(parsed_report: CreditReport, tmp_path):
    story = build_story(parsed_report)
    output_path = str(tmp_path / "rendered.pdf")
    result_path = render_pdf(story, output_path, report=parsed_report)
    assert result_path == output_path
    assert os.path.isfile(output_path)
    assert os.path.getsize(output_path) > 1000


def test_render_pdf_creates_missing_output_directory(parsed_report: CreditReport, tmp_path):
    story = build_story(parsed_report)
    output_path = str(tmp_path / "nested" / "dir" / "rendered.pdf")
    render_pdf(story, output_path, report=parsed_report)
    assert os.path.isfile(output_path)


def test_generate_report_end_to_end(raw_json, tmp_path):
    output_path = str(tmp_path / "report.pdf")
    result_path = generate_report(raw_json, output_path)
    assert result_path == output_path
    assert os.path.isfile(output_path)


def test_generate_report_mask_account_numbers_does_not_mutate_raw_json(raw_json, tmp_path):
    import copy

    original = copy.deepcopy(raw_json)
    generate_report(raw_json, str(tmp_path / "masked.pdf"), mask_account_numbers=True)
    assert raw_json == original
