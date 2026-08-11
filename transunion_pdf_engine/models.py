"""Normalized, framework-agnostic data model for a parsed CIBIL report.

Every value here has already been cleaned by :mod:`transunion_pdf_engine.parser`:
TransUnion sentinels (``-1``, ``-1.00``, empty string) have been collapsed to
``None``, dates are ``date`` objects, and coded fields carry both the raw
``*_code`` and the human ``*_label`` translated via :mod:`transunion_pdf_engine.constants`.

Section renderers should never need to touch raw JSON or code tables -- only
these dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class Identifier:
    id_type: str
    label: str
    id_number: str | None
    issue_date: date | None = None
    expiry_date: date | None = None


@dataclass
class Address:
    street_address: str
    region_code: str | None
    region_name: str
    postal_code: str | None
    category: str
    ownership_code: str | None
    ownership_label: str
    date_reported: date | None
    address_order: int

    @property
    def full_line(self) -> str:
        parts = [p for p in (self.street_address, self.region_name, self.postal_code) if p]
        return ", ".join(parts)


@dataclass
class Phone:
    type_code: str | None
    type_label: str
    number: str | None
    extension: str | None = None


@dataclass
class Employment:
    account_type_code: str | None
    account_type_label: str
    date_reported: date | None
    occupation: str | None
    income: str | None
    income_frequency_indicator: str | None
    net_gross_indicator: str | None
    employer_name: str | None = None


@dataclass
class MonthlyPayStatus:
    on_date: date
    status: str


@dataclass
class PaymentHistory:
    start_date: date | None
    end_date: date | None
    entries: list[MonthlyPayStatus] = field(default_factory=list)

    def by_year(self) -> dict[int, dict[int, str]]:
        """Return ``{year: {month: status}}`` for grid rendering."""
        grid: dict[int, dict[int, str]] = {}
        for entry in self.entries:
            grid.setdefault(entry.on_date.year, {})[entry.on_date.month] = entry.status
        return grid


@dataclass
class Account:
    creditor_name: str
    account_type_code: str | None
    account_type_label: str
    account_number: str | None
    ownership_code: str | None
    ownership_label: str
    is_open: bool
    credit_limit: Decimal | None
    sanctioned_amount: Decimal | None
    current_balance: Decimal | None
    cash_limit: Decimal | None
    amount_overdue: Decimal | None
    interest_rate: Decimal | None
    tenure_months: int | None
    emi_amount: Decimal | None
    payment_frequency_code: str | None
    payment_frequency_label: str
    actual_payment_amount: Decimal | None
    date_opened: date | None
    date_closed: date | None
    date_last_payment: date | None
    date_reported: date | None
    collateral_value: Decimal | None
    written_off_total: Decimal | None
    written_off_principal: Decimal | None
    settlement_amount: Decimal | None
    payment_history: PaymentHistory


@dataclass
class Enquiry:
    subscriber_name: str
    inquiry_date: date | None
    purpose_code: str | None
    purpose_label: str
    amount: Decimal | None
    control_number: str | None = None


@dataclass
class ScoreInfo:
    value: int | None
    model_name: str | None
    model_symbol: str | None
    band: str
    population_rank: int | None = None


@dataclass
class ReportMeta:
    control_number: str | None
    report_date: date | None
    generated_at: date | None = None
    generated_at_time: datetime | None = None


@dataclass
class Customer:
    name: str
    date_of_birth: date | None
    gender: str | None
    pan: str | None
    ckyc: str | None
    identifiers: list[Identifier] = field(default_factory=list)
    addresses: list[Address] = field(default_factory=list)
    phones: list[Phone] = field(default_factory=list)
    email: str | None = None
    employment: Employment | None = None


@dataclass
class SummaryTotals:
    total_accounts: int | None = None
    open_accounts: int | None = None
    closed_accounts: int | None = None
    total_sanctioned_amount: Decimal | None = None
    total_current_balance: Decimal | None = None
    total_amount_overdue: Decimal | None = None
    total_enquiries: int | None = None
    on_time_payment_history_pct: Decimal | None = None
    credit_card_utilization_pct: Decimal | None = None
    oldest_account_age_months: int | None = None
    credit_mix_pct: Decimal | None = None


@dataclass
class CreditReport:
    meta: ReportMeta
    customer: Customer
    score: ScoreInfo
    summary: SummaryTotals
    accounts: list[Account] = field(default_factory=list)
    enquiries: list[Enquiry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def open_accounts(self) -> list[Account]:
        return [a for a in self.accounts if a.is_open]

    @property
    def closed_accounts(self) -> list[Account]:
        return [a for a in self.accounts if not a.is_open]
