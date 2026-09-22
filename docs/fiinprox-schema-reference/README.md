# FiinProX input/output schemas: reference for KimFI MCP design

**Snapshot date:** 22 September 2026

**Audience:** KimFI MCP designers, implementers, and reviewers

**Scope:** all 17 FiinProX tools exposed to this session; deeper corporate-bond contracts; comparison with KimFI's connected schema reference v4 and invariants v5.

## Read this first

FiinProX exposes a hybrid interface: narrowly scoped retrieval tools, broad domain tools selected by a mode, metadata discovery tools, and a Python execution sandbox. Its type signatures are only part of the contract. Important requirements—such as choosing exactly one selector, supplying a parameter only for certain modes, preserving units, and selecting the correct row grain—often live in descriptive text.

Most FiinProX tools declare an output of `CallToolResult<{ result: string }>`. The string may contain JSON, but the sandbox returned plain text. Discovery and detail instead expose structured objects. A caller must distinguish the outer tool result, the inner application status, and the financial meaning of the rows.

KimFI already has useful features that should be retained: closed domain/action routing described by its facades, explicit population scope, currency safeguards, diagnostics, provenance, and freshness checks. FiinProX is most valuable as a reference for discovery, route selection, field metadata, and provider-to-public transformations—not as a schema to copy unchanged.

## Documentation map

| Document | Contents |
|---|---|
| [Tool-by-tool reference](01-tool-reference.md) | Every input parameter's visible type and optionality; workflow dependencies, defaults, outputs, and request examples for all 17 tools |
| [Bond schema deep dive](02-bond-contract.md) | Mode matrix, list fields, provider contract, time/unit semantics, examples, and known conflicts |
| [KimFI design reference](03-kimfi-design.md) | Existing KimFI evidence, semantic crosswalk, proposed contracts, migration priorities, and acceptance checks |
| [Evidence index](04-evidence-and-gaps.md) | Sources, live probes, verification limits, and contradictions requiring resolution |
| [Declaration snapshots](declared/get_bonds.md) | Original host-visible tool descriptions and bridge signatures; one file per tool |
| [KimFI schema snapshot](evidence/kimfi-schema-v4.json) | Connected reference document, including legacy schemas and canonical vocabulary |
| [KimFI invariant snapshot](evidence/kimfi-invariants-v5.json) | Business rules and diagnostics from the connected service |
| [KimFI vocabulary snapshot](evidence/kimfi-vocabulary-v5.json) | Term mappings and capability caveats |

## Evidence labels

- **Declared:** stated in a connected tool description/signature or reference document. This does not prove implementation behavior.
- **Observed:** returned by a bounded live probe during this documentation task.
- **Proposed:** a recommended KimFI design; not a claim about today's service.
- **Unverified:** not established by the available declaration or runtime evidence.

This is not a server-source audit or a raw MCP `tools/list` schema export. The host supplied TypeScript bridge signatures and tool descriptions. Consequently, restrictions absent from those signatures—such as numeric bounds, string formats, unknown-property handling, or server-side coercion—cannot be assumed absent from the underlying server.

Successful bond data could not be sampled: both direct and sandbox probes returned entitlement errors. No financial values or successful bond rows have been invented. All request examples outside the evidence files are illustrative.

## 1. Three layers of schema

| Layer | What it describes | Example |
|---|---|---|
| Host-visible tool input | Argument names and types accepted by the exposed bridge | `get_bonds({ metrics?: string[], issuer?: string, ... })` |
| Application/provider contract | Mode requirements, source method, aliases, post-processing, output grain | `metrics=['list']` selects the bond list route; an issuer name can be filtered locally |
| Tool result and financial payload | Transport blocks, nested status, rows, metadata, field meaning | `structuredContent.result` contains JSON with `success` and `data.status` |

For example, every `get_bonds` input is optional in the visible signature. That does **not** make every combination meaningful. The declared `price_ytm` mode requires a bond identifier and dirty price. Likewise, `get_equity_snapshot` has three optional selectors, but the description requires exactly one of them.

### Omitted, null, empty, and zero are different

A `?` marks an optional argument in the bridge. `| null` permits explicit null at that layer. Neither tells you the provider's default or guarantees that null and omission behave identically.

Do not substitute:
- an empty identifier list for an omitted selector;
- zero for a missing amount or rate;
- `false` for an unknown flag;
- a default period for a user-specified period that the chosen route cannot support.

Many defaults are documented only in prose. The tool reference identifies them; unspecified defaults remain unspecified.

## 2. How requests move through FiinProX

### Direct retrieval

Use the direct tool when the requested entity, metric, period, and row grain match its documented route. Common examples are a bond list, equity snapshot, raw OHLCV series, or fund NAV series.

