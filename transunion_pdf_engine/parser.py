"""Parses a raw TransUnion CIBIL JSON response into a normalized
:class:`~transunion_pdf_engine.models.CreditReport`.

Design rules (see ``docs/JSON_TO_PDF_MAPPING.md`` for the full field trace):

- Never raises on malformed input. Every extraction step is defensive; a
  broken sub-tree is logged as a warning and skipped, not fatal.
- Never hardcodes customer data -- every value flows from ``raw_json``.
- Primary source for header/summary fields is ``report_summary`` (a
  pre-flattened convenience block); primary source for repeated detail data
  (addresses, accounts, enquiries, identifiers, phones) is the raw bureau
  structure at ``cibil_report.GetCustomerAssetsResponse.GetCustomerAssetsSuccess
  .Asset.TrueLinkCreditReport``, since that is where the actual lists live.
- TransUnion sentinels (``-1``, ``-1.00``, ``""``, ``None``) collapse to
  ``None`` on the model so section renderers can uniformly show ``-``.
"""

from __future__ import annotations

import logging
from typing import Any

from transunion_pdf_engine.constants import (
    account_type_label,
    address_ownership_label,
    identifier_name_label,
    inquiry_purpose_label,
    ownership_label,
    payment_frequency_label,
    phone_type_label,
    score_band_for,
    state_label,
)
from transunion_pdf_engine.helpers import (
    as_list,
    clean_str,
    parse_any_date,
    parse_iso_datetime,
    safe_get,
    safe_symbol,
    to_decimal,
    to_int,
)
from transunion_pdf_engine.models import (
    Account,
    Address,
    CreditReport,
    Customer,
    Employment,
    Enquiry,
    Identifier,
    MonthlyPayStatus,
    Phone,
    PaymentHistory,
    ReportMeta,
    ScoreInfo,
    SummaryTotals,
)

logger = logging.getLogger("transunion_pdf_engine")


def parse_credit_report(raw_json: Any) -> CreditReport:
    """Entry point: raw TransUnion API JSON (dict) -> :class:`CreditReport`."""
    warnings: list[str] = []

    if not isinstance(raw_json, dict):
        logger.warning("raw_json is not a JSON object (got %s)", type(raw_json).__name__)
        warnings.append(f"Input was not a JSON object (got {type(raw_json).__name__})")
        return _empty_report(warnings)

    summary = raw_json.get("report_summary")
    if not isinstance(summary, dict):
        if summary is not None:
            warnings.append("report_summary was not an object; ignored")
        summary = {}

    customer_info = raw_json.get("customer_info")
    if not isinstance(customer_info, dict):
        customer_info = {}

    tlcr = safe_get(
        raw_json,
        "cibil_report", "GetCustomerAssetsResponse", "GetCustomerAssetsSuccess",
        "Asset", "TrueLinkCreditReport",
        default={},
    )
    if not isinstance(tlcr, dict):
        if tlcr:
            warnings.append("TrueLinkCreditReport missing or malformed")
        tlcr = {}

    credit_summary_data = safe_get(
        raw_json,
        "cibil_report", "GetCustomerAssetsResponse", "GetCustomerAssetsSuccess",
        "CreditSummaryData",
        default={},
    )
    if not isinstance(credit_summary_data, dict):
        credit_summary_data = {}

    asset = safe_get(
        raw_json,
        "cibil_report", "GetCustomerAssetsResponse", "GetCustomerAssetsSuccess",
        "Asset",
        default={},
    )
    if not isinstance(asset, dict):
        asset = {}

    borrower = tlcr.get("Borrower")
    if not isinstance(borrower, dict):
        if borrower is not None:
            warnings.append("Borrower missing or malformed")
        borrower = {}

    meta = _safe(_parse_meta, "report meta", warnings, summary, tlcr, asset, warnings,
                 default=ReportMeta(control_number=None, report_date=None))
    score = _safe(_parse_score, "score", warnings, summary, borrower, warnings,
                  default=ScoreInfo(value=None, model_name=None, model_symbol=None, band="-"))
    customer = _safe(_parse_customer, "customer", warnings, summary, customer_info, borrower, warnings,
                      default=Customer(name="Unknown", date_of_birth=None, gender=None, pan=None, ckyc=None))
    accounts = _safe(_parse_accounts, "accounts", warnings, tlcr, warnings, default=[])
    enquiries = _safe(_parse_enquiries, "enquiries", warnings, tlcr, warnings, default=[])
    totals = _safe(_parse_summary_totals, "summary totals", warnings,
                    summary, credit_summary_data, accounts, enquiries, default=SummaryTotals())

    return CreditReport(
        meta=meta,
        customer=customer,
        score=score,
        summary=totals,
        accounts=accounts,
        enquiries=enquiries,
        warnings=warnings,
    )


