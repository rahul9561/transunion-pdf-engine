"""End-to-end tests: generate an actual PDF from the real fixture and
validate its content with pypdf.
"""

from __future__ import annotations

import pypdf

from transunion_pdf_engine import generate_report


def _extract_text(pdf_path: str) -> str:
    reader = pypdf.PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_generated_pdf_has_multiple_pages(raw_json, tmp_path):
    output_path = str(tmp_path / "report.pdf")
    generate_report(raw_json, output_path)
    reader = pypdf.PdfReader(output_path)
    assert len(reader.pages) >= 5


def test_generated_pdf_contains_customer_identity(raw_json, tmp_path):
    output_path = str(tmp_path / "report.pdf")
    generate_report(raw_json, output_path)
    text = _extract_text(output_path)

    assert "ANAND VARDHAN GOYAL S/O RAM GOPAL" in text
    assert "04/10/1995" in text
    assert "CAZPG3241C" in text
    assert "60022246625681" in text
    assert "837" in text
    assert "11446589015" in text


def test_generated_pdf_contains_every_account_number(raw_json, tmp_path):
    output_path = str(tmp_path / "report.pdf")
    generate_report(raw_json, output_path)
    text = _extract_text(output_path)

    account_numbers = [
        "356305002359", "356305002360", "356305002361", "356305002362",
        "356305002363", "356305002364", "356305002365", "356305002366",
        "LAPAT00048210367", "041900NC00002081",
    ]
    for account_number in account_numbers:
        assert account_number in text, f"missing account number {account_number}"


def test_generated_pdf_contains_every_enquiry(raw_json, tmp_path):
    output_path = str(tmp_path / "report.pdf")
    generate_report(raw_json, output_path)
    text = _extract_text(output_path)

    assert text.count("POONAFIN") >= 1
    assert text.count("AU SFB") >= 1
    assert text.count("ADITYA BIRLA") >= 2  # appears twice in the fixture


def test_generated_pdf_currency_values_render_without_broken_glyphs(raw_json, tmp_path):
    output_path = str(tmp_path / "report.pdf")
    generate_report(raw_json, output_path)
    text = _extract_text(output_path)

    # The Indian Rupee sign must round-trip through the embedded font, not
    # a WinAnsi-encoding fallback that would drop or mangle it.
    assert "40,00,000" in text
    assert "■" not in text  # missing-glyph replacement box


def test_masking_hides_full_account_numbers(raw_json, tmp_path):
    unmasked_path = str(tmp_path / "unmasked.pdf")
    masked_path = str(tmp_path / "masked.pdf")
    generate_report(raw_json, unmasked_path)
    generate_report(raw_json, masked_path, mask_account_numbers=True)

    unmasked_text = _extract_text(unmasked_path)
    masked_text = _extract_text(masked_path)

    assert "356305002359" in unmasked_text
    assert "356305002359" not in masked_text
    assert "2359" in masked_text  # last 4 digits still visible


def test_generate_report_survives_malformed_json(tmp_path):
    malformed_inputs = [
        {},
        None,
        [],
        "not even a dict",
        {"report_summary": None, "cibil_report": "broken"},
        {"cibil_report": {"GetCustomerAssetsResponse": {"GetCustomerAssetsSuccess": None}}},
    ]
    for i, bad_input in enumerate(malformed_inputs):
        output_path = str(tmp_path / f"malformed_{i}.pdf")
        result_path = generate_report(bad_input, output_path)
        reader = pypdf.PdfReader(result_path)
        assert len(reader.pages) >= 1


def test_no_hardcoded_sample_customer_in_engine_source():
    """The engine's own source (not test fixtures) must never hardcode PII
    from the sample data -- every value must flow through the parser.
    """
    import pathlib

    engine_root = pathlib.Path(__file__).resolve().parent.parent / "transunion_pdf_engine"
    forbidden = ["ANAND VARDHAN GOYAL", "CAZPG3241C", "9217010023", "ANANDVARDHAN001"]
    for py_file in engine_root.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in content, f"{needle!r} hardcoded in {py_file}"
