"""ALL ACCOUNTS section: Open Accounts then Closed Accounts, each rendered as
a plain header row, an ACCOUNT DETAILS field list, and a PAYMENT STATUS block
with the monthly payment-history grid.
"""

from __future__ import annotations

from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table

from transunion_pdf_engine import constants, theme
from transunion_pdf_engine.helpers import (
    bordered_grid,
    bullet_heading,
    field_rows_table,
    format_currency,
    format_date,
    format_int,
    format_rate,
    format_text,
    hr_rule,
    legend_box,
    plain_header_grid,
    section_heading,
)
from transunion_pdf_engine.models import Account, CreditReport
from transunion_pdf_engine.styles import payment_grid_style


def render(story: list, report: CreditReport, styles: dict) -> None:
    if not report.accounts:
        return

    if report.open_accounts:
        story.append(_group_lead("ALL ACCOUNTS", "OPEN ACCOUNTS", theme.BULLET_OPEN, report.open_accounts[0], styles))
        story.extend(_account_details_block(report.open_accounts[0], styles))
        story.extend(_account_payment_block(report.open_accounts[0], styles))
        for account in report.open_accounts[1:]:
            story.append(hr_rule(space_before=6, space_after=10))
            story.append(_account_header(account, styles))
            story.extend(_account_details_block(account, styles))
            story.extend(_account_payment_block(account, styles))

    if report.closed_accounts:
        lead_title = None if report.open_accounts else "ALL ACCOUNTS"
        story.append(Spacer(1, 12))
        story.append(
            _group_lead(lead_title, "CLOSED ACCOUNTS", theme.BULLET_CLOSED, report.closed_accounts[0], styles)
        )
        story.extend(_account_details_block(report.closed_accounts[0], styles))
        story.extend(_account_payment_block(report.closed_accounts[0], styles))
        for account in report.closed_accounts[1:]:
            story.append(hr_rule(space_before=6, space_after=10))
            story.append(_account_header(account, styles))
            story.extend(_account_details_block(account, styles))
            story.extend(_account_payment_block(account, styles))


def _group_lead(section_title: str | None, bullet_text: str, dot_color, first_account: Account, styles: dict):
    """The section/group heading glued to the first account's header row, so
    a page break never leaves a heading stranded with no content under it.
    """
    elements = []
    if section_title:
        elements.append(section_heading(section_title, styles))
        elements.append(Spacer(1, 6))
    elements.append(bullet_heading(bullet_text, dot_color, styles))
    elements.append(hr_rule(space_before=2, space_after=8))
    elements.append(_account_header(first_account, styles))
    return KeepTogether(elements)


def _account_header(account: Account, styles: dict) -> Table:
    header_pairs = [
        ("Member Name", format_text(account.creditor_name)),
        ("Account Type", format_text(account.account_type_label)),
        ("Account Number", format_text(account.account_number)),
        ("Ownership", format_text(account.ownership_label)),
    ]
    return plain_header_grid(header_pairs, styles, n_cols=4)


def _account_details_block(account: Account, styles: dict) -> list:
    """ACCOUNT DETAILS heading + field table, kept together where possible."""
    return [
        Spacer(1, 8),
        KeepTogether(
            [
                Paragraph("ACCOUNT DETAILS", styles["subsection_heading"]),
                field_rows_table(_account_field_pairs(account), styles),
            ]
        ),
        Spacer(1, 8),
    ]


def _account_payment_block(account: Account, styles: dict) -> list:
    """PAYMENT STATUS heading + date range + history grid + legend, kept
    together as one cohesive unit tied to its account.
    """
    elements = [Paragraph("PAYMENT STATUS", styles["subsection_heading"])]
    elements.append(
        bordered_grid(
            [
                ("Payment Start Date", format_date(account.payment_history.start_date)),
                ("Payment End Date", format_date(account.payment_history.end_date)),
            ],
            styles,
            n_cols=2,
        )
    )
    elements.append(Spacer(1, 6))

    grid = _payment_history_table(account, styles)
    if grid is not None:
        elements.append(Paragraph("Payment History", styles["row_label"]))
        elements.append(Spacer(1, 3))
        elements.append(grid)
        elements.append(Spacer(1, 6))

    elements.append(legend_box(styles))
    return [KeepTogether(elements)]


def _account_field_pairs(account: Account) -> list[tuple[str, str]]:
    return [
        ("Credit Limit", format_currency(account.credit_limit)),
        ("Sanctioned Amount", format_currency(account.sanctioned_amount)),
        ("Current Balance", format_currency(account.current_balance)),
        ("Cash Limit", format_currency(account.cash_limit)),
        ("Amount Overdue", format_currency(account.amount_overdue)),
        ("Rate of Interest", format_rate(account.interest_rate)),
        ("Repayment Tenure", format_int(account.tenure_months)),
        ("EMI Amount", format_currency(account.emi_amount)),
        ("Payment Frequency", format_text(account.payment_frequency_label)),
        ("Actual Payment Amount", format_currency(account.actual_payment_amount)),
        ("Date Opened / Disbursed", format_date(account.date_opened)),
        ("Date Closed", format_date(account.date_closed)),
        ("Date of Last Payment", format_date(account.date_last_payment)),
        ("Date Reported And Certified", format_date(account.date_reported)),
        ("Value of Collateral", format_currency(account.collateral_value)),
        ("Written-off Amount (Total)", format_currency(account.written_off_total)),
        ("Written-off Amount (Principal)", format_currency(account.written_off_principal)),
        ("Settlement Amount", format_currency(account.settlement_amount)),
    ]


def _payment_history_table(account: Account, styles: dict):
    grid = account.payment_history.by_year()
    if not grid:
        return None

    years = sorted(grid.keys(), reverse=True)
    month_order = list(range(12, 0, -1))  # Dec .. Jan
    header = ["Year"] + [constants.MONTH_ABBREVIATIONS[m - 1] for m in month_order]
    rows = [header]
    for year in years:
        row = [str(year)] + [grid[year].get(m, "") for m in month_order]
        rows.append(row)

    year_col = 1.4 * cm
    month_col = (theme.CONTENT_WIDTH - year_col) / 12
    table = Table(rows, colWidths=[year_col] + [month_col] * 12)
    table.setStyle(payment_grid_style())
    return table
