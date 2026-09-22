# FiinProX schema reference for KimFI: approved documentation design

Date: 2026-09-22

The user approved a complete reference covering all exposed FiinProX tools, deeper bond examples, and KimFI MCP design recommendations.

## Delivered structure

- [Start here: schema guide](../../fiinprox-schema-reference/README.md)
- [All 17 tools and 174 input parameters](../../fiinprox-schema-reference/01-tool-reference.md)
- [Corporate-bond modes and provider contracts](../../fiinprox-schema-reference/02-bond-contract.md)
- [KimFI design comparison and recommendations](../../fiinprox-schema-reference/03-kimfi-design.md)
- [Evidence, conflicts and limitations](../../fiinprox-schema-reference/04-evidence-and-gaps.md)

## Scope and success criteria

Document the host-visible input/output declarations for every exposed FiinProX tool. Explain routing, conditional requirements, envelopes, errors, units, nulls, coverage and financial row grain. Preserve primary declaration snapshots and bounded runtime evidence. Compare them with KimFI's connected versioned references. Clearly mark proposed contracts, unexecuted examples and unavailable evidence.

The work is documentation only. No KimFI code, source data, connected account configuration or production service was changed. Successful bond retrieval is unverified because both probed data routes denied entitlement.

## Review

The approved design was expanded into the linked reference package and checked for coverage, syntax, links and inconsistent claims. Further KimFI implementation planning is outside this documentation request and should follow review of the recommendations.
