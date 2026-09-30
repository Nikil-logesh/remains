# Identity resolution

The organization number is the primary key. Inputs are normalized to digits
and must pass the Norwegian nine-digit checksum before a registry or dataset
lookup. A registry response must contain the requested number and a legal
name; aliases are retained only as candidate hints.

Website evidence is accepted only when the URL is public and its fetched
content contains the verified legal name (or an explicitly verified alias).
Cross-domain redirects, private hosts, malformed URLs, and name mismatches
are rejected. If multiple candidates remain plausible, emit `ambiguous` and
do not attach their facts to the profile.

No identity match is a reason to abstain, not permission to select the closest
company.
