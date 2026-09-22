# KimFI MCP design reference informed by FiinProX

All recommendations in this document are **proposed**, unless explicitly marked as observed or declared current behavior. No KimFI implementation or deployment was changed.

## 1. What KimFI already exposes

Sources: connected [schema v4](evidence/kimfi-schema-v4.json), [invariants v5](evidence/kimfi-invariants-v5.json), [vocabulary v5](evidence/kimfi-vocabulary-v5.json), and the host-visible facade descriptions.

| Existing surface | Declared role | Design value to retain |
|---|---|---|
| kimfi_context | reference, source search/fetch, freshness | Explicit vocabulary, invariants and data-state inspection |
| kimfi_query | Corporate-bond discovery/resolution/retrieval; government-bond trades | Bounded domain/action routing; disjoint identifier namespaces |
| kimfi_analyze | Bond aggregation/ranking, repurchase-disclosure analytics, cash-flow calculation | Business operations rather than arbitrary sandbox code |
| kimfi_read | Navigate documents, read selected text pages or page images | Traceable evidence navigation with page limits |
| kimfi_export | Bounded exports and artifact delivery | File metadata, expiry and availability outcomes |
| kimfi_create_chart | Explicit category/measure mappings and transforms | Financial measure types, units, diagnostics |
| search / fetch | Citable source discovery/retrieval | Source-level citation workflow, distinct from bond-row retrieval |

This is a comparison inventory, not an exhaustive replacement reference for all KimFI parameters. The exposed bridge represents kimfi_query and kimfi_analyze inputs as unions of unknown types, even though their descriptions say the branches are closed. That is a **schema visibility problem at this host surface**, not proof the server accepts arbitrary input.

### Important current-schema caveat

The schema reference contains detailed legacy CbondQuery/CbondBuybacksQuery schemas under domains, plus separate canonicalMeasures, canonicalDimensions, canonicalFilterFields, canonicalBuyback* arrays and current action lists.

For example:
- Legacy measure outstanding_amount corresponds to canonical amount_outstanding.
- Legacy issued_amount corresponds to canonical analytic measure issue_size, with scope restrictions described in the vocabulary.
- Current facades use domain/action, while the detailed legacy examples are not automatically complete current facade requests.
- The schema reference's action list and facade descriptions do not enumerate exactly the same features: the query description additionally mentions pilot ownership and prepare; the analyze description additionally mentions cashflow/prepare.

Therefore **do not paste a legacy querySchema example into a current facade without obtaining its exact current branch schema**. Recommendation: publish the complete current action-discriminated input and output schemas and mark legacy forms separately.

### Host routing versus domain inputs

The initial kimfi_context reference request omitted link_id, which is optional in the visible declaration, and the host returned: “This app tool requires a non-empty string link_id argument.” Supplying the selected connection ID allowed the reference call to succeed.

This is observed host routing behavior. It does not establish that link_id belongs in KimFI's business schema. The query facade description explicitly says its closed branches contain no session/link/citation ID field. Keep connector account selection separate from financial domain arguments; document the adapter boundary rather than adding routing keys indiscriminately.

## 2. Patterns to adopt, preserve, and avoid

| FiinProX pattern | Benefit | KimFI recommendation |
|---|---|---|
| Discovery before complex execution | Avoids inventing endpoints and fields | Adopt versioned capability discovery with supported input/output schemas |
| Field/indicator catalogs | Carries periods, units, entity type and mappings | Preserve explicit metric metadata; use separate IDs for separate semantics |
| Dimension-first route selection | Prevents asking an aggregate endpoint for missing entities | Expose row grain and supported dimensions per action |
| Direct domain routes | Efficient common operations | Keep focused KimFI actions for core use cases |
| Provider aliases normalized to public fields | Shields consumers from source naming | Maintain a versioned alias map with semantic validation |
| Missing-field coverage | Makes partial results visible | Extend to row/value/population coverage, not just column presence |
| Broad optional parameter objects | Reduces tool count | Prefer closed action branches instead of incompatible combinations |
| JSON inside result strings | Flexible compatibility | Prefer typed structuredContent and an optional human-readable summary |
| Prose-only constraints | Explains tricky business logic | Generate prose and validation from a shared contract where possible |
| Generic Python sandbox | Handles unusual analysis | Keep core KimFI analysis server-side; evaluate any sandbox separately |
| Numeric epsilons for strict bounds | Approximates a missing operator | Model gt/gte/lt/lte explicitly |
| Silent mode-specific defaults | Can make requests shorter | Return the resolved request and explicit material defaults |
| Broad fillna(0) guidance | Simplifies arithmetic | Preserve missingness and publish valid-value counts |

KimFI's current currency, source provenance, scope, and freshness safeguards are valuable improvements over what can be established from FiinProX's exposed signatures. Retain them.

## 3. Semantic crosswalk: compare before renaming