def _empty_report(warnings: list[str]) -> CreditReport:
    return CreditReport(
        meta=ReportMeta(control_number=None, report_date=None),
        customer=Customer(name="Unknown", date_of_birth=None, gender=None, pan=None, ckyc=None),
        score=ScoreInfo(value=None, model_name=None, model_symbol=None, band="-"),
        summary=SummaryTotals(),
        warnings=warnings,
    )


def _safe(func, label: str, warnings: list[str], *args, default):
    try:
        return func(*args)
    except Exception:
        logger.exception("Failed to parse %s", label)
        warnings.append(f"Failed to parse {label}")
        return default


# ---------------------------------------------------------------------------
# Report meta / score
# ---------------------------------------------------------------------------

def _parse_meta(summary: dict, tlcr: dict, asset: dict, warnings: list[str]) -> ReportMeta:
    control_number = clean_str(summary.get("control_number")) or clean_str(tlcr.get("ReferenceKey"))
    report_date = parse_any_date(summary.get("report_date"), field_name="report_date")
    generated_at = parse_any_date(asset.get("CreationDate"), field_name="Asset.CreationDate")
    generated_at_time = parse_iso_datetime(asset.get("CreationDate"), field_name="Asset.CreationDate")
    if report_date is None:
        report_date = generated_at
    return ReportMeta(
        control_number=control_number,
        report_date=report_date,
        generated_at=generated_at,
        generated_at_time=generated_at_time,
    )


def _parse_score(summary: dict, borrower: dict, warnings: list[str]) -> ScoreInfo:
    credit_score = safe_get(borrower, "CreditScore", default={}) or {}
    if not isinstance(credit_score, dict):
        credit_score = {}

    value = to_int(summary.get("credit_score"), field_name="credit_score")
    if value is None:
        value = to_int(credit_score.get("riskScore"), field_name="riskScore")

    model_name = clean_str(summary.get("score_name")) or clean_str(credit_score.get("scoreName"))
    model_symbol = safe_symbol(credit_score.get("CreditScoreModel"))
    band = clean_str(summary.get("score_band")) or score_band_for(value)
    population_rank = to_int(credit_score.get("populationRank"), field_name="populationRank")

    return ScoreInfo(
        value=value,
        model_name=model_name,
        model_symbol=model_symbol,
        band=band,
        population_rank=population_rank,
    )


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

def _parse_customer(summary: dict, customer_info: dict, borrower: dict, warnings: list[str]) -> Customer:
    name = clean_str(summary.get("name")) or clean_str(safe_get(borrower, "BorrowerName", "Name", "Forename"))
    if not name:
        forename = clean_str(customer_info.get("forename")) or ""
        surname = clean_str(customer_info.get("surname")) or ""
        name = (forename + " " + surname).strip() or "Unknown"

    dob = (
        parse_any_date(summary.get("date_of_birth"), field_name="date_of_birth")
        or parse_any_date(safe_get(borrower, "Birth", "date"), field_name="Birth.date")
        or parse_any_date(customer_info.get("date_of_birth"), field_name="customer_info.date_of_birth")
    )

    gender = clean_str(summary.get("gender")) or clean_str(borrower.get("Gender"))

    identifiers = _parse_identifiers(borrower, warnings)
    pan = (
        clean_str(summary.get("pan"))
        or next((i.id_number for i in identifiers if i.id_type == "TaxId"), None)
        or clean_str(customer_info.get("pan_id"))
    )
    ckyc = next((i.id_number for i in identifiers if i.id_type == "CkycId"), None)

    addresses = _parse_addresses(borrower, warnings)
    phones = _parse_phones(borrower, warnings)
    email = clean_str(safe_get(borrower, "EmailAddress", "Email"))
    employment = _parse_employment(borrower, warnings)

    return Customer(
        name=name,
        date_of_birth=dob,
        gender=gender,
        pan=pan,
        ckyc=ckyc,
        identifiers=identifiers,
        addresses=addresses,
        phones=phones,
        email=email,
        employment=employment,
    )


