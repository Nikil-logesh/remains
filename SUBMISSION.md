# Signalpost submission checklist

## Repository contents

Submit the repository containing:

- `app/`, `eval/`, `strategies/`, `signalpost/`, `tests/`
- `run.py`
- `requirements.txt`
- `.env.example`
- `README.md` and the policy/schema documentation

Do not commit:

- `.env`
- API keys or tokens
- `.venv/`
- `*.sqlite3`
- generated output or temporary smoke-test files
- the 125 MB local financial snapshot

## Clean-machine verification

From a new checkout:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

No API key is required for registry-only or local financial-dataset runs.
NVIDIA Gemma is optional. If enabled, provide a newly rotated key through the
environment only:

```env
NVIDIA_API_KEY=...
NVIDIA_MODEL=google/gemma-4-31b-it
```

Never commit `.env`.

## Evaluator command

The runtime evaluator supplies the company JSONL file. Do not replace it with a
hardcoded list:

```powershell
python run.py --input evaluator-companies.jsonl `
  --output output/profiles.jsonl `
  --run-id submission-001 `
  --enrich
```

If a local financial snapshot is available, add:

```powershell
--financial-dataset D:\learn\financial-filer-master-2025.jsonl.txt
```

Every non-empty input row produces exactly one output envelope in input order.
Malformed rows, unavailable sources, ambiguous identity, and failed refreshes
remain visible and are never silently dropped.

## Declared sources and models

- Brønnøysundregistrene Enhetsregisteret: canonical company identity
- Registry-provided first-party website: bounded public confirmation only
- Local supplied financial JSONL snapshot: optional structured facts
- NVIDIA NIM Gemma `google/gemma-4-31b-it`: optional extraction component
- No search result, social profile, or unofficial scraper is used as sole
  evidence for a published claim

## Cost and limits

Registry and website calls are public HTTP requests. The deterministic path
does not require a paid API. NVIDIA usage is optional and should be declared
using the provider's current pricing at submission time. The implementation
uses bounded requests, retries, response-size limits, and explicit abstention.

## Final report to evaluator

Provide:

1. Repository URL
2. Exact commit hash
3. One-command evaluator invocation
4. Declared models and APIs
5. Expected cost for 100 companies
6. Test result (`pytest -q`)
7. Any local dataset paths used
8. Known limitations and source-access assumptions

This working directory was initially not a Git repository. Initialize and
commit it locally before submission, then push it to the repository host:

```powershell
git init
git add .
git commit -m "Prepare Signalpost submission" `
  -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git rev-parse HEAD
```

Review `git status --short` and confirm no secrets or generated artifacts are
included before pushing.
