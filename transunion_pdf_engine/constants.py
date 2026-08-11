"""Static TransUnion CIBIL code tables and reference text.

The raw TransUnion feed sends enum-like objects with an empty ``description``
field (e.g. ``{"symbol": "02", "description": "", "rank": "100000", ...}``).
The bureau never populates that text in this feed, so every human-readable
label shown on the report is looked up here from the ``symbol`` using the
standard, publicly published TransUnion CIBIL code sets. Unknown codes never
raise -- callers get a safe fallback label instead.

These tables are TransUnion/CIBIL industry-standard code sets, not specific
to any other bureau or vendor.
"""

from __future__ import annotations

SENTINEL_STRINGS = {"-1", "-1.00", "", "0000-00-00"}
"""Raw string values TransUnion uses to mean "not applicable / not reported"."""

# ---------------------------------------------------------------------------
# Account / credit / inquiry type codes (2-digit)
# ---------------------------------------------------------------------------
ACCOUNT_TYPE_LABELS: dict[str, str] = {
    "00": "Other",
    "01": "Auto Loan (Personal)",
    "02": "Housing Loan",
    "03": "Property Loan",
    "04": "Loan Against Shares/Securities",
    "05": "Personal Loan",
    "06": "Consumer Loan",
    "07": "Gold Loan",
    "08": "Education Loan",
    "09": "Loan to Professional",
    "10": "Credit Card",
    "11": "Leasing",
    "12": "Overdraft",
    "13": "Two-Wheeler Loan",
    "14": "Non-Funded Credit Facility",
    "15": "Current Loan Against Bank Deposits (LABD)",
    "16": "Fleet Card",
    "17": "Commercial Vehicle Loan",
    "18": "Telco - Wireless",
    "19": "Telco - Broadband",
    "20": "Telco - Landline",
    "21": "GECL Secured",
    "22": "GECL Unsecured",
    "23": "Corporate Credit Card",
    "31": "Secured Credit Card",
    "32": "Used Car Loan",
    "33": "Construction Equipment Loan",
    "34": "Tractor Loan",
    "35": "Corporate Loan",
    "36": "Flexi Cash Credit",
    "37": "Loan on Credit Card",
    "38": "Business Loan - Priority Sector - Small Business",
    "39": "Business Loan - Priority Sector - Agriculture",
    "40": "Business Loan - Priority Sector - Others",
    "41": "Business Loan - General",
    "42": "Business Non-Funded Credit Facility - General",
    "43": "Business Non-Funded Credit Facility - Priority Sector - Small Business",
    "44": "Business Non-Funded Credit Facility - Priority Sector - Agriculture",
    "45": "Business Non-Funded Credit Facility - Priority Sector - Others",
    "51": "Business Loan Against Bank Deposits",
    "52": "Business Loan Against Shares/Securities",
    "53": "Business Loan Against Property",
    "54": "Business Fleet Card",
    "61": "Herbal/Kisan Credit Card",
    "71": "Prime Minister Jaan Dhan Yojana - Overdraft",
    "91": "Other",
}


def account_type_label(symbol: str | None) -> str:
    """Translate an ``AccountType``/``CreditType`` symbol to its label."""
    if not symbol:
        return "-"
    return ACCOUNT_TYPE_LABELS.get(symbol, f"Account Type ({symbol})")


# Enquiry purpose reuses the account type table; only a handful of purpose
# codes diverge from it, listed here as overrides.
INQUIRY_PURPOSE_OVERRIDES: dict[str, str] = {
    "00": "Other",
}


def inquiry_purpose_label(symbol: str | None) -> str:
    if not symbol:
        return "-"
    if symbol in INQUIRY_PURPOSE_OVERRIDES:
        return INQUIRY_PURPOSE_OVERRIDES[symbol]
    return account_type_label(symbol)


# ---------------------------------------------------------------------------
# Ownership / account designator codes
# ---------------------------------------------------------------------------
OWNERSHIP_LABELS: dict[str, str] = {
    "1": "Individual",
    "2": "Co-Applicant",
    "3": "Guarantor",
    "4": "Joint",
    "5": "Authorized User",
    "6": "Deceased",
    "7": "Business Partner",
    "8": "Sole Proprietor",
    "9": "Sponsor",
}


def ownership_label(symbol: str | None) -> str:
    if not symbol:
        return "-"
    return OWNERSHIP_LABELS.get(symbol, f"Ownership ({symbol})")


# ---------------------------------------------------------------------------
# Address ownership / residence codes
# ---------------------------------------------------------------------------
ADDRESS_OWNERSHIP_LABELS: dict[str, str] = {
    "01": "Owned",
    "02": "Rented/Leased",
    "03": "Parental",
    "04": "Company Provided",
    "05": "Others",
}


def address_ownership_label(symbol: str | None) -> str:
    if not symbol:
        return "-"
    return ADDRESS_OWNERSHIP_LABELS.get(symbol, f"Residence Code ({symbol})")


# ---------------------------------------------------------------------------
# Phone type codes
# ---------------------------------------------------------------------------
PHONE_TYPE_LABELS: dict[str, str] = {
    "01": "Mobile Phone",
    "02": "Residence Phone",
    "03": "Office Phone",
    "04": "Fax",
}


def phone_type_label(symbol: str | None) -> str:
    if not symbol:
        return "-"
    return PHONE_TYPE_LABELS.get(symbol, f"Telephone ({symbol})")


