# All 17 FiinProX tools: input and output reference

Captured 2026-09-22. Parameter tables are extracted from the host-visible TypeScript declarations. “Required” means syntactically required at that bridge; prose may impose additional conditional requirements. Optional does not imply a known default. Null is accepted only where explicitly present in the type. Types named `number` do not establish integer-only validation or numeric bounds.

Every example is illustrative unless explicitly described as observed; the linked evidence files are the authoritative record of actual requests/responses. Inner output fields below are not complete JSON Schemas where the service did not expose one. See [envelope handling](README.md#3-output-envelopes-and-decoding).

## Inventory

| Tool | Required bridge arguments | Declared structured payload |
|---|---|---|
| [search_tool_candidates](#search_tool_candidates) | `search_query` | `open structured object` |
| [get_tool_detail](#get_tool_detail) | None syntactically | `open structured object` |
| [execute_api](#execute_api) | `code` | `{ result: string }` |
| [search_filters](#search_filters) | None syntactically | `{ result: string }` |
| [execute_screening](#execute_screening) | `filter` | `{ result: string }` |
| [search_fundamental_fields](#search_fundamental_fields) | `searching_keywords` | `{ result: string }` |
| [get_fundamental_data](#get_fundamental_data) | `data_type`, `tickers`, `years` | `{ result: string }` |
| [search_sector_code_by_name](#search_sector_code_by_name) | `keyword` | `{ result: string }` |
| [get_tickerlist](#get_tickerlist) | `tickers` | `{ result: string }` |
| [get_equity_snapshot](#get_equity_snapshot) | None syntactically | `{ result: string }` |
| [fetch_trading_data](#fetch_trading_data) | `fields`, `realtime`, `tickers` | `{ result: string }` |
| [get_market_statistics](#get_market_statistics) | `from_date`, `metric`, `tickers` | `{ result: string }` |
| [get_technical_indicator](#get_technical_indicator) | `indicators`, `tickers` | `{ result: string }` |
| [get_bonds](#get_bonds) | None syntactically | `{ result: string }` |
| [get_economy](#get_economy) | `metrics` | `{ result: string }` |
| [get_funds](#get_funds) | None syntactically | `{ result: string }` |
| [report_mcp_bug](#report_mcp_bug) | None syntactically | `{ result: string }` |

## search_tool_candidates

[Full declaration and original provider guidance](declared/search_tool_candidates.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `agent_id` | `string \| null` | No |
| `financial_keywords` | `Array<string> \| null` | No |
| `include_alternatives` | `boolean` | No |
| `original_query` | `string \| null` | No |
| `refine_query` | `string \| null` | No |
| `search_query` | `string` | Yes |
| `supplementary_mode` | `boolean` | No |
| `top_k` | `number` | No |

Discover a specialized provider API or cached solution. Use dedicated screening/fundamental discovery when appropriate; use this general path for peer comparisons, filing links, index valuation history, and needs beyond a direct tool.

Default top_k is documented as 5. Financial keywords should cover independent dimensions of intent. Inspect cache candidates first, then function candidates. One broader retry with an increased limit is documented when candidates do not fit.

Observed output: a structured object with search_query, core_tools, cache_candidates, function_candidates, ticker_entities, ready_to_answer, do_not_answer_from_this_result, required_next_tool, required_next_arguments, and NEXT_ACTION_REQUIRED. Candidates are metadata, not financial rows. The sampled generic bond query also returned apparently unrelated ticker entities; validate entity resolution against intent. Next: detail for a relevant returned candidate.

**Example request**:

```json
{
  "search_query": "Danh sách trái phiếu theo tổ chức phát hành",
  "include_alternatives": true,
  "top_k": 2
}
```

[Observed request and response](evidence/candidates.json). Compare the recorded request with any illustrative variant above.

## get_tool_detail

[Full declaration and original provider guidance](declared/get_tool_detail.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `ServerName` | `string \| null` | No |
| `agent_id` | `string \| null` | No |
| `detail_level` | `string` | No |
| `func_name` | `string \| Array<string> \| null` | No |
| `func_names` | `string \| Array<string> \| null` | No |
| `toolAction` | `string \| null` | No |
| `toolSummary` | `string \| null` | No |
| `tool_id` | `string \| Array<string> \| null` | No |

Retrieve a previously shortlisted function/cache contract. detail_level is described as minimal/execution/full, default execution, but is only a string in the bridge. Use func_name/func_names for functions or tool_id for cached solutions. A selected identifier is operationally needed despite all inputs being syntactically optional. Monitoring fields are accepted and ignored according to their comments.

Observed output: detail_level, tools[], and next-step flags. Each sampled tools entry had id, short_desc, parameters, output_desc, usage_instruction, happy_cases, execution_rules. The parameters field was prose, while output_desc.columns described field types and meanings. The sample described a DataFrame, not the final MCP envelope.

**Example request**:

```json
{
  "func_name": "client.bond.issuers.list_issuance_info",
  "detail_level": "full"
}
```

[Observed request and response](evidence/detail.json). Compare the recorded request with any illustrative variant above.

## execute_api

[Full declaration and original provider guidance](declared/execute_api.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `agent_id` | `string \| null` | No |
| `code` | `string` | Yes |

Execute a discovered provider call using Python. Read detail first. Use preloaded client; do not construct another client. Available names include pd, np, plt, mdates, datetime, timedelta, date, relativedelta, json, reduce, and documented wrappers. System/network imports and dynamic helpers such as getattr/eval/exec are forbidden. Print output; merely returning a Python value is not enough. Statements/ratios use the dedicated tools.

The description allows one correction after a code/argument error. An entitlement denial is not fixable by changing financial scope.

Declared output is a result string. Observed output was plain Success/Stdout/Stderr text, not JSON. Successful stdout is code-dependent. The sampled request below failed at provider access; the head/to_json projection was not verified to execute.

**Example request**:

```json
{
  "code": "result = client.bond.issuers.list_issuance_info(tickers=['VCB'], related=False)\nprint(result.head(2).to_json(orient='records', force_ascii=False))"
}
```

[Observed request and response](evidence/execute.json). Compare the recorded request with any illustrative variant above.

## search_filters

[Full declaration and original provider guidance](declared/search_filters.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `indicator_keyword` | `Array<string> \| null` | No |
| `sector_keyword` | `Array<string> \| null` | No |
| `sector_level` | `number \| null` | No |
| `sector_top_k` | `number` | No |
| `top_k` | `number` | No |

Discover screening indicator IDs and optionally sector codes. This catalog differs from fundamental field paths. Defaults: top_k=10, sector_top_k=10; sector levels are described as 1–5, omission searches all levels.

Observed output: JSON success/data; data contained count, indicatorsByQuery[], sharedIndicators[]. Sector searches are declared to return sectorsByQuery. Indicator fields included indicatorId, indicatorName, fullName, industryType, unit, multiplier, periods, hasData, dataStatus, score, path_mapping. periods contained interimCodes, defaultIndicatorInterimIdByCode, additionalConditionOnly.

The P/E probe returned ID "8014", diluted P/E, multiplier 1, Daily frequency. It must not silently stand in for a specifically requested basic P/E.

**Example request**:

```json
{
  "indicator_keyword": [
    "P/E"
  ],
  "top_k": 1
}
```

[Observed request and response](evidence/filters.json). Compare the recorded request with any illustrative variant above.

## execute_screening

[Full declaration and original provider guidance](declared/execute_screening.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `exchanges` | `Array<string> \| null` | No |
| `export_limit` | `number` | No |
| `filter` | `Array<unknown>` | Yes |
| `sectors` | `Array<string> \| null` | No |
| `sort` | `Array<unknown> \| null` | No |

Run AND-combined conditions built from search_filters. export_limit defaults to 50 preview records. Omit exchanges/sectors for unrestricted scope. sort is described as [zero_based_filter_index, "asc"|"desc"]. Filter objects are not structurally typed.

Threshold rule: raw = display / multiplier. For multiplier 100, displayed 20% becomes 0.20; for multiplier 1e-9, displayed VND1bn becomes 1e9. Existence/disclosure requests omit min/max, since min=0 wrongly excludes disclosed losses.

The prose asks for all company-type variants in one AND-combined list. Cross-type behavior is unverified; do not assume OR semantics. Examples use camelCase filter keys while a comment uses snake_case. Accepted aliases are unverified.

Output: result string with screening data/preview; full successful inner schema not sampled. The example uses the discovered diluted P/E ID but was not executed.

**Example request**:

```json
{
  "filter": [
    {
      "indicatorId": "8014",
      "interimCode": "Daily",
      "max_value": 15
    }
  ],
  "exchanges": [
    "HOSE"
  ],
  "export_limit": 10
}
```

## search_fundamental_fields

[Full declaration and original provider guidance](declared/search_fundamental_fields.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `searching_keywords` | `string \| Array<string>` | Yes |
| `top_k` | `number` | No |

Resolve financial-statement/ratio field paths. top_k defaults to 5. Accepts a keyword or keyword list. Use the company-type key in path_mapping.

Observed output: JSON success/data, with data keyed by query string. Each value was a list containing id, path_mapping, keyword_en, description, statement_type, data_type, _score. Generic prose says keyword, while the sample used keyword_en.

The sampled ROE hit contained COMPANY/SECURITIES/INSURANCE mappings, not BANK. That hit is insufficient for a bank request, but does not prove bank ROE is unavailable.

**Example request**:

```json
{
  "searching_keywords": "ROE",
  "top_k": 1
}
```

[Observed request and response](evidence/fundamental_fields.json). Compare the recorded request with any illustrative variant above.

## get_fundamental_data

[Full declaration and original provider guidance](declared/get_fundamental_data.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `data_type` | `"statement" \| "ratios"` | Yes |
| `fields` | `Array<string> \| null` | No |
| `quarters` | `Array<number> \| null` | No |
| `report_type` | `"consolidated" \| "separate"` | No |
| `statement` | `"IncomeStatement" \| "BalanceSheet" \| "CashFlow" \| "Note" \| "BankCurrencyRisk" \| "BankInterestRateRisk" \| "BankLiquidityRisk" \| "CapitalAdequacyReport" \| null` | No |
| `tickers` | `Array<string>` | Yes |
| `years` | `number \| Array<number>` | Yes |

Retrieve financial statements or ratios for known companies and fiscal periods. Copy data_type and company-type-specific field paths from discovery. Statements require the returned PascalCase statement type. CapitalAdequacyReport is annual: omit quarters. fields/statement are bridge-optional despite semantic requirements for particular requests. tickers must be an array, even for one security. years accepts a number or number array. Report types are consolidated/separate; the captured comments do not establish a default.

Declared output includes data and ticker_entities, but complete inner row nesting was not supplied or sampled. Ratios are not all percentages: ROE/margins/growth use 0–100 percent, leverage/liquidity/valuation use multiples, and cycle measures use days. Statement items retain their own units.

The example uses a discovered COMPANY ROE path; it is unexecuted. Peer comparisons, industry aggregates, and filing URLs require suitable discovery routes.

**Example request**:

```json
{
  "data_type": "ratios",
  "fields": [
    "4_profitability_ratio.roe"
  ],
  "tickers": [
    "HPG"
  ],
  "years": 2025
}
```

## search_sector_code_by_name

[Full declaration and original provider guidance](declared/search_sector_code_by_name.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `dense_weight` | `number \| null` | No |
| `keyword` | `string` | Yes |
| `search_mode` | `"bm25" \| "dense" \| "hybrid"` | No |
| `sector_level` | `number \| null` | No |
| `top_k` | `number` | No |

Resolve a natural-language sector to a classification code, not a list of securities. Defaults: search_mode=hybrid, sector_level=4, top_k=5. Broader levels/null should match requested scope. dense_weight falls back to server configuration; observed 0.8 is not a guaranteed universal default. Preserve compound names containing &, /, commas, or “và”.

Observed output: success; data.status/query/rows/warnings/metadata. Row fields: industryName, industryCode, icbCode, level, score. Metadata included search_mode, dense_weight, returned_rows, sector_level. The example returned BANKS_L2 and ICB "8300".

**Example request**:

```json
{
  "keyword": "ngân hàng",
  "sector_level": 2,
  "top_k": 1
}
```

[Observed request and response](evidence/sector.json). Compare the recorded request with any illustrative variant above.

## get_tickerlist

[Full declaration and original provider guidance](declared/get_tickerlist.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `tickers` | `Array<string>` | Yes |

Retrieve constituent/registry codes. The only public argument is tickers, a list of selectors. Examples: VN30/VN100/VNINDEX/HNXINDEX for constituents; BANKS_L2 or numeric ICB codes for sectors; INDEX for indices; Sector for classifications; FU for futures; CW for warrants; FUND for funds.

Preserve OTC and longer codes. Use equity_snapshot for company attributes, and general discovery for portfolio rebalancing.

Observed output: JSON success/data with status, rows, errors, warnings, metadata, field_dictionary. VN30 returned 30 ticker rows. Metadata contained provider_function, provider_kwargs, returned_rows and coverage. An internal otc=true appeared in provider_kwargs but is not an exposed public input. field_dictionary also mentioned name, even though only ticker was present.

**Example request**:

```json
{
  "tickers": [
    "VN30"
  ]
}
```

[Observed request and response](evidence/tickerlist.json). Compare the recorded request with any illustrative variant above.

## get_equity_snapshot

[Full declaration and original provider guidance](declared/get_equity_snapshot.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `exchanges` | `Array<string> \| null` | No |
| `fields` | `Array<string> \| null` | No |
| `filters` | `Array<{ [key: string]: unknown; }> \| null` | No |
| `offset` | `number` | No |
| `screener_date` | `string \| null` | No |
| `sectors` | `Array<string> \| null` | No |
| `sort_by` | `string \| null` | No |
| `sort_order` | `"asc" \| "desc"` | No |
| `tickers` | `Array<string> \| null` | No |
| `top` | `number \| null` | No |

Return one row per security/company, including OTC where supported. Choose exactly one of tickers/exchanges/sectors. fields only project; they do not aggregate or deduplicate. sort ranks company rows, not sectors. Filters are local. offset is zero-based after filtering/sorting. Omitting top is documented to return all matches. Omitting screener_date uses the latest preceding business day.

Declared fields: ticker, organization_name, organization_short_name, exchange_code, sector, industry_level_1..5, tax_code. Dynamic snapshot fields include literal runtime column names such as “P/E cơ bản”, “P/B”, “Vốn hóa thị trường”, and “% Thay đổi giá từ đầu năm”. They depend on availability.

An exchanges=["HOSE"] request still returns company rows, not an exchange aggregate. Use screening discovery for metrics/periods outside the fixed snapshot fields, and general discovery for market-level aggregates. Full success envelope not sampled.

**Example request**:

```json
{
  "tickers": [
    "VCB"
  ],
  "fields": [
    "ticker",
    "organization_name",
    "exchange_code",
    "sector"
  ]
}
```

## fetch_trading_data

[Full declaration and original provider guidance](declared/fetch_trading_data.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `adjusted` | `boolean` | No |
| `by` | `"1m" \| "5m" \| "15m" \| "30m" \| "1h" \| "2h" \| "4h" \| "1d"` | No |
| `fields` | `Array<string>` | Yes |
| `from_date` | `string \| null` | No |
| `include_unclosed` | `boolean` | No |
| `lasted` | `boolean` | No |
| `period` | `number \| null` | No |
| `realtime` | `boolean` | Yes |
| `tickers` | `Array<string>` | Yes |
| `to_date` | `string \| null` | No |

Return uncached raw trading series. Required: tickers array, fields array, realtime boolean. Always send realtime=false. Prose mentions scalar tickers, but the visible bridge requires an array.

Dynamic fields: open/high/low/close/volume/value/bu/sd/fb/fs/fn. Do not put timestamp/ticker in fields; identifiers are added if supplied by source. Use period>=5 OR a from_date/to_date window. Daily dates: YYYY-MM-DD; intraday: YYYY-MM-DD HH:MM. adjusted defaults true. Daily lasted=true with no explicit window documents a five-bar fallback. include_unclosed can trigger a today-range retry for stale latest daily data. The spelling lasted is part of the interface.

Declared output: timestamp/ticker plus dynamic values; exact financial units/row nesting unverified. bu/sd are aggressive buy/sell volumes, not money. VN30 means the index itself; retrieve constituents first when individual stocks are intended. Derived comparisons/ranking go through discovery; indicators use the dedicated tool.

**Example request**:

```json
{
  "tickers": [
    "HPG"
  ],
  "fields": [
    "close",
    "volume"
  ],
  "realtime": false,
  "by": "1d",
  "period": 5
}
```

## get_market_statistics

[Full declaration and original provider guidance](declared/get_market_statistics.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `from_date` | `string` | Yes |
| `metric` | `"freefloat" \| "value_by_investor" \| "overview" \| "ceilingfloor" \| "foreign"` | Yes |
| `tickers` | `string \| Array<string>` | Yes |
| `time_filter` | `"Daily" \| "Weekly" \| "Monthly" \| "Quarterly" \| "Yearly" \| null` | No |
| `to_date` | `string \| null` | No |

Wrap five PriceStatistics methods. Required: metric, tickers, from_date (YYYY-MM-DD); optional to_date follows provider/current-date behavior.

- freefloat: tickers array; outputs ticker/timestamp/freefloat/outstanding_share/freefloat_rate.
- value_by_investor: tickers array; investor-category trading, not aggressive order flow.
- overview: ticker string or array, time_filter required; total_match_volume/value, total_deal_volume/value, market_cap, percent_price_change; documented for stocks.
- ceilingfloor: ticker string; ticker/timestamp/ceiling_value/floor_value.
- foreign: tickers array, time_filter required; foreign trading/ownership/room.

No fields, filters, top, offset, or sorting inputs. Named percentage fields use 0–100; share-count fields are quantities. No breadth counts or index valuation series. Full successful inner envelope not sampled.

**Example request**:

```json
{
  "metric": "foreign",
  "tickers": [
    "VCB"
  ],
  "from_date": "2026-08-01",
  "to_date": "2026-08-31",
  "time_filter": "Daily"
}
```

## get_technical_indicator

[Full declaration and original provider guidance](declared/get_technical_indicator.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `adjusted` | `boolean` | No |
| `by` | `"1m" \| "5m" \| "15m" \| "30m" \| "1h" \| "2h" \| "4h" \| "1d"` | No |
| `df_fields` | `Array<string> \| null` | No |
| `from_date` | `string \| null` | No |
| `include_signals` | `boolean` | No |
| `indicators` | `Array<{ [key: string]: unknown; }>` | Yes |
| `lasted` | `boolean` | No |
| `period` | `number \| null` | No |
| `source_field` | `"open" \| "high" \| "low" \| "close" \| "volume" \| "value" \| "bu" \| "sd" \| "fb" \| "fs" \| "fn"` | No |
| `tickers` | `Array<string>` | Yes |
| `to_date` | `string \| null` | No |

Fetch trading inputs and compute registered indicators in the server. Both tickers and indicators are lists. The description enumerates 98 names; preserve exact registry spelling, including unusual names. The indicator objects are open dictionaries: nested parameter validation is not fully visible.

Defaults: adjusted=true; source_field=close; df_fields=OHLCV for dataframe-based indicators. Top-level period controls returned bars after calculation and conflicts with explicit dates; it differs from a nested indicator's lookback period.

Declared output: timestamp, ticker, indicator_name, indicator_value. include_signals retains additional native outputs. output_value_semantics metadata explains status codes and *_index positions. A position is not a timestamp/price. Do not assume all values are continuous price measurements.

The illustrative RSI request follows the description's object convention; no success response was sampled. Constituent versus sector/index rules still apply. Unregistered indicators and complex derived analysis use discovery.

**Example request**:

```json
{
  "tickers": [
    "HPG"
  ],
  "indicators": [
    {
      "name": "rsi",
      "period": 14
    }
  ],
  "by": "1d",
  "period": 30
}
```

## get_bonds

[Full declaration and original provider guidance](declared/get_bonds.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `aggregate` | `Array<string> \| null` | No |
| `bond_tickers` | `Array<string> \| null` | No |
| `buy` | `boolean \| null` | No |
| `clean_price` | `boolean \| null` | No |
| `collateral` | `unknown \| null` | No |
| `coupon_type` | `string \| null` | No |
| `date_check` | `string \| null` | No |
| `dirty_price` | `number \| null` | No |
| `fields` | `Array<string> \| null` | No |
| `filters` | `Array<{ [key: string]: unknown; }> \| null` | No |
| `from_date` | `string \| null` | No |
| `from_percentage` | `number \| null` | No |
| `group_by` | `Array<string> \| null` | No |
| `industries` | `Array<string> \| null` | No |
| `issue_method` | `string \| null` | No |
| `issuer` | `string \| null` | No |
| `issuers` | `Array<string> \| null` | No |
| `late_payment_type` | `string \| null` | No |
| `method` | `string \| null` | No |
| `method_type` | `string \| null` | No |
| `metrics` | `Array<string> \| null` | No |
| `month` | `number \| null` | No |
| `offset` | `number` | No |
| `payment_date` | `string \| null` | No |
| `quarter` | `number \| null` | No |
| `related` | `boolean \| null` | No |
| `release_method` | `string \| null` | No |
| `remaining_duration_type` | `string \| null` | No |
| `sort_by` | `string \| null` | No |
| `sort_order` | `"asc" \| "desc"` | No |
| `status` | `unknown \| null` | No |
| `time_frequency` | `string \| null` | No |
| `time_range` | `string \| null` | No |
| `to_date` | `string \| null` | No |
| `to_percentage` | `number \| null` | No |
| `top` | `number` | No |
| `total_value_type` | `string \| null` | No |
| `trading` | `unknown \| null` | No |
| `trading_type` | `string \| null` | No |
| `year` | `number \| null` | No |
| `ytm` | `unknown \| null` | No |

Mode-based corporate-bond retrieval, filtering and simple aggregation. metrics selects a route, not arbitrary measures. Every input is optional in the bridge, but modes have conditional requirements. Choose the entity/dimension first, then a mode whose output supports it.

Declared output: normalized route-specific rows, with PARTIAL and coverage.missing_fields when requested fields are absent. Only an entitlement error was observed; no successful bond rows were verified. Default top/offset values and a complete closed mode enum are not encoded.

Read the bond deep dive for the mode matrix, allowed list fields, units, time semantics, conditional inputs, and contradictions.

**Example request**:

```json
{
  "metrics": [
    "list"
  ],
  "issuer": "VCB",
  "fields": [
    "bond_ticker",
    "issuer",
    "maturity_date"
  ],
  "top": 5
}
```

[Observed request and response](evidence/bond-entitlement-error.json). Compare the recorded request with any illustrative variant above.

## get_economy

[Full declaration and original provider guidance](declared/get_economy.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `cpi_scope` | `"inflation" \| "contribution" \| "all" \| null` | No |
| `data_type` | `string \| null` | No |
| `fdi_scope` | `"all" \| "provinces" \| "industries" \| "countries" \| "structure" \| "composition_by_country" \| "composition_by_industry" \| "composition_by_province" \| "overview" \| "registered_by_country" \| "registered_by_industry" \| "registered_by_province" \| null` | No |
| `fields` | `Array<string> \| null` | No |
| `filters` | `Array<{ [key: string]: unknown; }> \| null` | No |
| `from_date` | `string \| null` | No |
| `is_nominal` | `boolean \| null` | No |
| `is_value` | `boolean \| null` | No |
| `location` | `string \| null` | No |
| `metrics` | `Array<string>` | Yes |
| `month` | `unknown \| null` | No |
| `most_recent` | `boolean` | No |
| `offset` | `number` | No |
| `product` | `string \| null` | No |
| `quarter` | `unknown \| null` | No |
| `sort_by` | `string \| null` | No |
| `sort_order` | `"asc" \| "desc"` | No |
| `to_date` | `string \| null` | No |
| `top` | `number` | No |
| `topic` | `string \| null` | No |
| `year` | `unknown \| null` | No |
| `ytd` | `boolean \| null` | No |

System-wide macroeconomic data. Exactly one metrics mode per call is instructed, despite a string-array signature. Mode families: news, gdp_sector, gdp_province, gdp_spending, cpi, export_import, fdi, balance_payment, open_market, money_credit, exchange_rate, interest_rate, state_budget, manufacturing.

Route-specific constraints:
- gdp_province/gdp_by_province is annual; grdp_structure requires location.
- gdp_sector uses is_value for value versus growth, not composition; composition uses gdp_composition. Growth forces constant-price behavior.
- CPI distinguishes inflation/contribution/all and RTD/YoY/MoM/YTD.
- FDI scope selects geographic/industry/composition/registered-capital routes.
- money_supply_outstanding is monthly. It is not company-level bank ratios.
- other_bank_interest_rates uses from_date; state_bank_interest_rates uses year/month.
- state_budget_balances is annual; social_investment_capital is the other declared topic.
- manufacturing provides indices/growth, not physical product quantities.
- export/import routes distinguish product, location, trade balance and top groups; narrower industry-specific questions require discovery.

Keep most_recent=true for latest requests; explicit supported periods turn it off in the wrapper. Only pass time fields supported by the selected topic. Provider rows are documented to be cached for one hour, then locally filtered/sorted/projected/bounded.

Output is a result string with route-specific fields and declared PARTIAL/coverage metadata. Leave fields omitted until the route is known. See the original declaration for per-topic fields. Successful envelope not sampled; no group_by/aggregate inputs exist.

**Example request**:

```json
{
  "metrics": [
    "gdp_province"
  ],
  "topic": "gdp_by_province",
  "year": 2025,
  "data_type": "Value"
}
```

## get_funds

[Full declaration and original provider guidance](declared/get_funds.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `absolute` | `boolean \| null` | No |
| `allocation_type` | `"asset" \| "sector" \| null` | No |
| `asset_tickers` | `Array<string> \| null` | No |
| `big4_interest_rate` | `boolean \| null` | No |
| `fields` | `Array<string> \| null` | No |
| `filters` | `Array<{ [key: string]: unknown; }> \| null` | No |
| `frequency` | `string \| null` | No |
| `from_date` | `string \| null` | No |
| `fund_groups` | `Array<string> \| null` | No |
| `fund_structures` | `Array<string> \| null` | No |
| `fund_tickers` | `Array<string> \| null` | No |
| `fund_types` | `Array<string> \| null` | No |
| `holding_history_type` | `"contribution" \| "volume" \| null` | No |
| `holding_type` | `"current" \| "history" \| "stock_owners" \| "fund_holders" \| null` | No |
| `metrics` | `Array<string> \| null` | No |
| `month` | `number \| null` | No |
| `months` | `Array<number> \| null` | No |
| `most_recent` | `boolean \| null` | No |
| `offset` | `number` | No |
| `quarters` | `Array<number> \| null` | No |
| `sort_by` | `string \| null` | No |
| `sort_order` | `"asc" \| "desc"` | No |
| `statement` | `string \| null` | No |
| `to_date` | `string \| null` | No |
| `top` | `number` | No |
| `vn30` | `boolean \| null` | No |
| `vnindex` | `boolean \| null` | No |
| `year` | `number \| null` | No |
| `years` | `Array<number> \| null` | No |

Fund master/universe, profiles, NAV, performance, flows, holdings, allocation, risk, and reports. One metrics mode per call is instructed.

Mode rules:
- ticker_list is the master code list; universe is snapshot screening by NAV/performance/type.
- profile requires fund_tickers.
- nav/nav_data use route-specific frequency/date rules; Custom uses a date window. funds_nav requires fund_tickers/from_date and normalizes a wide provider table to date/fund_ticker/nav_per_share_adjusted.
- performance/top_nav/key_metrics/risk and allocation snapshots use year+month or most_recent.
- flow selects history, market flow, or snapshot statistics by arguments. Missing from_date can default to 30 days with a warning.
- holdings current is a snapshot; omitted fund_tickers may discover funds with holdings. History needs fund_tickers/from_date; volume outputs holding_volume, contribution outputs holding_weight.
- fund_holders/stock_owners require underlying asset_tickers, not fund identifiers; snapshot dates use year/month or most_recent, not from_date/to_date.
- allocation_type chooses asset versus sector; history requires fund_tickers/from_date.
- periodical reports require funds/statement/years, months OR quarters. If neither period selector is supplied, the wrapper documents months 1–12.
- Periodical statements: AssetReport/ProfitLossReport/PortfolioReport/OtherReport. Financial statements: BalanceSheet/IncomeStatement/CashFlow/Notes.

In universe, nav is total NAV/AUM in VND; nav_per_share is per certificate. fund_types are legal/trading classes (ETF/open/closed); fund_structures are strategies (equity/bond/balanced). holding_weight is portfolio weight; holding_ratio is ownership of the underlying asset. Most-recent snapshots are unsuitable for multi-period comparisons.

Output: result string with route-specific rows and declared partial-coverage metadata; successful envelope unverified. The description mentions group_by/aggregate but the exposed input signature contains neither.

**Example request**:

```json
{
  "metrics": [
    "universe"
  ],
  "fund_types": [
    "ETF"
  ],
  "fields": [
    "fund_ticker",
    "fund_name",
    "nav"
  ],
  "sort_by": "nav",
  "sort_order": "desc",
  "top": 5
}
```

## report_mcp_bug

[Full declaration and original provider guidance](declared/report_mcp_bug.md).

| Input | Visible type | Required at bridge? |
|---|---|---|
| `code` | `string` | No |
| `error_message` | `string` | No |
| `note` | `string` | No |

Side-effecting support tool for recording MCP/API issues. code, error_message and note are optional strings. No required content rule is exposed. Do not include credentials or unrelated conversation.

Output is declared as a result string; acknowledgement fields were not supplied. Not called during this documentation task. Issues were recorded locally, not submitted to support. A KimFI reporting interface should expose a typed report ID, timestamp and outcome.

**Example request** (not submitted):

```json
{
  "error_message": "Application error returned with outer isError=false",
  "note": "Inspect the nested status. No credentials included."
}
```
