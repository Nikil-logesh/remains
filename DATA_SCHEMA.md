# Data schema and contract

Batch input is JSONL. Blank lines are ignored; every non-empty line produces
exactly one JSON output envelope in the same order. Malformed JSON and invalid
identities still receive a terminal envelope containing the original `input`.

An envelope contains `run`, `run_id`, `terminal_status`, `organisation_number`,
`input`, `claims`, `evidence`, `changes`, `errors`, and `operations`.
`terminal_status` is `completed` or `failed`; field-level availability is
always explicit: `available`, `not_available`, `blocked`, `not_applicable`,
`ambiguous`, or `failed`.

Available claims must reference evidence IDs. Evidence records retain source
type/class, URL or file URI, retrieval timestamp, source row key where
applicable, value, and SHA-256 content hash. Missing values are `null` (never
fabricated zeroes). Evidence metadata is append-only in meaning: a refresh
creates new metadata rather than mutating the old observation.
