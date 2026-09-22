# Bond input/output contract

**Evidence:** [get_bonds declaration](declared/get_bonds.md), [provider detail](evidence/detail.json), [direct error](evidence/bond-entitlement-error.json), [sandbox error](evidence/execute.json). All success examples below are illustrative, not runtime-verified.

## 1. Public wrapper versus provider method

The public get_bonds tool accepts one large argument object. metrics chooses a route; issuer/issuers, bond_tickers, dates, and mode-specific settings determine provider parameters. Local filters, aggregation, sorting, projection, and top/offset may then shape the result. The exact ordering of every transformation is not proven by the visible declaration.

For list mode, the documented provider is client.bond.list.list_bonds. Its provider inputs are bond_tickers, industries, indicator_list, filter, indicator_group. Public from_date/to_date are not provider list inputs. Filter issue_date/maturity_date explicitly instead.

The wrapper requests a Vietnamese indicator list internally and maps returned names into snake_case. A listed-equity issuer code such as VCB may be forwarded through the provider's bond_tickers selector. A company name is instead described as a broader fetch/cache followed by issuer-name filtering. This is a wrapper-specific behavior, not a general identifier equivalence.

For list_issuance_info, the discovered provider is client.bond.issuers.list_issuance_info. Its issuer selector is tickers. The public wrapper uses issuer/issuers to express that selection. Do not send provider-only arguments directly to the public tool.

## 2. Choose by row grain before choosing a measure

| Question/required grain | Mode(s) | Conditional input and output restrictions |
|---|---|---|
| Individual bonds and issuer attributes | list | bond_tickers for bonds; issuer/issuers for issuers; local/provider filters; exact list allowlist below |
| Planned future issuance | issuance_plan | from_date/to_date; documented default today through six months ahead |
| Issuance by industry | sector_issuance_stats / primary_issuance_by_sector | year + time_range; industry grain |
| Market/industry period-end outstanding | outstanding_bonds; primary_outstanding also mentioned | time_range; industries for applicable route; no issuer/bond breakdown |
| Issuance by method/collateral | issued_value_by_method / issued_value_by_collateral | time_range; output dimension must match intended grouping |
| Issuer issuance ranking | top_issuers_by_issuance | year + time_frequency; not time_range |
| Issuer outstanding ranking | top_issuers_by_outstanding | Only supported ranking measures; full provider requirements unverified |
| Expected market principal/coupon cash flows | expected_cash_flow_market / expected_cash_flow_by_industry | year + time_range; coupon_type='Origin' for principal-only maturity pressure |
| Late-payment statistics | late_payments / primary_late_payments | date, industry, late_payment_value, count; no issuer/bond identity |
| Issuer bond issuance list | list_issuance_info | issuer/issuers required; provider status/collateral/related semantics below |
| Issuer upcoming principal/interest | payments_due | issuer/issuers; time_range defaults Monthly; future-only |
| Issuer remaining maturities | remaining_maturities | issuer/issuers; not a market-wide substitute; no time_range contract described |
| Issuer debt/equity context | relative_to_equity | issuer/issuers; full output schema unverified |
| Issuer outstanding by provider coupon bands | outstanding_by_coupon_group | issuer/issuers; provider bands, not arbitrary user bands |
| Bond trading history | trading_stats | from_date; default trailing 30 days if omitted; rows by trading date |
| Industry trading | sector_trading_stats / sector_trading_value | from_date; description disallows top on sector_trading_value |
| Liquidity by trading method | market_liquidity_by_method | from_date; period/method output |
| Cumulative liquidity by bond/issuer | liquidity_change_by_bond / liquidity_change_by_issuer | from_date/to_date; top supported; cumulative window, not time-series rows |
| Issuer average YTM | issuer_avg_ytm | from_date; issuer-level output |
| Bid/offer rate ranking | top_interest_rate | buy explicitly true/false (documented fallback true); trading_type Deal/Match |
| Current price boards | realtime_trading_board / realtime_matching_board | Snapshot only; not historical date-range queries |
| Bond pricing information | bond_info | bond_tickers required |
| Bond cash flows | cash_flow | bond_tickers required |
| YTM from assumed price | price_ytm | One bond in bond_tickers + dirty_price; optional payment_date |
| Buyback transactions | buyback_transactions | Optional issuer/bond selection; from_date/to_date; group issuer before ranking |
| Ownership/company relationships | interconnection_map | Issuer ticker via issuer/issuers or bond_tickers; optional percentage bounds |

