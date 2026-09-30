# Evaluator contract

Evaluators may provide any runtime batch; code must not contain evaluation
company numbers or rely on a fixed batch size. For each non-empty input row,
the output count and order must match exactly. Test malformed rows, invalid
checksums, missing datasets, blocked websites, ambiguous identities, source
failures, and valid zero values.

Pass criteria include:

- all six availability states are representable and visible;
- abstentions have null values and an explanatory note/error;
- no fabricated zeros or names;
- every available claim has traceable immutable evidence metadata;
- identity gates precede website facts;
- failed refreshes preserve prior values;
- clean installation and one-command batch execution work offline.
