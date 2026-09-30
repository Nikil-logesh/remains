# Refresh and history

Refreshes are read-only observations. Build and validate a complete candidate
profile first, compare it with the prior profile, and commit it only after all
identity/evidence gates pass. On timeout, parse failure, source outage, or any
other refresh error, retain the prior profile and return the error with
availability `failed`. A failed refresh must never replace known values with
null or zero.

Changes are deterministic field-level diffs. Each observation records when and
where it was retrieved and a SHA-256 hash of the exact source payload or row.
