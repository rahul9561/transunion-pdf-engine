# TransUnion CIBIL JSON → PDF Field Mapping

Source fixture: `input/transunion_response.json`
Reference layout: `docs/sample_report.pdf.pdf` (11 pages; the generated
report runs ~14 pages for this fixture -- section order, headings, cards,
and every field match the reference, but page count is not forced to match
since related content (an account's header/details/payment-status) is kept
together rather than compressed to hit a fixed page count)

This document traces every field required by the PDF to its **exact JSON path**
in the raw TransUnion response. Paths are written as Python-style subscripts
from the JSON root.

## 0. Root shape

```
root
├── client_key                       # integration metadata — NOT rendered
├── web_token_url                    # integration metadata — NOT rendered
├── customer_info                    # convenience echo of request identity — used only as a fallback
├── report_summary                   # pre-flattened summary block — primary source for header/summary fields
├── diagnosis                        # API call status — NOT rendered
├── steps                            # API orchestration trace — NOT rendered
└── cibil_report
    └── GetCustomerAssetsResponse
        └── GetCustomerAssetsSuccess
            ├── CreditSummaryData     # secondary source for the 5 summary ratios
            └── Asset
                └── TrueLinkCreditReport   # PRIMARY source for all detail sections
```

`client_key`, `web_token_url`, `diagnosis`, `steps` are transport/orchestration
metadata belonging to the calling application, not the bureau report. They are
intentionally never rendered and never parsed into the report model.

Shorthand used below:
- `TLCR` = `root["cibil_report"]["GetCustomerAssetsResponse"]["GetCustomerAssetsSuccess"]["Asset"]["TrueLinkCreditReport"]`
- `BORROWER` = `TLCR["Borrower"]`
- `SUMMARY` = `root["report_summary"]`

Every TransUnion enum-like object (`{"symbol": "...", "description": "", "rank": "100000", "abbreviation": ""}`)
arrives with an **empty `description`** in this feed — the bureau does not
populate the text form. The PDF must therefore translate `symbol` values using
static TransUnion/CIBIL code tables (`pdf_engine/constants.py`), never the
JSON's own (blank) description field. This was confirmed by cross-referencing
every symbol in the fixture against the text shown in `docs/sample_report.pdf.pdf`
(see "Code tables" section at the end).

---

## 1. Report metadata / header (sample PDF page 1)

| PDF field | JSON path | Notes |
|---|---|---|
| CIBIL Score & Report Control Number | `SUMMARY["control_number"]` (= `TLCR["ReferenceKey"]`) | Both paths hold the same value; `report_summary` used as primary, `ReferenceKey` as cross-check |
| Report Date | `SUMMARY["report_date"]` | Already `DD/MM/YYYY` |
| "Hello, {name}" | `SUMMARY["name"]` (= `BORROWER["BorrowerName"]["Name"]["Forename"]`) | Full string incl. "S/O ..." suffix, used verbatim |
| CIBIL Score value | `SUMMARY["credit_score"]` (= `BORROWER["CreditScore"]["riskScore"]`, string) | int in summary, string in raw |
| Score model / name | `SUMMARY["score_name"]` (= `BORROWER["CreditScore"]["scoreName"]`) | e.g. `CIBILTransUnionScore3` |
| Score model symbol | `BORROWER["CreditScore"]["CreditScoreModel"]["symbol"]` | e.g. `CIBILTUSC3` — informational only |
| Score band | `SUMMARY["score_band"]` | e.g. `Excellent`; if absent, derive with `constants.score_band_for(score)` |
| Population rank | `BORROWER["CreditScore"]["populationRank"]` | not shown in sample PDF; parsed but unused by default layout |
| Running page-header timestamp (top of every page) | `Asset["CreationDate"]` (ISO datetime, e.g. `2026-08-10T13:05:25.091+05:30`) | Parsed into `ReportMeta.generated_at_time` (a full `datetime`, unlike `generated_at`/`report_date` which are date-only) so the header can show `DD/MM/YYYY HH:MM`, matching the reference report's top-left timestamp |

## 2. Personal details (page 1)

| PDF field | JSON path |
|---|---|
| Name | `SUMMARY["name"]` → fallback `BORROWER["BorrowerName"]["Name"]["Forename"]` → fallback `customer_info.forename + " " + customer_info.surname` |
| Date of Birth | `SUMMARY["date_of_birth"]` (`DD/MM/YYYY`) → fallback `BORROWER["Birth"]["date"]` (ISO `YYYY-MM-DD+TZ`) → fallback `customer_info["date_of_birth"]` (ISO) |
| Gender | `SUMMARY["gender"]` → fallback `BORROWER["Gender"]` |

## 3. Identification details (page 1)

Source list: `BORROWER["IdentifierPartition"]["Identifier"]` (list of `{"ID": {"Id", "IdentifierName", "SerialNumber"}, ...}`).

| PDF field | JSON path | Notes |
|---|---|---|
| Identification Type | `Identifier[i]["ID"]["IdentifierName"]` translated via `constants.IDENTIFIER_NAME_LABELS` | `TaxId` → "Income Tax ID Number (PAN)", `CkycId` → "CKYC", `SocialId` → not shown in sample PDF (internal bureau key) — parser keeps it, PDF section skips `SocialId` rows by default to match the reference layout |
| ID Number | `Identifier[i]["ID"]["Id"]` | e.g. `CAZPG3241C`, `60022246625681` |
| Issue Date / Expiry Date | not present anywhere in the feed | rendered as `-` (sample PDF also shows `-` for both, confirming the bureau never supplies these) |
| PAN (top-level convenience) | `SUMMARY["pan"]` (= `BORROWER["IdentifierPartition"]["Identifier"][?IdentifierName=="TaxId"]["ID"]["Id"]` = `customer_info["pan_id"]`) | all three agree: `CAZPG3241C` |
| CKYC (top-level convenience) | `Identifier[?IdentifierName=="CkycId"]["ID"]["Id"]` | `60022246625681` |

## 4. Address details (page 1)

Source list: `BORROWER["BorrowerAddress"]` (list of 4 in the fixture).

| PDF field | JSON path | Notes |
|---|---|---|
| Address line | `BorrowerAddress[i]["CreditAddress"]["StreetAddress"]` + `["Region"]` + `["PostalCode"]` | Composed as `"{StreetAddress}, {RegionName}, {PostalCode}"`; `Region` translated via `constants.STATE_CODES` (standard CIBIL 2-digit state code table, e.g. `"03"→"Punjab"`, `"27"→"Maharashtra"`, `"99"→"APO Address"`) |
| Category | derived: last item in address-order list (`addressOrder` descending) is **Permanent Address**, all others are **Residence Address** | Confirmed against sample PDF: 4 addresses, `addressOrder` 0,1,2 → "Residence Address", `addressOrder` 3 (highest) → "Permanent Address" |
| Residence Code (ownership) | `BorrowerAddress[i]["Ownership"]["symbol"]` translated via `constants.ADDRESS_OWNERSHIP_LABELS` (`"01"→"Owned"`) | empty symbol → `-` |
| Date Reported | `BorrowerAddress[i]["dateReported"]` (ISO `YYYY-MM-DD+TZ`) | formatted `DD/MM/YYYY` |

## 5. Contact details (page 2)

Source list: `BORROWER["BorrowerTelephone"]` (list of 2 in the fixture).

| PDF field | JSON path | Notes |
|---|---|---|
| Telephone Number Type | `BorrowerTelephone[i]["PhoneType"]["symbol"]` translated via `constants.PHONE_TYPE_LABELS` (`"01"→"Mobile Phone"`, `"03"→"Office Phone"`) |
| Telephone Number | `BorrowerTelephone[i]["PhoneNumber"]["Number"]` |
| Telephone Extension | not present in feed | rendered as `-` |

## 6. Email details (page 2)

| PDF field | JSON path |
|---|---|
| Email ID | `BORROWER["EmailAddress"]["Email"]` |

## 7. Employment details (page 2)

| PDF field | JSON path | Notes |
|---|---|---|
| Account Type | `BORROWER["Employer"]["account"]` translated via `constants.ACCOUNT_TYPE_LABELS` (same table as tradeline account types; value `"15"` → "Current Loan Against Bank Deposits (LABD)") | This is the account-type code of the tradeline the bureau associates with employer info, not a literal job title |
| Date Reported | `BORROWER["Employer"]["dateReported"]` (ISO) → `DD/MM/YYYY` |
| Occupation | `BORROWER["Employer"]["OccupationCode"]["description"]` | empty in feed → `-` |
| Income | not present in feed | rendered as `-` |
| Monthly / Annual Income Indicator | `BORROWER["Employer"]["IncomeFreqIndicator"]` | empty → `-` |
| Net / Gross Income Indicator | `BORROWER["Employer"]["NetGrossIndicator"]` | empty → `-` |

## 8. Accounts (pages 2–10)

Source list: `TLCR["TradeLinePartition"]` (list of 10 in the fixture; each item is `{"accountTypeSymbol", "Tradeline": {...}}`).

**Grouping/order** (confirmed against sample PDF page order): all accounts with
empty/missing `Tradeline.dateClosed` are **Open Accounts** and render first, in
original list order; all others are **Closed Accounts**, rendered next, in
original list order. In the fixture this yields tradeline index 9 (PNB) as the
1 open account, and indices 0–8 (ICICI ×9) as the 9 closed accounts — matching
`report_summary.open_accounts=1` / `closed_accounts=9`.

| PDF field | JSON path | Notes |
|---|---|---|
| Member Name | `Tradeline["creditorName"]` |
| Account Type | `accountTypeSymbol` (top of tradeline item, mirrored at `Tradeline["GrantedTrade"]["AccountType"]["symbol"]` and `["CreditType"]["symbol"]`) translated via `constants.ACCOUNT_TYPE_LABELS` | `"02"→"Housing Loan"`, `"01"→"Auto Loan (Personal)"`, `"15"→"Current Loan Against Bank Deposits (LABD)"` |
| Account Number | `Tradeline["accountNumber"]` | rendered in full by default, matching the reference PDF; optional masking available — see Security note |
| Ownership | `Tradeline["AccountDesignator"]["symbol"]` translated via `constants.OWNERSHIP_LABELS` | `"1"→"Individual"`, `"4"→"Joint"` |
| Credit Limit | `Tradeline["GrantedTrade"]["CreditLimit"]` | sentinel `"-1"` → `-` |
| Sanctioned Amount | `Tradeline["highBalance"]` | formatted as INR (`₹40,00,000`); **this is the field used for "Sanctioned Amount" in the sample PDF**, confirmed by exact value match across all 10 accounts |
| Current Balance | `Tradeline["currentBalance"]` | INR |
| Cash Limit | `Tradeline["GrantedTrade"]["CashLimit"]` | sentinel `"-1"` → `-` |
| Amount Overdue | `Tradeline["GrantedTrade"]["amountPastDue"]` | INR, `0` allowed |
| Rate of Interest | `Tradeline["GrantedTrade"]["interestRate"]` | sentinel `"-1.00"` → `-`; else `"{v}%"` |
| Repayment Tenure | `Tradeline["GrantedTrade"]["termMonths"]` | sentinel `"-1"` → `-` |
| EMI Amount | `Tradeline["GrantedTrade"]["EMIAmount"]` | sentinel `"-1"` → `-`; else INR |
| Payment Frequency | `Tradeline["GrantedTrade"]["PaymentFrequency"]["symbol"]` translated via `constants.PAYMENT_FREQUENCY_LABELS` | `"03"→"Monthly"`; empty symbol → `-` |
| Actual Payment Amount | `Tradeline["GrantedTrade"]["actualPaymentAmount"]` | sentinel `"-1"` → `-`; else INR |
| Date Opened / Disbursed | `Tradeline["dateOpened"]` (ISO) → `DD/MM/YYYY` |
| Date Closed | `Tradeline["dateClosed"]` | empty → `-` |
| Date of Last Payment | `Tradeline["GrantedTrade"]["dateLastPayment"]` | empty → `-` |
| Date Reported And Certified | `Tradeline["dateReported"]` |
| Value of Collateral | `Tradeline["GrantedTrade"]["collateral"]` | sentinel `"-1"` → `-`; else INR |
| Written-off Amount (Total) | `Tradeline["writtenOffAmtTotal"]` | sentinel `"-1"` → `-`; else INR |
| Written-off Amount (Principal) | `Tradeline["writtenOffPrincipal"]` | sentinel `"-1"` → `-`; else INR |
| Settlement Amount | `Tradeline["settlementAmount"]` | sentinel `"-1"` → `-`; else INR |

### 8a. Payment history (per account)

Source: `Tradeline["GrantedTrade"]["PayStatusHistory"]`.

| PDF field | JSON path | Notes |
|---|---|---|
| Payment Start Date | `PayStatusHistory["startDate"]` | most recent reported month, ISO → `DD/MM/YYYY` |
| Payment End Date | `PayStatusHistory["endDate"]` | oldest reported month |
| Payment History grid | `PayStatusHistory["MonthlyPayStatus"]` = list of `{"date": ISO, "status": "0".."N"/"XXX"}` | grouped by calendar year extracted from `date`, columns Dec→Jan, cell = `status`; legend STD/SUB/DBT/LSS/SMA/XXX rendered as static text (`constants.PAY_STATUS_LEGEND`) |
| (fallback) `PayStatusHistory["status"]` | comma-joined string mirroring `MonthlyPayStatus` order | used only if `MonthlyPayStatus` list is absent/empty |

## 9. Enquiries (page 11)

Source list: `TLCR["InquiryPartition"]` (list of 4 in the fixture; each item is `{"Inquiry": {...}}`).

| PDF field | JSON path | Notes |
|---|---|---|
| Member Name | `Inquiry["subscriberName"]` |
| Date Of Enquiry | `Inquiry["inquiryDate"]` (ISO) → `DD/MM/YYYY` |
| Enquiry Purpose | `Inquiry["inquiryType"]` translated via `constants.ACCOUNT_TYPE_LABELS` fallback `constants.INQUIRY_PURPOSE_OVERRIDES` | `"00"→"Other"` |
| Enquiry Amount | `Inquiry["amount"]` | INR |
| (unused) Enquiry control number | `Inquiry["enqControlNum"]` | parsed, not shown (matches sample PDF, which omits it) |

## 10. Report-level summary counters (used for cards / totals, not just page 1)

All from `SUMMARY` (`root["report_summary"]`), cross-checked against
`root["cibil_report"][...]["CreditSummaryData"]` where overlapping:

| Field | JSON path | Cross-check path |
|---|---|---|
| Total accounts | `SUMMARY["total_accounts"]` | `len(TLCR["TradeLinePartition"])` |
| Open accounts | `SUMMARY["open_accounts"]` | count of tradelines with empty `dateClosed` |
| Closed accounts | `SUMMARY["closed_accounts"]` | count of tradelines with non-empty `dateClosed` |
| Total sanctioned amount | `SUMMARY["total_sanctioned_amount"]` | sum of `Tradeline["highBalance"]` |
| Total current balance | `SUMMARY["total_current_balance"]` | sum of `Tradeline["currentBalance"]` |
| Total amount overdue | `SUMMARY["total_amount_overdue"]` | sum of `Tradeline["GrantedTrade"]["amountPastDue"]` |
| Total enquiries | `SUMMARY["total_enquiries"]` | `len(TLCR["InquiryPartition"])` |
| On-time payment history % | `SUMMARY["on_time_payment_history_pct"]` | `CreditSummaryData["OnTimePaymentHistory"]` |
| Credit card utilization % | `SUMMARY["credit_card_utilization_pct"]` | `CreditSummaryData["CreditCardUtilization"]` |
| Oldest account age (months) | `SUMMARY["oldest_account_age_months"]` | `CreditSummaryData["OldestCreditAccountPeriod"]` |
| Credit mix % | not in `SUMMARY` | `CreditSummaryData["CreditMix"]` — parsed, not on sample PDF page 1, kept on model for future use |

## 11. Disclaimer (page 11, footer of every page)

Not present anywhere in the JSON — this is **static regulatory text**, owned
by the PDF engine itself (`pdf_engine/constants.py::DISCLAIMER_TEXT` and
`FOOTER_TEXT`), reproduced verbatim from the sample PDF:

> "All information contained in this credit report has been collated by
> TransUnion CIBIL Limited (TU CIBIL) based on information provided/submitted
> by its various members ("Members")... COPYRIGHT {year} TRANSUNION CIBIL.
> ALL RIGHTS RESERVED."

The engine substitutes the generation year/timestamp and the report control
number at render time; it never fabricates report data here.

---

## Visual design pass (local assets only)

A second refinement pass restyled every section to visually match
`docs/sample_report.pdf.pdf` (cyan section labels, light-gray bordered
cards, a semicircular score gauge, single-column "ACCOUNT DETAILS" rows,
split running header/footer). This pass changed **presentation only** --
every JSON path in this document is unchanged. Assets used, all local,
none downloaded:

- `pdf_engine/assets/cibil-logo.svg` -- the CIBIL wordmark, rendered via
  `svglib` (`svg2rlg`) into a scaled ReportLab `Drawing` in
  `helpers.logo_drawing()`. If the SVG can't be loaded for any reason, the
  engine falls back to a text "CIBIL / Part of TransUnion" brand block
  (`score_section._brand_block`) rather than failing.
- `pdf_engine/assets/Montserrat/static/Montserrat-{SemiBold,Bold}.ttf` --
  page title ("CIBIL Score & Report"), greeting, and cyan section headings.
- `pdf_engine/assets/Poppins/Poppins-Bold.ttf` -- the large numeric score in
  the gauge.
- `pdf_engine/assets/Roboto/static/Roboto-{Regular,Medium,Bold}.ttf` --
  everything else: field labels/values, table cells, footer, disclaimer.

All three families embed the Indian Rupee glyph (U+20B9), confirmed via
`fontTools` before wiring them in, so `theme.CURRENCY_SYMBOL` is always the
real "₹" character -- no "Rs." fallback is needed when the local assets are
present (`theme._register_fonts()` still falls back to base-14 Helvetica,
and currency to `"Rs. "`, if an asset file is ever missing).

---

## Fields intentionally NOT rendered

| JSON path | Reason |
|---|---|
| `client_key`, `web_token_url` | integration credentials, not report content |
| `diagnosis.*` | API call diagnostics |
| `steps[*]` | API orchestration trace (FulfillOffer, GetAuthenticationQuestions, etc.) |
| `TLCR.SafetyCheckPassed`, `.SafetyCheckFailure`, `.DeceasedIndicator`, `.FraudIndicator`, `.Frozen`, `.Message` | internal bureau flags, all falsy/blank in fixture; parsed onto the model for future compliance use but not shown on the standard report layout, matching the sample PDF |
| `Sources.Source.OriginalData` | base64 blob of the raw bureau payload, not human content |

---

## Code tables required (`pdf_engine/constants.py`)

Derived by cross-referencing every `symbol` value present in the fixture
against the corresponding rendered text in `docs/sample_report.pdf.pdf`, and
extended with the standard published TransUnion CIBIL code sets for
completeness (with a safe "Unknown ({code})" fallback for anything not
covered — the parser never guesses or crashes on an unmapped code):

- `ACCOUNT_TYPE_LABELS` — 2-digit account/credit type code → label (`01` Auto Loan (Personal), `02` Housing Loan, `15` Current Loan Against Bank Deposits (LABD), …)
- `OWNERSHIP_LABELS` — `AccountDesignator.symbol` → label (`1` Individual, `4` Joint, …)
- `ADDRESS_OWNERSHIP_LABELS` — address `Ownership.symbol` → label (`01` Owned, …)
- `PHONE_TYPE_LABELS` — `PhoneType.symbol` → label (`01` Mobile Phone, `03` Office Phone, …)
- `STATE_CODES` — 2-digit region code → Indian state/UT name (`03` Punjab, `27` Maharashtra, `99` APO Address, …) — standard published CIBIL region table
- `PAYMENT_FREQUENCY_LABELS` — `PaymentFrequency.symbol` → label (`03` Monthly, …)
- `IDENTIFIER_NAME_LABELS` — `IdentifierName` → label (`TaxId` Income Tax ID Number (PAN), `CkycId` CKYC, `SocialId` Social/Bureau ID)
- `PAY_STATUS_LEGEND` — static legend text block (STD/SUB/DBT/LSS/SMA/XXX/###)

All tables are TransUnion CIBIL industry-standard code sets, not CRIF-specific
logic.

---

## Security note

Account numbers, PAN, and CKYC are sensitive PII. The reference sample PDF
renders these in full, so the engine matches that by default. An optional
`mask_account_numbers=True` flag on `generate_report` (via `helpers.mask_account_number`,
keeping only the last 4 characters) is available for deployments that need it;
this is a rendering-time-only switch and never changes the parsed model.
No PII from the fixture is ever hardcoded into engine source — all customer
data flows through the parser at call time.