def _parse_identifiers(borrower: dict, warnings: list[str]) -> list[Identifier]:
    result: list[Identifier] = []
    items = as_list(safe_get(borrower, "IdentifierPartition", "Identifier"))
    for idx, item in enumerate(items):
        try:
            if not isinstance(item, dict):
                continue
            id_obj = item.get("ID")
            if not isinstance(id_obj, dict):
                continue
            id_type = clean_str(id_obj.get("IdentifierName")) or "Unknown"
            result.append(
                Identifier(
                    id_type=id_type,
                    label=identifier_name_label(id_type),
                    id_number=clean_str(id_obj.get("Id")),
                )
            )
        except Exception:
            logger.warning("Skipping malformed identifier at index %d", idx)
            warnings.append(f"Skipped malformed identifier at index {idx}")
    return result


def _parse_addresses(borrower: dict, warnings: list[str]) -> list[Address]:
    items = as_list(safe_get(borrower, "BorrowerAddress"))

    parsed: list[tuple[int, Address]] = []
    for idx, item in enumerate(items):
        try:
            if not isinstance(item, dict):
                continue
            credit_address = item.get("CreditAddress")
            if not isinstance(credit_address, dict):
                credit_address = {}
            order = to_int(item.get("addressOrder"), field_name="addressOrder")
            if order is None:
                order = idx
            region_code = clean_str(credit_address.get("Region"))
            ownership_code = safe_symbol(item.get("Ownership"))
            address = Address(
                street_address=clean_str(credit_address.get("StreetAddress")) or "",
                region_code=region_code,
                region_name=state_label(region_code),
                postal_code=clean_str(credit_address.get("PostalCode")),
                category="Residence Address",
                ownership_code=ownership_code,
                ownership_label=address_ownership_label(ownership_code),
                date_reported=parse_any_date(item.get("dateReported"), field_name="address.dateReported"),
                address_order=order,
            )
            parsed.append((order, address))
        except Exception:
            logger.warning("Skipping malformed address at index %d", idx)
            warnings.append(f"Skipped malformed address at index {idx}")

    if parsed:
        max_order = max(order for order, _ in parsed)
        for order, address in parsed:
            if order == max_order:
                address.category = "Permanent Address"

    return [address for _, address in parsed]


def _parse_phones(borrower: dict, warnings: list[str]) -> list[Phone]:
    items = as_list(safe_get(borrower, "BorrowerTelephone"))
    result: list[Phone] = []
    for idx, item in enumerate(items):
        try:
            if not isinstance(item, dict):
                continue
            number = clean_str(safe_get(item, "PhoneNumber", "Number"))
            type_code = safe_symbol(item.get("PhoneType"))
            result.append(Phone(type_code=type_code, type_label=phone_type_label(type_code), number=number))
        except Exception:
            logger.warning("Skipping malformed phone at index %d", idx)
            warnings.append(f"Skipped malformed phone at index {idx}")
    return result


def _parse_employment(borrower: dict, warnings: list[str]) -> Employment | None:
    employer = borrower.get("Employer")
    if not isinstance(employer, dict) or not employer:
        return None
    try:
        account_code = clean_str(employer.get("account"))
        occupation = clean_str(safe_get(employer, "OccupationCode", "description"))
        return Employment(
            account_type_code=account_code,
            account_type_label=account_type_label(account_code),
            date_reported=parse_any_date(employer.get("dateReported"), field_name="Employer.dateReported"),
            occupation=occupation,
            income=None,
            income_frequency_indicator=clean_str(employer.get("IncomeFreqIndicator")),
            net_gross_indicator=clean_str(employer.get("NetGrossIndicator")),
            employer_name=clean_str(employer.get("name")),
        )
    except Exception:
        logger.warning("Skipping malformed employment block")
        warnings.append("Skipped malformed employment block")
        return None


# ---------------------------------------------------------------------------
# Accounts (tradelines)
# ---------------------------------------------------------------------------

