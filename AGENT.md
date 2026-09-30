# Signalpost agent playbook

Signalpost is a read-only, evidence-first company enrichment pipeline. Agents
must preserve input order and emit one terminal envelope for every non-empty
JSONL row. Never infer a value from a missing source, turn missing numbers
into zero, or silently drop a row.

## Operating rules

1. Normalize and validate identity before collecting company facts.
2. Use the source ladder in `CRAWLERS.md`; prefer first-party/official sources.
3. Apply the identity gates in `IDENTITY_RESOLUTION.md` before accepting
   website or secondary-source evidence.
4. Every assertion is either supported by immutable evidence metadata or is
   explicitly abstained from.
5. Availability is one of `available`, `not_available`, `blocked`,
   `not_applicable`, `ambiguous`, or `failed`.
6. Refreshes are transactional: a failed refresh cannot overwrite the last
   successful profile.
7. Do not add social-network, people-search, login-only, or prohibited
   platform scrapers.

Run the complete suite with `pytest -q`. The supported entry point is
`python run.py --input INPUT.jsonl --output OUTPUT.jsonl`.
