# Consensus Design and Binding Matrix

## Evidence boundary

The leader and each validator independently fetch the same sealed artifact
URLs. Each source must return a direct successful response from the exact
authority host; explicit 3xx responses, timeout, server failures, oversized bodies, and
unparseable responses are failures rather than alternative evidence.

The implementation canonicalizes a bounded extract from each source and places
it in compact JSON as data, never as executable prompt instructions. The fixed
prompt asks only for the five mismatch bits and one vote enum. It does not ask
for legal conclusions, confidence values, vote counts, or prose used by state.

The leader returns a compact decision tuple:

```text
(trace_status, mismatch_mask, missing_mask, vote_outcome)
```

The validator first rejects non-`Return`, malformed, out-of-range, or
cross-field-inconsistent leader output. It then independently fetches evidence,
derives its own tuple under the same closed taxonomy, and accepts only an exact
match of every stored field. No unverified reason code is stored.

## Cross-field invariants

- `SUPPORTED` requires both masks to be zero.
- `PARTIALLY_SUPPORTED` requires mismatch mask zero and a nonzero mask made only
  of optional roles.
- `MATERIAL_MISMATCH` requires a nonzero mismatch mask and no unresolved source.
- `NO_PUBLIC_TRACE` requires at least one missing essential role.
- `UNRESOLVED` is used for operational or semantic indeterminacy, never as a
  substitute for a confirmed missing official record.
- A derived vote enum must agree with resolution wording and minutes; otherwise
  `VOTE_OUTCOME` is set.
- A new assessment revision is exactly the sealed case revision; stale and
  replayed challenges are rejected.

## Consensus Binding Matrix

| Field | Source | Stored | Downstream effect | Validator check | Binding | Differential test |
|---|---|---:|---|---|---|---|
| `trace_status` | derived tuple | yes | oracle result | rederive precedence | exact enum | partial vs mismatch |
| `mismatch_mask` | agenda/minutes/resolution | yes | remediation route | rederive each bit | exact integer bits | action vs condition |
| `missing_mask` | fetch result + role policy | yes | completeness signal | exact availability policy | exact integer bits | minutes vs resolution missing |
| `vote_outcome` | minutes + resolution | yes | downstream fact | rederive wording outcome | exact enum | approved vs deferred |
| `revision` | sealed lifecycle | yes | history identity | deterministic lifecycle | deterministic | stale challenge |
| manifest hash | sorted sealed artifacts | yes | evidence epoch | deterministic serialization | deterministic | changed URL/hash |

## Required tests

- create, draft add/replace, duplicate role/URL, seal preconditions, and
  immutability after seal;
- host/HTTPS/day/hash/length validation and owner checks;
- each status, each mismatch bit alone and in combinations, and every missing
  bit;
- approved/rejected/deferred/no-recorded/unknown votes and their conflicts;
- timeout, 404, redirect, malformed HTTP/LLM output, and hostile transcript;
- same-status differential consensus failures for mask, vote, and revision;
- validator dissent, non-return leader result, strict mocks, and serialization;
- challenge authorization, stale revision, idempotency, immutable history, and
  reassessment.

## Tooling baseline

Use Python 3.12+ with `genlayer-test==0.29.2`, `genvm-linter==0.11.0`, and the
exact runtime dependency published in the current GenLayer contract docs:
`py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
The required local sequence is lint, Direct Mode with
strict web/LLM mocks, then consensus validator tests. `gltest --network
studionet` is reserved for the post-PRE-DEPLOY integration stage.