These names are documented strings and aliases, not a complete machine-enforced enum. A mode's existence does not establish entitlement, available history, or supported aggregation fields.

time_range/time_frequency are described as Monthly, Quarterly, Yearly. When a query specifies a month or quarter, use year and the supported month/quarter field. Do not assume every row date is an observation date.

## 3. List-mode output allowlist

The declaration explicitly gives the following list-only fields. Their grouping below is explanatory; scalar types, nullability, and units are not fully specified by a machine-readable row schema.

| Group | Declared field names |
|---|---|
| Identity/classification | bond_ticker, industry, issuer, issuer_organization, bond_type, issue_location, currency_code, issue_method |
| Dates/tenor | issue_date, maturity_date, original_maturity_date, term, remaining_years, next_trading_date, trading_date |
| Amounts/prices/yield | issue_value, outstanding_value, par_value, coupon_value, dirty_price, ytm, redemption |
| Coupon | next_coupon_rate, current_coupon_rate, first_coupon_rate, coupon_type, payment_calendar_name, float_bench, float_interest_spread |
| State/options | active_status_name, trading_status_name, green_bond, convertible, covered_warrant |
| Collateral/guarantees | collateral, collateral_type_name, collateral_description, payment_guarantee, payment_guarantee_ticker |
| Credit/events | bond_event_type_name, credit_public_date, late_payment, debt_restructuring, rating_type_name, rating_date, rating_score_value |

List does **not** support release_method, source_url, public_date, principal_late_payment, or coupon_late_payment according to its explicit allowlist statement. Later prose contradicts some exclusions and suggests additional fields. Follow the restrictive list contract until a runtime schema confirms otherwise.

Examples of declared provider aliases:

| Provider alias | Normalized field |
|---|---|
| BondTicker | bond_ticker |
| OrganizationShortName | issuer |
| IssueDateId | issue_date |
| MaturityDateId | maturity_date |
| CouponInterestRateCurrent | current_coupon_rate |
| CouponInterestRateNext | next_coupon_rate |
| ActiveStatusName / active_status | active_status_name |
| Outsdval | outstanding_value |

An alias is a naming translation, not evidence that differently named financial concepts mean the same thing.

## 4. Financial semantics that must travel with the schema

### Outstanding is a stock

For outstanding_bonds, provider outstanding_bond becomes outstanding_value: a period-end balance. issue_value, value_of_canceled_bond, and value_of_redeemed_bond are period flows.

Monthly labels may look like "2026-05-01 00:00", but mean May 2026, not a measurement on May 1. Yearly labels can use January 1; quarterly labels can be "Q2-2026". For latest outstanding, choose the newest period's balance. Do not sum the balance over periods. Differences are appropriate only when the question asks for changes.

A useful proposed schema separates period_start, period_end, observation_date, and measure_kind instead of using one ambiguous date string.

### Coupon and late-payment meanings

- current_coupon_rate, next_coupon_rate and first_coupon_rate are distinct. Missing current coupon does not permit silently substituting the next coupon.
- List late_payment is declared as principal-plus-interest late-payment **value over one year**, in VND, not a boolean.
- A list filter late_payment eq true means nonzero value; false means zero/absent according to the wrapper description. It does not prove all historical obligations were settled.
- debt_restructuring is declared as a one-year monetary amount in **VND billions**, not a flag. Its unit differs from late_payment.
- Event classification and one-year monetary measures are different evidence. Count distinct bonds for bond counts; count rows only when the intended unit is records.
- A late-payment classification is not automatically a legal/default determination.

The provider coupon-band example labels x>=12 as ">12%". That label is mathematically inaccurate at exactly 12; a new KimFI bucket should use explicit inclusive/exclusive boundaries and a matching label such as "12% and above".

### Currency, amounts and missing values

Do not generalize units from one provider route to another. The sampled provider detail for list_issuance_info explicitly states VND amounts and percentage-point coupon rates. The get_bonds list declaration separately states VND for late_payment and VND billions for debt_restructuring; it does not supply a typed unit dictionary for every field.

Preserve missing values. The discovered provider detail suggests fillna(0) before sums/averages. That is a documented instruction, but **not a suitable blanket KimFI rule**: replacing a missing coupon with zero changes a mean and falsely implies a zero-coupon bond. A proposed adapter should publish non-null counts, missing counts, and the aggregation policy.