def _parse_accounts(tlcr: dict, warnings: list[str]) -> list[Account]:
    partition = as_list(tlcr.get("TradeLinePartition"))
    accounts: list[Account] = []
    for idx, item in enumerate(partition):
        try:
            account = _parse_one_account(item)
            if account is not None:
                accounts.append(account)
        except Exception:
            logger.warning("Skipping malformed tradeline at index %d", idx)
            warnings.append(f"Skipped malformed tradeline at index {idx}")
    return accounts


def _parse_one_account(item: Any) -> Account | None:
    if not isinstance(item, dict):
        return None
    tradeline = item.get("Tradeline")
    if not isinstance(tradeline, dict):
        return None
    granted_trade = tradeline.get("GrantedTrade")
    if not isinstance(granted_trade, dict):
        granted_trade = {}

    account_type_code = clean_str(item.get("accountTypeSymbol")) or safe_symbol(
        granted_trade.get("AccountType")
    )
    ownership_code = safe_symbol(tradeline.get("AccountDesignator"))
    payment_frequency_code = safe_symbol(granted_trade.get("PaymentFrequency"))
    date_closed = parse_any_date(tradeline.get("dateClosed"), field_name="dateClosed")

    return Account(
        creditor_name=clean_str(tradeline.get("creditorName")) or "Unknown",
        account_type_code=account_type_code,
        account_type_label=account_type_label(account_type_code),
        account_number=clean_str(tradeline.get("accountNumber")),
        ownership_code=ownership_code,
        ownership_label=ownership_label(ownership_code),
        is_open=date_closed is None,
        credit_limit=to_decimal(granted_trade.get("CreditLimit"), field_name="CreditLimit"),
        sanctioned_amount=to_decimal(tradeline.get("highBalance"), field_name="highBalance"),
        current_balance=to_decimal(tradeline.get("currentBalance"), field_name="currentBalance"),
        cash_limit=to_decimal(granted_trade.get("CashLimit"), field_name="CashLimit"),
        amount_overdue=to_decimal(granted_trade.get("amountPastDue"), field_name="amountPastDue"),
        interest_rate=to_decimal(granted_trade.get("interestRate"), field_name="interestRate"),
        tenure_months=to_int(granted_trade.get("termMonths"), field_name="termMonths"),
        emi_amount=to_decimal(granted_trade.get("EMIAmount"), field_name="EMIAmount"),
        payment_frequency_code=payment_frequency_code,
        payment_frequency_label=payment_frequency_label(payment_frequency_code),
        actual_payment_amount=to_decimal(granted_trade.get("actualPaymentAmount"), field_name="actualPaymentAmount"),
        date_opened=parse_any_date(tradeline.get("dateOpened"), field_name="dateOpened"),
        date_closed=date_closed,
        date_last_payment=parse_any_date(granted_trade.get("dateLastPayment"), field_name="dateLastPayment"),
        date_reported=parse_any_date(tradeline.get("dateReported"), field_name="dateReported"),
        collateral_value=to_decimal(granted_trade.get("collateral"), field_name="collateral"),
        written_off_total=to_decimal(tradeline.get("writtenOffAmtTotal"), field_name="writtenOffAmtTotal"),
        written_off_principal=to_decimal(tradeline.get("writtenOffPrincipal"), field_name="writtenOffPrincipal"),
        settlement_amount=to_decimal(tradeline.get("settlementAmount"), field_name="settlementAmount"),
        payment_history=_parse_payment_history(granted_trade.get("PayStatusHistory")),
    )


def _parse_payment_history(raw: Any) -> PaymentHistory:
    if not isinstance(raw, dict):
        return PaymentHistory(start_date=None, end_date=None, entries=[])

    entries: list[MonthlyPayStatus] = []
    for month_item in as_list(raw.get("MonthlyPayStatus")):
        if not isinstance(month_item, dict):
            continue
        on_date = parse_any_date(month_item.get("date"), field_name="MonthlyPayStatus.date")
        if on_date is None:
            continue
        status = clean_str(month_item.get("status")) or "XXX"
        entries.append(MonthlyPayStatus(on_date=on_date, status=status))

    return PaymentHistory(
        start_date=parse_any_date(raw.get("startDate"), field_name="PayStatusHistory.startDate"),
        end_date=parse_any_date(raw.get("endDate"), field_name="PayStatusHistory.endDate"),
        entries=entries,
    )


