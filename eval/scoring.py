"""Gold-set scoring with explicit safety metrics."""

from typing import Any


def score_attempts(attempts: list[dict[str, Any]], gold: list[dict[str, Any]]) -> dict[str, Any]:
    gold_by_org = {str(row.get("organization_number", row.get("organisation_number", row.get("company", "")))): row for row in gold}
    rows = []
    for attempt in attempts:
        org = str(attempt.get("organization_number", attempt.get("organisation_number", attempt.get("company", ""))))
        expected = gold_by_org.get(org, {}).get("claims", [])
        expected_map = {str(c["field"]): c.get("value") for c in expected if isinstance(c, dict) and "field" in c}
        actual = {str(c["field"]): c.get("value") for c in attempt.get("claims", []) if isinstance(c, dict) and c.get("field") and c.get("availability", "available") == "available"}
        correct = sum(actual.get(field) == value for field, value in expected_map.items())
        published = len(actual)
        rows.append({"organization_number": org, "correct": correct, "expected": len(expected_map), "published": published,
                     "wrong_company": int(attempt.get("wrong_company_publications", 0))})
    total_expected = sum(r["expected"] for r in rows)
    total_correct = sum(r["correct"] for r in rows)
    total_published = sum(r["published"] for r in rows)
    return {"companies": len(rows), "coverage": total_correct / total_expected if total_expected else 0.0,
            "precision": total_correct / total_published if total_published else 1.0,
            "wrong_company_publications": sum(r["wrong_company"] for r in rows), "rows": rows}