The broad bond/economy/fund tools may normalize provider column names and apply local filters, sorting, projection, and bounds. They do not all expose the same post-processing features: only `get_bonds` visibly exposes `group_by` and `aggregate`.

### Metadata-assisted financial requests

| Intent | Required chain | Output of discovery becomes |
|---|---|---|
| Screen stocks | `search_filters → execute_screening` | Indicator IDs, scale multipliers, and period selectors |
| Retrieve statements/ratios | `search_fundamental_fields → get_fundamental_data` | Data type, statement type, and company-type-specific field path |
| Resolve a natural-language sector | `search_sector_code_by_name → relevant domain tool` | An industry code; not a stock list |
| Retrieve sector/index constituents | `get_tickerlist → retrieval tool` | Individual member tickers |

These identifier systems are separate. A fundamental field path is not a screening indicator ID. A sector code passed to a price tool means that sector's own series, not every constituent's series.

### General discovery and execution

1. `search_tool_candidates` returns cache/function candidates and routing metadata.
2. The caller evaluates whether a candidate matches the intended dimensions and measures.
3. `get_tool_detail` returns parameters, output descriptions, and execution rules for the selected candidate.
4. `execute_api` runs a short Python call using the preloaded client and prints the result.

Discovery is not data retrieval. The observed discovery payload explicitly included `ready_to_answer:false` and `required_next_tool`. Its automatic top suggestion was a bank-portfolio aggregate, while the second candidate was an issuer bond list. This demonstrates why semantic ranking must be checked against intent rather than followed blindly.

## 3. Output envelopes and decoding

### A. JSON encoded in a result string

Observed on sector discovery, field discovery, ticker lists, screening metadata, and the direct bond error:

```json
{
  "content": [{"type": "text", "text": "<payload text>"}],
  "structuredContent": {"result": "<payload text>"},
  "isError": false
}
```

The placeholder above represents a string, not a nested object. For JSON-returning tools, parse it once and inspect its actual shape.

The ticker-list payload contained:

```json
{
  "success": true,
  "data": {
    "status": "OK",
    "rows": [{"ticker": "ACB"}],
    "errors": [],
    "warnings": [],
    "metadata": {
      "coverage": {
        "has_gap": false,
        "missing_fields": [],
        "returned_fields": ["ticker"]
      }
    },
    "field_dictionary": {
      "ticker": {"description": "…", "unit": null}
    }
  }
}
```

This is a shortened structural example from the [observed ticker-list response](evidence/tickerlist.json), which returned 30 rows. The field dictionary also described an optional `name` field that was not returned. A dictionary entry therefore does not prove row-level availability.

### B. Structured discovery output

`search_tool_candidates` and `get_tool_detail` returned application objects directly in `structuredContent`, with an equivalent serialized text block. Do not assume that `structuredContent.result` exists on these tools.

### C. Sandbox text output

The sandbox's declared `result: string` was **not JSON** in the observed call:

```text
Success: False
Stdout:

Stderr:
<provider entitlement message>
```

A universal `JSON.parse(result)` strategy will fail here. Preserve text when the payload is not JSON. Prefer structured output for new KimFI interfaces.

### D. An application error can arrive with isError=false

The [bond probe](evidence/bond-entitlement-error.json) returned outer `isError:false`, but inner `success:false`, `data.status:'ERROR'`, empty rows, and an access-entitlement explanation.

A robust adapter should:
1. Check the outer error signal.
2. Select structured content where available; otherwise inspect the text blocks.
3. Decode JSON only where valid.
4. Check application `success`, status, errors, and coverage.
5. Interpret rows only after those checks.
6. Keep empty-success, partial-data, and failed-access outcomes distinct.

This sequence is a proposed consumer strategy based on observed responses, not a claim about undocumented server internals.

## 4. Coverage, limits, and semantics

`OK` and `ERROR` were observed. `PARTIAL` is declared for missing requested fields in several direct tools. The complete status enum is not exposed.

`metadata.coverage.missing_fields` describes missing requested columns; it does not necessarily describe missing observations or missing values within an existing column. Similarly, `has_gap:false` is not proof that all market entities, all dates, or every provider are represented.

`top`, `offset`, and `export_limit` have tool-specific meanings. Ticker lists and raw market-statistics tools do not accept these arguments. The visible schemas do not establish a universal maximum, stable pagination order, snapshot consistency, or total-row counter.

Request the intended population before aggregation; aggregate before ranking; and distinguish returned rows from all matched rows. Never calculate a market total from a truncated preview.

## 5. What this reference verifies

The package includes the exact declarations for all 17 tools, a complete bridge input inventory, eight live FiinProX probes, and three KimFI reference snapshots. It verifies schema observations and documentation consistency—not all provider routes, business calculations, or successful bond data.

See [evidence and gaps](04-evidence-and-gaps.md) before using an illustrative request in production.