This table is a conceptual mapping, not a safe mechanical field conversion.

| FiinProX concept | KimFI concept seen in references | Conditions before mapping |
|---|---|---|
| bond_ticker | bond_code / trading_code / isin | Resolve identity and domain; an issuance code is not automatically a trading code |
| issuer / issuer equity ticker | issuer_name and resolved issuer identity | Preserve identifier type and related-company scope |
| outstanding_value | amount_outstanding; legacy outstanding_amount | Match currency, scale, population and observation basis |
| issue_value | issue_size; legacy issued_amount | Match issuance event/flow definition; canonical issuance is private-placement scope-pinned in vocabulary |
| current_coupon_rate | No established direct equivalent to issuance rate | Do not map to coupon_rate_at_issue |
| first_coupon_rate | initial disclosed/Year-1 rate | Confirm dates, structure and source evidence |
| float_interest_spread | coupon_spread_bps | Establish source unit before converting to basis points |
| term / duration | issue-to-maturity term | Provider duration is months in sampled detail; do not assume financial duration |
| remaining_years | remaining_term_years | Align as-of date and day-count/time convention |
| active_status_name | circulation_status / public registration status | Use segment-specific status basis; maturity alone does not define live |
| trading_status_name | trading_registration_status / trading venue | Keep separate from circulation |
| late_payment | No direct equivalent established | Preserve rolling-year amount and combined principal/interest meaning |
| debt_restructuring | No direct equivalent established | Monetary one-year measure, not a boolean or issuance purpose |
| buyback_transactions | repurchase_disclosures | Disclosure evidence is not automatic proof of settlement |
| ytm | Vocabulary explicitly says no YTM for its coupon analytics | Do not rename a coupon rate as yield or imply unsupported pricing |
| source_url from arbitrary list prose | source_refs / document/page evidence | FiinProX list explicitly excludes source_url; keep citations evidence-based |

## 4. Proposed input architecture

Keep a small set of public facades, with **one closed discriminated branch per action**. Separate selection, measurement, and presentation concerns. This does not require one MCP tool per provider endpoint.

Each branch should declare:

1. Identity and namespace: corporate/government domain; issuer ID versus bond issuance/trading ID.
2. Population: market segment and live/all scope, including the segment-specific status basis.
3. Time: date axis, interval inclusivity, period grain, observation basis and timezone.
4. Measures/dimensions: supported combinations and aggregation meaning.
5. Bounded selection: filters, sort/rank, result limit and pagination semantics.
6. Preconditions: required fields, incompatible fields and entitlement/capability requirements.
7. Output variant: row grain, result columns, units and diagnostic codes.

### Illustrative proposed schema fragment — not the deployed KimFI schema