# ---------------------------------------------------------------------------
# Payment frequency codes
# ---------------------------------------------------------------------------
PAYMENT_FREQUENCY_LABELS: dict[str, str] = {
    "01": "Weekly",
    "02": "Fortnightly",
    "03": "Monthly",
    "04": "Quarterly",
    "05": "Half-Yearly",
    "06": "Yearly",
    "07": "Bullet",
}


def payment_frequency_label(symbol: str | None) -> str:
    if not symbol:
        return "-"
    return PAYMENT_FREQUENCY_LABELS.get(symbol, f"Frequency ({symbol})")


# ---------------------------------------------------------------------------
# Identifier name labels
# ---------------------------------------------------------------------------
IDENTIFIER_NAME_LABELS: dict[str, str] = {
    "TaxId": "Income Tax ID Number (PAN)",
    "CkycId": "CKYC",
    "SocialId": "Social/Bureau ID",
    "VoterIdCard": "Voter ID Card",
    "Passport": "Passport",
    "DriverLicense": "Driving License",
    "UniversalIdentificationNumber": "Aadhaar (UID)",
    "RationCardId": "Ration Card",
}

# Identifier types not shown on the standard report layout (internal bureau
# keys), matching the reference sample PDF which omits them.
IDENTIFIER_TYPES_HIDDEN = {"SocialId"}


def identifier_name_label(name: str | None) -> str:
    if not name:
        return "-"
    return IDENTIFIER_NAME_LABELS.get(name, name)


# ---------------------------------------------------------------------------
# Indian state / region codes (standard CIBIL 2-digit region table)
# ---------------------------------------------------------------------------
STATE_CODES: dict[str, str] = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttaranchal",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Orissa",
    "22": "Chattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman & Diu",
    "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra",
    "28": "Andhra Pradesh",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Pondicherry",
    "35": "Andaman & Nicobar",
    "36": "Telangana",
    "99": "APO Address",
}


def state_label(symbol: str | None) -> str:
    if not symbol:
        return ""
    return STATE_CODES.get(symbol, f"Region ({symbol})")


# ---------------------------------------------------------------------------
# Score bands (fallback when report_summary.score_band is absent)
# ---------------------------------------------------------------------------
SCORE_BANDS = (
    (579, "Poor"),
    (669, "Fair"),
    (739, "Good"),
    (799, "Very Good"),
    (900, "Excellent"),
)


def score_band_for(score: int | None) -> str:
    if score is None:
        return "-"
    for upper, label in SCORE_BANDS:
        if score <= upper:
            return label
    return "Excellent"


# ---------------------------------------------------------------------------
# Payment status legend (static text block, shown under every payment grid)
# ---------------------------------------------------------------------------
PAY_STATUS_LEGEND = (
    ("STD", "Standard"),
    ("SUB", "Substandard"),
    ("DBT", "Doubtful"),
    ("LSS", "Loss"),
    ("SMA", "Special Mention Account"),
    ("XXX", "Not Reported"),
    ("###", "Number of days past due"),
)

MONTH_ABBREVIATIONS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# ---------------------------------------------------------------------------
# Static regulatory / disclaimer text (not present in the JSON feed)
# ---------------------------------------------------------------------------
REPORT_TITLE = "CIBIL Report"
BUREAU_BRAND = "CIBIL"
BUREAU_TAGLINE = "Part of TransUnion"
PAGE_TITLE = "CIBIL Score & Report"

DISCLAIMER_TEXT = (
    "Disclaimer: All information contained in this credit report has been "
    "collated by TransUnion CIBIL Limited (TU CIBIL) based on information "
    "provided/submitted by its various members (“Members”), as part "
    "of periodic data submission, and Members are required to ensure "
    "accuracy, completeness and veracity of the information submitted. The "
    "credit report is generated using the proprietary search and match "
    "logic of TU CIBIL. In case of any discrepancy in personal or account "
    "information pertaining to loan accounts / credit cards, the concerned "
    "financial institution or credit card company may also be contacted for "
    "the required clarification."
)

COPYRIGHT_TEXT = (
    "COPYRIGHT {year} TRANSUNION CIBIL. ALL RIGHTS RESERVED. For more "
    "information, please visit our website at www.cibil.com"
)

SCORE_EXPLANATION_TEXT = (
    "This section reflects your CIBIL Score, which is widely used by loan "
    "providers to evaluate loan applications. Your score ranges between 300 "
    "and 900, and is calculated based on the information available in the "
    "“Accounts” and “Enquiry” section of your CIBIL "
    "Report. The closer your score is to 900, the more confidence the "
    "lender will have in your ability to repay the loan. Higher your score, "
    "the better chances of your application getting approved."
)

SCORE_NH_NOTE_TITLE = (
    "Please note in some cases you might be displayed a CIBIL Score of "
    "“NH” which indicates one of the following 3 things:"
)

SCORE_NH_NOTES = (
    "You have a credit card or loan account, but no credit activity in the "
    "last three years.",
    "Lenders may have made enquiries, but you do not have any credit "
    "activity.",
    "You only have add-on credit cards, and no credit exposure.",
)

ENQUIRY_NOTE = (
    "(e) Indicates the value provided by bank when you applied for a credit "
    "facility."
)

END_OF_REPORT_TEXT = "End of report"

FOOTER_CREDIT_TEXT = (
    "Generated by transunion_pdf_engine from TransUnion CIBIL data — not the original "
    "TransUnion CIBIL report"
)
