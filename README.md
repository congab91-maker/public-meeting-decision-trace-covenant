# Public Meeting Decision Trace Covenant

An evidence-trace oracle for a public meeting decision. It records whether an
agenda item, meeting record, and published resolution support the same declared
decision. It does not decide legality, political merit, quorum law, or speaker
truthfulness.

## Live Deployment

Studionet (Chain ID 61999):
[`0x941CAD8c63C99D5f397018EEe00AabaEcad2E2E1`](https://explorer-studio.genlayer.com/address/0x941CAD8c63C99D5f397018EEe00AabaEcad2E2E1)

Deployment transaction:
[`0x68c4a4b60cdc119bd7003659757c606ffb0f85ee950442dff4501b6eb11073c0`](https://explorer-studio.genlayer.com/tx/0x68c4a4b60cdc119bd7003659757c606ffb0f85ee950442dff4501b6eb11073c0)
(FINALIZED, SUCCESS, 5/5 validators agree). Reproducible E2E inputs are in
`samples/demo_manifest.json`; transaction and readback details are in
`docs/deployment-evidence.md`.

## Development status

The implementation specification is in `docs/architecture.md` and the consensus
binding requirements are in `docs/consensus.md`. The contract source and Direct
Mode regression tests are implemented locally; PRE-DEPLOY semantic validation
and Studionet evidence are recorded in the deployment evidence file.

## Intended integrations

- A transparency dashboard can render `read_trace` without trusting an indexer.
- A governance workflow can require `SUPPORTED` before showing a meeting decision
  as trace-complete.
- A DAO execution gate can use the status, masks, and revision to decide whether
  an announced resolution needs human follow-up.

## Repository structure

```text
contracts/  # standalone Intelligent Contract source
docs/       # approved architecture and consensus design
samples/    # exact public demo manifests are added after hash capture
tests/      # Direct Mode regression tests
```

## Consensus Engineering Lessons

- Hash commitments are checked against fetched raw bytes before any model call.
- Leader and validator rerun the same bounded assessment and exact-compare every
  stored decision field.
- Failed fetches, malformed bytes, and malformed model output fail closed as
  `UNRESOLVED`.

## Consensus Binding Matrix

| Stored field | Binding |
|---|---|
| `trace_status`, masks, `vote_outcome` | exact leader/validator decision JSON |
| `missing_mask` | sealed artifact availability and HTTP result |
| agenda commitment | SHA-256(raw AGENDA bytes) = artifact hash = `agenda_item_hash` |
| `revision` and history | deterministic lifecycle and revision-keyed storage |

## License

MIT. See `LICENSE`.
