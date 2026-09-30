# Limitations

The default batch path is intentionally conservative and offline unless a
runtime dataset is supplied. It does not discover arbitrary companies by
guessing URLs, bypass robots/authentication, or scrape prohibited social and
people-search platforms. Registry coverage, website availability, language,
rate limits, and dataset freshness can all limit fields.

`not_available`, `blocked`, `ambiguous`, and `failed` are meaningful outcomes,
not empty success. Consumers must distinguish them from `available`; absence
of a claim is not evidence that the value is zero.
