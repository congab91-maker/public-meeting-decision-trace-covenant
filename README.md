# Public Meeting Decision Trace Covenant

An evidence-trace oracle for a public meeting decision. It records whether an
agenda item, meeting record, and published resolution support the same declared
decision. It does not decide legality, political merit, quorum law, or speaker
truthfulness.

## Live Deployment

Not yet deployed. Studionet evidence is created only after the exact source,
tests, and PRE-DEPLOY approvals are complete.

## Development status

The implementation specification is in `docs/architecture.md` and the consensus
binding requirements are in `docs/consensus.md`. The contract source and Direct
Mode regression tests are implemented locally; PRE-DEPLOY semantic validation
and Studionet evidence remain pending.

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

## License

MIT. See `LICENSE`.