## 5. Provider detail: list_issuance_info

The following is declared by the discovered provider detail, not by a successful data response.

### Inputs

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| tickers | array | Required | Issuer equity codes; use an array even though prose includes a scalar example |
| status | array | Default [15,22] | 15 normal; 16 cancelled at maturity; 17 cancelled by repurchase; 22 matured but not fully paid |
| collateral | string | Default All | All, Yes, No |
| related | boolean | Default true | Include related-company issuance |

related=true can expand scope beyond the named issuer. The live probe explicitly used related=false.

### Output DataFrame columns

| Column | Declared type | Meaning/unit |
|---|---|---|
| ticker | string | Issuer security code |
| bond_ticker | string | Bond code |
| issuer | string | Issuer short name |
| issue_method | string | Placement/issuance method |
| next_interest_payment_date | string | YYYY-MM-DD HH:MM |
| issue_date | string | YYYY-MM-DD HH:MM |
| maturity_date | string | YYYY-MM-DD HH:MM |
| coupon_rate | number | Percent; 10.96 means 10.96%, not 0.1096 |
| issue_value | number | VND, no extra multiplier |
| outstanding_value | number | Current VND balance |
| duration | number | Months |
| status | string | Activity/payment status label |
| collateral_type | string | Collateral category |

The provider description permits NaN in numeric fields; that caveat is not encoded in its simple type labels. A JSON serializer must decide how to represent missing numeric values without producing invalid JSON NaN tokens.

## 6. Illustrative request cookbook

These requests demonstrate declared contracts. They are not captured successful executions.

### A. Active VCB bonds ordered by maturity

```json
{
  "metrics": ["list"],
  "issuer": "VCB",
  "filters": [
    {"field": "active_status_name", "op": "contains", "value": "Đang lưu hành"}
  ],
  "fields": ["bond_ticker", "issuer", "maturity_date", "current_coupon_rate", "outstanding_value", "active_status_name"],
  "sort_by": "maturity_date",
  "sort_order": "asc",
  "top": 10
}
```

The wrapper documents mapping "Đang lưu hành" to provider label "Bình thường". Trading status is a separate axis. This request's top=10 means its returned amounts must not be presented as an issuer total.

### B. Issuers ranked by one-year late-payment value

```json
{
  "metrics": ["list"],
  "group_by": ["issuer"],
  "aggregate": ["sum:late_payment"],
  "sort_by": "sum_late_payment",
  "sort_order": "desc",
  "top": 5
}
```

Expected grain: issuer aggregates, not bond rows. This is combined principal and interest, not principal-only late payment. The precise aggregate response envelope and coverage of all matched bonds remain unverified.

### C. Principal maturity pressure

```json
{
  "metrics": ["expected_cash_flow_market"],
  "time_range": "Monthly",
  "year": 2026,
  "coupon_type": "Origin"
}
```

The description says a call may return a multi-year future series. Select the intended window from that series. ALL includes coupon interest and is not equivalent to principal maturities. Any derived ratio requires a separately compatible outstanding denominator and aligned coverage.

### D. Top issuer by buybacks during August 2026

```json
{
  "metrics": ["buyback_transactions"],
  "from_date": "2026-08-01",
  "to_date": "2026-08-31",
  "group_by": ["issuer"],
  "aggregate": ["sum:redemption_value"],
  "sort_by": "sum_redemption_value",
  "sort_order": "desc",
  "top": 1
}
```

The inclusive/exclusive semantics of FiinProX date bounds were not formally established. Verify them before translating this window to KimFI's half-open dateRange. Do not assume reported buyback rows are independently confirmed settlement events.

### E. Issuance ranking for a completed year

```json
{
  "metrics": ["top_issuers_by_issuance"],
  "year": 2025,
  "time_frequency": "Yearly",
  "top": 10
}
```

This route uses time_frequency. Renaming it to time_range without checking the contract changes the request.

## 7. What the access error establishes

Both direct list mode and the discovered issuer-list provider failed because the account lacked access or an active service entitlement. The direct response included empty rows, errors, missing requested fields and has_gap=true. The sandbox returned plain error text.

This establishes a response-handling requirement, not a bond-market data gap. Metadata discovery remained available. Do not strip issuer filters or switch financial meaning to manufacture a successful-looking answer.
