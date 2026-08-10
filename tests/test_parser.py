"""Tests for pdf_engine.parser against the real TransUnion fixture and
against defensively-malformed input.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pdf_engine.models import CreditReport
from pdf_engine.parser import parse_credit_report


# ---------------------------------------------------------------------------
# Fixture-driven assertions (input/transunion_response.json)
# ---------------------------------------------------------------------------

def test_customer_name(parsed_report: CreditReport):
    assert parsed_report.customer.name == "ANAND VARDHAN GOYAL S/O RAM GOPAL"


def test_customer_dob(parsed_report: CreditReport):
    assert parsed_report.customer.date_of_birth == date(1995, 10, 4)


def test_customer_gender(parsed_report: CreditReport):
    assert parsed_report.customer.gender == "Male"


def test_customer_pan(parsed_report: CreditReport):
    assert parsed_report.customer.pan == "CAZPG3241C"


def test_customer_ckyc(parsed_report: CreditReport):
    assert parsed_report.customer.ckyc == "60022246625681"


def test_customer_email(parsed_report: CreditReport):
    assert parsed_report.customer.email == "ANANDVARDHAN001@GMAIL.COM"


def test_customer_addresses(parsed_report: CreditReport):
    addresses = parsed_report.customer.addresses
    assert len(addresses) == 4
    categories = [a.category for a in addresses]
    assert categories.count("Permanent Address") == 1
    assert categories.count("Residence Address") == 3
    assert addresses[0].postal_code == "148035"
    assert addresses[0].region_name == "Punjab"


def test_score(parsed_report: CreditReport):
    assert parsed_report.score.value == 837
    assert parsed_report.score.model_name == "CIBILTransUnionScore3"
    assert parsed_report.score.band == "Excellent"


def test_control_number(parsed_report: CreditReport):
    assert parsed_report.meta.control_number == "11446589015"


def test_account_counts(parsed_report: CreditReport):
    assert len(parsed_report.accounts) == 10
    assert len(parsed_report.open_accounts) == 1
    assert len(parsed_report.closed_accounts) == 9
    assert parsed_report.summary.total_accounts == 10
    assert parsed_report.summary.open_accounts == 1
    assert parsed_report.summary.closed_accounts == 9


def test_open_account_values(parsed_report: CreditReport):
    open_account = parsed_report.open_accounts[0]
    assert open_account.creditor_name == "PNB"
    assert open_account.account_number == "041900NC00002081"
    assert open_account.account_type_label == "Housing Loan"
    assert open_account.ownership_label == "Joint"
    assert open_account.sanctioned_amount == Decimal("4000000")
    assert open_account.current_balance == Decimal("2597451")
    assert open_account.emi_amount == Decimal("43945")
    assert open_account.interest_rate == Decimal("7.85")
    assert open_account.tenure_months == 140
    assert open_account.collateral_value == Decimal("9781105")
    assert open_account.actual_payment_amount == Decimal("43000")
    assert open_account.amount_overdue == Decimal("0")


def test_closed_account_sanctioned_amounts(parsed_report: CreditReport):
    sanctioned = sorted(
        int(a.sanctioned_amount) for a in parsed_report.closed_accounts if a.sanctioned_amount is not None
    )
    assert sanctioned == [90000, 99300, 110700, 111600, 196500, 200000, 540000, 1350000, 1500000]


def test_account_payment_history(parsed_report: CreditReport):
    open_account = parsed_report.open_accounts[0]
    assert len(open_account.payment_history.entries) == 36
    assert open_account.payment_history.start_date == date(2026, 7, 1)
    assert open_account.payment_history.end_date == date(2023, 8, 1)


def test_enquiries(parsed_report: CreditReport):
    enquiries = parsed_report.enquiries
    assert len(enquiries) == 4
    assert parsed_report.summary.total_enquiries == 4
    subscribers = [e.subscriber_name for e in enquiries]
    assert subscribers == [
        "POONAFIN",
        "ADITYA BIRLA F L LICENCECANCELLED",
        "AU SFB",
        "ADITYA BIRLA F L LICENCECANCELLED",
    ]
    amounts = [e.amount for e in enquiries]
    assert amounts == [Decimal("100"), Decimal("100"), Decimal("100000"), Decimal("100")]
    assert enquiries[0].inquiry_date == date(2025, 3, 18)
    assert all(e.purpose_label == "Other" for e in enquiries)


def test_no_warnings_on_clean_fixture(parsed_report: CreditReport):
    assert parsed_report.warnings == []


# ---------------------------------------------------------------------------
# Defensive parsing: malformed / missing / null / sentinel input
# ---------------------------------------------------------------------------

def test_non_dict_input_does_not_raise():
    report = parse_credit_report(["not", "a", "dict"])
    assert isinstance(report, CreditReport)
    assert report.customer.name == "Unknown"
    assert report.warnings


def test_none_input_does_not_raise():
    report = parse_credit_report(None)
    assert isinstance(report, CreditReport)
    assert report.accounts == []


def test_empty_dict_does_not_raise():
    report = parse_credit_report({})
    assert isinstance(report, CreditReport)
    assert report.customer.name == "Unknown"
    assert report.accounts == []
    assert report.enquiries == []


def test_missing_nested_keys_does_not_raise():
    report = parse_credit_report({"report_summary": {"name": "JANE DOE"}})
    assert report.customer.name == "JANE DOE"
    assert report.accounts == []


def test_malformed_tradeline_is_skipped_not_fatal():
    raw = {
        "cibil_report": {
            "GetCustomerAssetsResponse": {
                "GetCustomerAssetsSuccess": {
                    "Asset": {
                        "TrueLinkCreditReport": {
                            "TradeLinePartition": [
                                {"Tradeline": {"creditorName": "GOOD BANK", "GrantedTrade": {}}},
                                {"not": "a valid tradeline shape"},
                                "not even a dict",
                                None,
                            ]
                        }
                    }
                }
            }
        }
    }
    report = parse_credit_report(raw)
    assert len(report.accounts) == 1
    assert report.accounts[0].creditor_name == "GOOD BANK"


def test_sentinel_values_collapse_to_none():
    raw = {
        "cibil_report": {
            "GetCustomerAssetsResponse": {
                "GetCustomerAssetsSuccess": {
                    "Asset": {
                        "TrueLinkCreditReport": {
                            "TradeLinePartition": [
                                {
                                    "Tradeline": {
                                        "creditorName": "SENTINEL BANK",
                                        "highBalance": "-1",
                                        "currentBalance": "",
                                        "writtenOffAmtTotal": None,
                                        "GrantedTrade": {
                                            "interestRate": "-1.00",
                                            "EMIAmount": "-1",
                                        },
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
    report = parse_credit_report(raw)
    account = report.accounts[0]
    assert account.sanctioned_amount is None
    assert account.current_balance is None
    assert account.written_off_total is None
    assert account.interest_rate is None
    assert account.emi_amount is None


def test_single_item_lists_collapsed_to_object_are_normalized():
    """TransUnion's XML-derived feed sometimes serializes a 1-item repeated
    element as a bare object instead of a 1-item array (observed on
    MonthlyPayStatus in the real fixture). The parser must accept both
    shapes for every repeated field.
    """
    raw = {
        "cibil_report": {
            "GetCustomerAssetsResponse": {
                "GetCustomerAssetsSuccess": {
                    "Asset": {
                        "TrueLinkCreditReport": {
                            "Borrower": {
                                "BorrowerAddress": {
                                    "CreditAddress": {"StreetAddress": "1 MAIN ST", "PostalCode": "110001"},
                                    "addressOrder": "0",
                                },
                                "BorrowerTelephone": {
                                    "PhoneNumber": {"Number": "9999999999"},
                                    "PhoneType": {"symbol": "01"},
                                },
                                "IdentifierPartition": {
                                    "Identifier": {"ID": {"Id": "ABCDE1234F", "IdentifierName": "TaxId"}}
                                },
                            },
                            "TradeLinePartition": {
                                "Tradeline": {
                                    "creditorName": "SOLO BANK",
                                    "GrantedTrade": {
                                        "PayStatusHistory": {
                                            "MonthlyPayStatus": {"date": "2026-01-01+05:30", "status": "0"}
                                        }
                                    },
                                }
                            },
                            "InquiryPartition": {
                                "Inquiry": {"subscriberName": "SOLO LENDER", "inquiryType": "00", "amount": "50"}
                            },
                        }
                    }
                }
            }
        }
    }
    report = parse_credit_report(raw)
    assert len(report.customer.addresses) == 1
    assert len(report.customer.phones) == 1
    assert len(report.customer.identifiers) == 1
    assert len(report.accounts) == 1
    assert len(report.accounts[0].payment_history.entries) == 1
    assert len(report.enquiries) == 1
