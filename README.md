# Signalpost — Company Intelligence Agent

Signalpost performs a **read-only** lookup of Norwegian companies in the
Brønnøysund Register Centre's Enhetsregisteret. The production path combines official registry identity, bounded first-party
source confirmation, evidence-backed claims, SQLite history, fail-closed
abstention, and streaming batch output. External calls are bounded and never
fabricate data.

## Evaluator contract

Batch input is arbitrary runtime JSONL, not a fixed fixture. Every non-empty
input row produces exactly one output envelope in the same order, including
malformed rows and invalid identities; the original row is retained as
`input`. Field availability is explicit: `available`, `not_available`,
`blocked`, `not_applicable`, `ambiguous`, or `failed`. Abstentions are visible
with `null` values and an explanatory note/error, and missing data is never
converted to zero. Available claims reference immutable evidence metadata
(source, retrieval time, row key, and content hash).

Identity is resolved through the official registry before first-party website
evidence is accepted. Refreshes are transactional: a failed refresh preserves
the prior profile. See `AGENT.md`, `CRAWLERS.md`, `IDENTITY_RESOLUTION.md`,
`DATA_SCHEMA.md`, `REFRESH.md`, `EVAL.md`, and `LIMITATIONS.md`.

## Setup

Python 3.12+ is required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run

```powershell
python run.py --company 984851006
python run.py 984851006 --json
python run.py 984851006 --json --enrich
```

Optional NVIDIA Gemma support uses only `NVIDIA_API_KEY` and `NVIDIA_MODEL`
from the environment. Without a key, the deterministic path is used; keys are
never logged. Website URLs must be public `http(s)` URLs and identity
verification is required before website evidence is accepted.

Example (the live registry can change):

```text
{
  "organization_number": "984851006",
  "legal_name": "Test Company AS",
  "source_url": "https://data.brreg.no/enhetsregisteret/api/enheter/984851006"
}
```

The command makes one read-only registry request and stores the successful
response in the local SQLite file. It does not create or update registry data,
accounts, or external resources. Network errors and invalid input are reported
without inventing fallback company information.

`--enrich` enables bounded first-party confirmation. The registry website is
normalized to a public HTTPS origin, then only the homepage and deterministic
same-origin paths (`about`, `contact`, `company`, `sitemap.xml`, and
`robots.txt`) are attempted. Responses are size-limited, retried with a
per-company request budget, and never followed across hosts. JSON-LD,
OpenGraph, metadata, and readable text are retained as hashed evidence only
after the legal name, organization number, or registered address confirms the
registry identity. Mismatches, conflicts, blocked URLs, and unavailable
sources remain explicit abstentions; search results, social platforms, and
authenticated sources are never used.

## Tests

```powershell
pytest -q
```

## Batch JSONL mode

Batch mode is streaming and read-only: it emits exactly one terminal JSON
envelope for every non-empty input line, including malformed or invalid rows.
Missing data is reported as `not_available`; it is never fabricated. Configure the
financial snapshot with `--financial-dataset` or
`SIGNALPOST_FINANCIAL_DATASET_PATH`.

```powershell
python run.py --input companies.jsonl --output envelopes.jsonl `
  --financial-dataset D:\learn\financial-filer-master-2025.jsonl.txt `
  --run-id smoke-001
```

Add `--enrich` to the batch command to run the same fail-closed public-source
confirmation for each valid organization number.

Each envelope contains `run`, `claims`, `evidence`, `changes`, `errors`, and
`operations`. Financial rows are looked up sequentially so the 130 MB snapshot
is not loaded into memory. The source path, line key, retrieval timestamp, and
content SHA-256 are retained for auditability. Batch mode performs no network
calls and does not hardcode evaluation companies.

## Learning harness

Connectors are registered under stable, versioned names (`registry`, `website`,
`financial`, `announcements`, `accounts`, and `llm`). Unavailable connectors
return an explicit `not_implemented` result and never invent claims. Local
SQLite `AttemptStore` records every company/strategy attempt, including input
URLs and hashes, candidates, evidence, decisions, runtime, requests, cost,
errors, and status. A winner is changed only after a strict, frozen-policy
promotion gate; rejected challengers leave the previous winner untouched.

Gold corpora and challenger attempts can be compared offline without external
services:

```powershell
python -m eval.run --corpus gold.jsonl --challenger challenger.jsonl
```

## Submission smoke test

Run this before submitting:

```powershell
pytest -q
python run.py --company 984851006 --json --enrich
python run.py --input companies.jsonl --output output.jsonl `
  --financial-dataset D:\learn\financial-filer-master-2025.jsonl.txt `
  --run-id submission-smoke
```

The batch command must produce one JSON object per non-empty input row. Do not
include `.env`, API keys, `signalpost.sqlite3`, `.venv`, or generated output
files in the repository. See [SUBMISSION.md](SUBMISSION.md) for the final
submission checklist and the exact information to send to the evaluator.