# ---------------------------------------------------------------------------
# Enquiries
# ---------------------------------------------------------------------------

def _parse_enquiries(tlcr: dict, warnings: list[str]) -> list[Enquiry]:
    partition = as_list(tlcr.get("InquiryPartition"))
    enquiries: list[Enquiry] = []
    for idx, item in enumerate(partition):
        try:
            enquiry = _parse_one_enquiry(item)
            if enquiry is not None:
                enquiries.append(enquiry)
        except Exception:
            logger.warning("Skipping malformed enquiry at index %d", idx)
            warnings.append(f"Skipped malformed enquiry at index {idx}")
    return enquiries


def _parse_one_enquiry(item: Any) -> Enquiry | None:
    if not isinstance(item, dict):
        return None
    inquiry = item.get("Inquiry")
    if not isinstance(inquiry, dict):
        return None

    purpose_code = clean_str(inquiry.get("inquiryType"))
    return Enquiry(
        subscriber_name=clean_str(inquiry.get("subscriberName")) or "Unknown",
        inquiry_date=parse_any_date(inquiry.get("inquiryDate"), field_name="inquiryDate"),
        purpose_code=purpose_code,
        purpose_label=inquiry_purpose_label(purpose_code),
        amount=to_decimal(inquiry.get("amount"), field_name="amount"),
        control_number=clean_str(inquiry.get("enqControlNum")),
    )


# ---------------------------------------------------------------------------
# Summary totals
# ---------------------------------------------------------------------------

def _parse_summary_totals(
    summary: dict,
    credit_summary_data: dict,
    accounts: list[Account],
    enquiries: list[Enquiry],
    warnings: list[str] | None = None,
) -> SummaryTotals:
    total_accounts = to_int(summary.get("total_accounts"), field_name="total_accounts")
    if total_accounts is None and accounts:
        total_accounts = len(accounts)

    open_accounts = to_int(summary.get("open_accounts"), field_name="open_accounts")
    if open_accounts is None and accounts:
        open_accounts = sum(1 for a in accounts if a.is_open)

    closed_accounts = to_int(summary.get("closed_accounts"), field_name="closed_accounts")
    if closed_accounts is None and accounts:
        closed_accounts = sum(1 for a in accounts if not a.is_open)

    total_enquiries = to_int(summary.get("total_enquiries"), field_name="total_enquiries")
    if total_enquiries is None and enquiries:
        total_enquiries = len(enquiries)

    on_time = to_decimal(summary.get("on_time_payment_history_pct"), field_name="on_time_payment_history_pct")
    if on_time is None:
        on_time = to_decimal(credit_summary_data.get("OnTimePaymentHistory"), field_name="OnTimePaymentHistory")

    cc_utilization = to_decimal(
        summary.get("credit_card_utilization_pct"), field_name="credit_card_utilization_pct"
    )
    if cc_utilization is None:
        cc_utilization = to_decimal(
            credit_summary_data.get("CreditCardUtilization"), field_name="CreditCardUtilization"
        )

    oldest_account_age = to_int(
        summary.get("oldest_account_age_months"), field_name="oldest_account_age_months"
    )
    if oldest_account_age is None:
        oldest_account_age = to_int(
            credit_summary_data.get("OldestCreditAccountPeriod"), field_name="OldestCreditAccountPeriod"
        )

    return SummaryTotals(
        total_accounts=total_accounts,
        open_accounts=open_accounts,
        closed_accounts=closed_accounts,
        total_sanctioned_amount=to_decimal(
            summary.get("total_sanctioned_amount"), field_name="total_sanctioned_amount"
        ),
        total_current_balance=to_decimal(
            summary.get("total_current_balance"), field_name="total_current_balance"
        ),
        total_amount_overdue=to_decimal(
            summary.get("total_amount_overdue"), field_name="total_amount_overdue"
        ),
        total_enquiries=total_enquiries,
        on_time_payment_history_pct=on_time,
        credit_card_utilization_pct=cc_utilization,
        oldest_account_age_months=oldest_account_age,
        credit_mix_pct=to_decimal(credit_summary_data.get("CreditMix"), field_name="CreditMix"),
    )
