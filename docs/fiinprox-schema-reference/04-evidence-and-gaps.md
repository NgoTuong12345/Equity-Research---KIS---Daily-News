# Evidence, limitations, and contract conflicts

Captured on 22 September 2026 through the connected FiinProX and KimFI tools. No external web summary was used as a substitute for the actual connected interfaces.

## 1. Evidence sources

| Source | What it proves | What it does not prove |
|---|---|---|
| 17 files in declared/ | Tool descriptions and bridge input/output declarations visible in this session | Exact underlying JSON Schema, server source, full provider implementation |
| Eight FiinProX response fixtures | Actual returned payloads for the recorded requests | Behavior for all tools/modes/accounts/dates |
| KimFI schema v4 | Published reference structure, legacy typed schemas and canonical vocabulary lists | A complete current facade schema where the reference does not provide one |
| KimFI invariants v5 | Published financial correctness rules | Independent audit of every implementation path |
| KimFI vocabulary v5 | Published term-to-field mappings and capability caveats | Evidence that all referenced ingested tables have callable tools |

Files in declared/ preserve original prose, including contradictions. The annotated documents flag conflicts rather than silently rewriting the source.

## 2. Live probe inventory

| Probe | Request intent | Observed result | Fixture |
|---|---|---|---|
| get_bonds | One VCB list row with five selected fields | Application ERROR, access entitlement denied; outer isError=false | [bond error](evidence/bond-entitlement-error.json) |
| search_sector_code_by_name | Banking at level 2, one result | OK; BANKS_L2, ICB 8300 | [sector](evidence/sector.json) |
| search_fundamental_fields | ROE, one candidate | Success; ratios mapping for COMPANY/SECURITIES/INSURANCE | [field search](evidence/fundamental_fields.json) |
| search_filters | P/E, one candidate | Success; diluted P/E ID 8014, Daily, multiplier 1 | [screening metadata](evidence/filters.json) |
| get_tickerlist | VN30 members | OK; 30 rows, returned field ticker | [ticker list](evidence/tickerlist.json) |
| search_tool_candidates | Bond list/issuer/outstanding/coupon | Structured metadata; two candidates; first was not the intended bond-list grain | [discovery](evidence/candidates.json) |
| get_tool_detail | Selected issuer bond-list candidate | Structured parameters/output_desc/execution rules | [detail](evidence/detail.json) |
| execute_api | Issuer bond-list call, related=false, print two rows | Plain-text failure: missing/expired access entitlement | [sandbox](evidence/execute.json) |

A KimFI schema reference call without link_id returned a host routing error. Retrying with the selected connector ID returned the schema. The substantive schema, invariants, and vocabulary are preserved without connection-account IDs.

No bug-report tool was invoked. No exports were requested. These fixtures are documentation evidence, not trading data downloads or a full integration test suite.

## 3. Verified output facts

1. Most FiinProX declarations use structuredContent.result as a string, not a typed financial object.
2. Some such strings are JSON; execute_api's sampled string was plain text.
3. Discovery/detail use structured objects directly.
4. An outer isError=false can contain an application-level error.
5. Ticker-list output can include provider metadata and a field dictionary.
6. A field dictionary can describe a field absent from actual returned rows.
7. Discovered field IDs and paths carry business-specific context; the top match is not universally appropriate.
8. Provider schema metadata can be available when underlying data entitlement is unavailable.

## 4. Conflicts and ambiguities to retain in the design review

| Finding | Evidence | Documentation decision / KimFI lesson |
|---|---|---|
| Scalar ticker prose versus array signature | fetch_trading_data | Use array at this bridge; publish one unambiguous accepted shape |
| Global optional arguments versus mode-specific requirements | get_bonds, get_equity_snapshot, get_market_statistics | Distinguish syntax from semantic preconditions; use closed action branches |
| Open string metrics arrays despite one-mode guidance | get_economy, get_funds | Prefer a single enum/discriminator or enforce maxItems=1 |
| String-valued details instead of typed parameter schema | get_tool_detail.parameters | Metadata retrieval is helpful but not full machine validation |
| Unsupported list fields reappear in later guidance | get_bonds mentions source_url/public_date/release_method and extra coupon/rating fields after an explicit exclusion/allowlist | Prefer explicit allowlist until a route-specific schema proves support |
| Defaults and units vary by bond route | VND provider amounts; VND late_payment; billion-VND debt_restructuring | Never infer global monetary scale |
| x>=12 labelled ">12%" | Bond coupon bucket example | Correct boundary labels and publish inclusivity |
| Missing-value zero filling before averages | Provider detail logic_constraints | Preserve null semantics; averaging zero-filled unknown rates is misleading |
| AND screening plus company-type variants | execute_screening | Verify intended union/intersection behavior before relying on it |
| camelCase versus snake_case filter names | execute_screening examples and argument comment | Publish a canonical typed filter and explicit aliases |
| Epsilon-based strict comparison | execute_screening comment | Use explicit gt/lt operators |
| group_by/aggregate mentioned but not in signature | get_funds | Do not send nonexistent public arguments |
| Provider-only otc appears in output | get_tickerlist metadata | Internal arguments are not automatically public capabilities |
| Exact metadata dictionary differs from prose label | search_fundamental_fields keyword_en observed | Generate docs from schemas/fixtures |
| “No late-payment-day data” versus discovery fallback advice | get_bonds description | Treat direct-mode absence separately from any wider catalog search; do not assert global availability |
| Discovery top candidate/entity mismatch | Sample generic bond query | Validate intent and row grain, not just similarity score |
| KimFI current descriptions versus legacy detailed schemas | schema v4 plus current facades | Publish exact current branch schemas with explicit compatibility notes |
| KimFI link_id bridge optional but host demanded it | kimfi_context first reference call | Separate host connector routing from domain schemas |

## 5. Unknowns not disguised as facts

- Exact raw MCP inputSchema/outputSchema for FiinProX tools, including additionalProperties policies and coercion.
- Successful bond list/provider responses under this account.
- Complete bond mode enumeration and every mode's field-level output schema.
- Per-field types, nullability, units and currency guarantees for every broad domain route.
- Exact FiinProX date-bound inclusivity, pagination stability, count semantics and query snapshot consistency.
- Default top/offset/max limits where not stated.
- Full output/error variants for uncalled tools.
- All indicator-specific nested parameter contracts.
- Exact accepted alias sets where prose and examples disagree.
- Complete current KimFI query/analyze branch schemas through this host.
- Whether all declared behavioral rules are enforced server-side.

These limits do not prevent documenting the interface. They determine which statements are declarations, observations, or proposals.

## 6. How to refresh this package

1. Capture the current exposed tool declarations and compare argument names/types.
2. Retrieve versioned KimFI schema, vocabulary and invariants references.
3. Re-run only bounded read probes appropriate to the available entitlement.
4. Preserve exact requests and responses, with date and source labels.
5. Update the annotated tables and conflict register; do not silently erase unresolved differences.
6. Validate embedded JSON examples, local links, field inventories and version labels.
7. When successful bond access is available, add one bounded list response and one aggregate/provider example with units/coverage; do not infer their shape from the error fixture.
8. Keep proposed KimFI contracts clearly separated from deployed schemas.

## 7. Review status

The author reviewed tool coverage, input optionality, envelope distinctions, financial units and field mappings. The package's input tables are derived from all 17 captured bridge declarations, totaling 174 input parameters across tools. JSON examples and evidence are checked during document verification.

This is a documentation deliverable. Proposed implementation acceptance checks appear in the KimFI design reference; they are not claimed as executed server tests.
