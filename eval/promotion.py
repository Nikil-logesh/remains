DEFAULT_POLICY = {"min_coverage_delta": 0.01, "max_precision_drop": 0.0, "max_wrong_company_increase": 0}


def promotion_gate(challenger: dict, incumbent: dict, policy: dict | None = None) -> dict:
    rules = {**DEFAULT_POLICY, **(policy or {})}
    reasons = []
    if challenger.get("wrong_company_publications", 0) > incumbent.get("wrong_company_publications", 0) + rules["max_wrong_company_increase"]:
        reasons.append("wrong_company_publications_increased")
    if challenger.get("precision", 0) < incumbent.get("precision", 0) - rules["max_precision_drop"]:
        reasons.append("precision_dropped")
    if challenger.get("coverage", 0) < incumbent.get("coverage", 0) + rules["min_coverage_delta"]:
        reasons.append("coverage_did_not_improve")
    return {"promote": not reasons, "reasons": reasons, "policy": rules}