This example shows how an action-specific input can enforce requirements without admitting unrelated arguments. It is intentionally small; it is not a full market analytics schema.

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "domain": {"const": "cbond"},
    "action": {"const": "aggregate_bonds"},
    "universe": {"enum": ["live", "all"]},
    "measures": {
      "type": "array",
      "minItems": 1,
      "maxItems": 2,
      "uniqueItems": true,
      "items": {"enum": ["bonds", "amount_outstanding_vnd"]}
    },
    "dimensions": {
      "type": "array",
      "maxItems": 2,
      "uniqueItems": true,
      "items": {"enum": ["issuer_name", "industry"]}
    },
    "limit": {"type": "integer", "minimum": 1, "maximum": 500}
  },
  "required": ["domain", "action", "universe", "measures"]
}
```

The full schema should add explicit segment selection, monetary conversion and status semantics. A declared default is not a substitute for publishing the resolved value actually used.

### Filters need typed branches too

Use operator-specific shapes: eq takes value, in takes values, range takes bounds, isNull takes neither. Reject meaningless mixtures rather than silently ignoring extra keys. Enforce value types from the chosen field's metadata.

Current KimFI reference: analytics dateRange is lower-inclusive/upper-exclusive; _after/_before-style parameters are documented as inclusive on both ends. Expose these differences in machine-readable metadata or converge them in a versioned change.

Do not implement strict comparison as threshold +/- 1e-10. Explicit comparison operators preserve intent for money, rates, floats and integers without arbitrary rounding behavior.

## 5. Proposed output architecture

Prefer one structured application envelope with action-specific data. Keep tool execution outcome separate from data quality.

| Proposed field | Meaning |
|---|---|
| schema_version | Public contract version |
| outcome | success, needs_clarification, or error |
| trust_status | ok, partial, or error; preserve KimFI's existing quality vocabulary |
| domain / action | Executed business operation |
| query_time | Request execution timestamp, explicitly zoned |
| observation_basis | Data date/as-of/period basis, separate from query_time |
| applied | Resolved scope, filters, periods, defaults and limits |
| data | Action-specific typed result |
| coverage | Matched/returned counts, missing values/fields, truncation and scope limitations |
| field_dictionary | Data type, unit, scale, currency and measure kind |
| diagnostics | Stable code, level, path, message and fix |
| source_refs | Citable source references with evidence scope |
| next_steps | Bounded follow-up hints; not arbitrary commands |

KimFI already declares many of these concepts. This table proposes a consistent composition, not a mandate to rename every existing field. Its existing as_of field is documented as a Vietnam query date, not source-data freshness; that distinction should stay explicit.

For an empty successful result, return success with zero matched rows and resolved scope. For lack of entitlement, return an error code such as ENTITLEMENT_REQUIRED; do not encode it as an empty market. For partial fields, include useful rows and quality diagnostics. These example codes are proposed, not claimed current codes.

A response schema should not let success/error branches contradict one another. Consumers should not need to parse localized error prose to determine retryability.

### Field metadata

For each numeric field, document:
- Unit and scale: VND versus VND billion; percent versus fraction; basis points versus percent.
- Currency origin and any applied conversion rate/date/source.
- Measure kind: stock, flow, rate, price, ratio, count or index.
- Valid aggregation: sum, weighted average, arithmetic average, last observation, or none.
- Null meaning: unavailable, not applicable, unresolved, or invalid source.
- Weighting basis and denominator coverage for weighted averages.
- Date basis and source provenance.

These prevent numerically valid but economically invalid answers.

## 6. Business invariants to keep executable

Current KimFI references explicitly establish:

- Corporate and government bond codes occupy different namespaces.
- Live scope follows circulation/registration status, not a maturity-date test.
- Amounts require face value times quantity; quantities alone do not measure market value.
- Mixed currencies must not be summed without a stated conversion policy.
- Trading registration and issuance circulation are separate axes.
- Outstanding is a stock; issuance is a flow.
- Public-segment outstanding-stock figures are unavailable in the described scope.
- Rating results are not comparable across agencies.
- Null coupon is not verified zero coupon.
- Analytics FX conversion prefers VCB transfer-buy rates, with the documented earlier-date central-bank fallback.
- Empty results must be qualified by scope and freshness.

Implement these in validation/analytics and return diagnostics. Natural-language tool instructions are useful reinforcement, not sufficient enforcement.

The vocabulary says principal/interest payment extraction and government auction ingestion exist without corresponding read tools. A crawled table is not the same as an exposed capability. Similarly, cash-flow model availability must not be represented as evidence of actual payments.

## 7. Recommended design priorities

| Priority | Change | Completion criterion |
|---|---|---|
| 1 | Publish exact current facade branch schemas | Every domain/action has a current input/output schema; no unknown-only branch at the consuming host |
| 1 | Separate canonical and legacy contracts | Examples validate against their named version; retired forms cannot be mistaken for current requests |
| 1 | Normalize success/error/partial outcomes | Entitlement, empty data, missing fields and source failure have unambiguous typed outcomes |
| 1 | Attach financial semantics | Every amount/rate/tenor field has units, currency and time basis |
| 2 | Add capability and row-grain discovery | Caller can tell whether a route contains issuer/bond/date dimensions before execution |
| 2 | Generate documentation from contract metadata | Parameter tables, descriptions and validators share authoritative definitions |
| 2 | Strengthen coverage and pagination | Consumers can detect truncation and avoid totals from partial previews |
| 2 | Formalize provider alias mappings | Aliases are tested for meaning, units, scope and availability |
| 3 | Add versioned request/response fixtures | Representative behavior is reproducible across releases |
| 3 | Define optional extensibility separately | Any code-execution feature has a separate justified contract; not needed for core analytics |

This task delivers a design reference, not an implementation plan or rollout. Changes to KimFI should be scoped separately after review.

## 8. Proposed acceptance checks

These are tests to add when implementing the design; they were not run against a changed server.

| Case | Expected behavior |
|---|---|
| Wrong field for selected action | Reject with field path and supported alternatives |
| Missing conditional input | Reject before provider call |
| Invalid date shape or reversed range | Clear date validation diagnostic |
| Exact boundary date | Matches documented inclusive/exclusive rule |
| Strict > or < numeric threshold | Correct without epsilon substitution |
| Missing coupon versus verified zero | Distinct outputs and aggregation denominators |
| Currency mixture | Group or convert explicitly; never silently total |
| Issuer ranking from bond records | Aggregate whole selected population before top-N |
| Result truncation | Matched/returned counts and truncation flag |
| Provider access denial | Typed error, not zero-data success |
| Missing requested field | Partial outcome with precise coverage |
| Issuance code versus trading code | Resolve by namespace; do not guess by prefix |
| Metadata field advertised but absent | Distinguish catalog existence from returned-column coverage |
| Contract and generated documentation drift | Build/check fails with actionable differences |

A useful review artifact is a matrix of every action, branch schema, row grain, units, examples, and error variants. This reference supplies the FiinProX side and the available KimFI comparison evidence.
