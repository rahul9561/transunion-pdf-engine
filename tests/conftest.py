import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "input" / "transunion_response.json"


@pytest.fixture(scope="session")
def raw_json():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def parsed_report(raw_json):
    from pdf_engine.parser import parse_credit_report

    return parse_credit_report(raw_json)
