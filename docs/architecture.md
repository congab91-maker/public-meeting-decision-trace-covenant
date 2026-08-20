# Architecture: Public Meeting Decision Trace Covenant

## Scope and vocabulary

One case represents one meeting, one agenda item, and one declared resolution.
The contract records a trace result; it is not a court, a quorum checker, or a
truth assessor. A case accepts at most four official artifacts:

| Artifact type | Bit | Essential | Purpose |
|---|---:|---:|---|
| `AGENDA` | 1 | yes | states the authorized agenda scope |
| `MINUTES` | 2 | yes | records deliberation and vote context |
| `RESOLUTION` | 4 | yes | states the adopted/rejected/deferred result |
| `ANNOUNCEMENT` | 8 | no | records a later official statement |

The initial public-source target is Seattle City Council's official Legislative
Information Center (`seattle.legistar.com`), linked by the Office of the City
Clerk. `agenda_item_hash` commits to the complete raw bytes of the AGENDA
artifact, not to an extracted agenda-item fragment. Exact source bytes and
SHA-256 values are intentionally captured only
immediately before the on-chain demo, because changing public documents must not
be represented by a stale hash.

## State

`MeetingCase` owns the authority host, meeting day, agenda-item commitment,
current revision, lifecycle, and sealed manifest. `Artifact` stores only the
role, canonical HTTPS URL, and the caller-supplied SHA-256 commitment. A
`TraceAssessment` stores the exact decision fields for the current revision.
Historical assessments are append-only records keyed by case and revision.

The implementation uses typed `TreeMap` storage collections and no Python
`dict` or `list` storage. Concrete GenVM type syntax is verified against the
installed pinned runtime during code implementation.

## Lifecycle and authorization

```text
DRAFT --seal_case--> SEALED --assess_trace--> ASSESSED
                                     |                 |
                                     +--challenge_trace-+
                                                       v
                                                   CHALLENGED
                                                       |
                                           seal_case + resolve_challenge
                                                       v
                                                   REASSESSED
```

- `create_meeting_case`: any caller creates a unique case and becomes owner.
- `add_artifact`: owner only, only in `DRAFT` or the active `CHALLENGED` revision.
- `seal_case`: owner only; requires all three essential roles exactly once.
- `assess_trace`: permissionless after sealing; cannot overwrite an assessment.
- `challenge_trace`: owner only; requires the currently assessed revision. It
  opens the next revision and clears only that revision's working artifacts.
- `resolve_challenge`: permissionless after the challenge revision is sealed;
  it creates the next immutable assessment.

The brief's `new_manifest` hash is derived at seal time rather than accepted as
the sole challenge input: a hash alone cannot give validators fetchable URLs.
This preserves the intended manifest commitment while retaining verifiable
replacement artifacts.

## Input policy

- Case IDs: 1-64 ASCII characters, unique.
- `authority_host`: lowercase DNS host, 1-253 characters; no scheme, port,
  path, or user-info.
- Meeting day: exact `YYYY-MM-DD`, bounded to a reasonable public-record range
  chosen in implementation tests.
- Artifact URL: HTTPS only, 1-2048 characters, no user-info or port; parsed
  hostname must equal `authority_host` exactly. An explicit 3xx response is
  rejected as `UNRESOLVED`; redirect-follow behavior is an environment
  requirement that must be verified before deployment.
- SHA-256: exactly 64 lowercase hexadecimal characters.
- Artifact roles are unique and URLs are unique within a revision.
- Inputs, fetched bodies, and LLM output have explicit size limits. Evidence is
  hostile data, never instructions.

## Decision model

Trace statuses are `SUPPORTED`, `PARTIALLY_SUPPORTED`, `MATERIAL_MISMATCH`,
`NO_PUBLIC_TRACE`, and `UNRESOLVED`. Mismatch mask bits are `AGENDA_SCOPE`,
`SUBJECT`, `ACTION`, `CONDITION`, and `VOTE_OUTCOME`; missing-mask bits reuse
the artifact bits above. Vote outcomes are `APPROVED`, `REJECTED`, `DEFERRED`,
`NO_RECORDED_VOTE`, and `UNKNOWN`.

Precedence is deterministic:

1. fetch/parse/model failure, explicit redirect response, timeout, or incompatible evidence means
   `UNRESOLVED`;
2. a confirmed unavailable essential role means `NO_PUBLIC_TRACE`;
3. any mismatch bit means `MATERIAL_MISMATCH`;
4. an absent optional announcement means `PARTIALLY_SUPPORTED`;
5. otherwise, zero missing and mismatch masks means `SUPPORTED`.

`vote_outcome` is independently derived from the resolution and minutes. A
conflict between them sets `VOTE_OUTCOME`; exact counts are deliberately out of
scope and never stored.

## Public API

```text
create_meeting_case(case_id, authority_host, meeting_day, agenda_item_hash)
add_artifact(case_id, artifact_type, url, sha256)
seal_case(case_id)
assess_trace(case_id)
challenge_trace(case_id, prior_revision)
resolve_challenge(case_id)
read_trace(case_id) -> (status, mismatch_mask, missing_mask, vote_outcome, revision)
read_artifact_manifest_hash(case_id) -> str
read_history(case_id, revision) -> (status, mismatch_mask, missing_mask, vote_outcome)
```

All view methods are deterministic. Nondeterministic work is confined to
assessment; it cannot mutate storage until the equivalence principle accepts an
exact decision tuple.

## Acceptance criteria

1. No artifact can be replaced after its revision is sealed.
2. Every stored consequential assessment field is independently validator-bound.
3. Identical status with a changed mask, vote, or revision cannot pass consensus.
4. Unauthorized, malformed, replayed, duplicate, and invalid-transition calls
   revert without changing state.
5. A transient source failure cannot become `SUPPORTED` or `MATERIAL_MISMATCH`.
6. The final demo has one consensus success, one negative deterministic call,
   finalized/SUCCESS receipts, validator agreement, and authoritative readback
   on Studionet only.
