# Crawlers and source ladder

Signalpost is not a general web crawler. Connectors are bounded, read-only,
and only fetch public URLs supplied by an authoritative source.

## Source ladder

1. Official registries and regulator APIs (identity and legal facts).
2. First-party company websites (only after identity verification).
3. Licensed/public datasets supplied at runtime (for example a financial
   snapshot), retaining file URI, row key, retrieval time, and content hash.
4. Public announcements and accounts connectors when enabled.
5. No source: abstain rather than guess.

Requests use HTTPS where available, bounded response sizes, finite timeouts,
no authentication, and no state-changing operations. Redirects remain on the
verified host. The project intentionally has no social-platform, directory
circumvention, login-only, or personal-data scraper.
