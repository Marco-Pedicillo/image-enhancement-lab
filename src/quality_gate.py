
from src.metrics import calculate_metrics


def evaluate_candidate(original, candidate):
    """
    Conservative quality checks for an enhancement
    candidate. Thresholds are experimental.
    """
    before = calculate_metrics(original)
    after = calculate_metrics(candidate)

    warnings = []

    if after["contrast"] < before["contrast"] * 0.85:
        warnings.append("Excessive global contrast loss")

    if after["local_contrast"] < before["local_contrast"] * 0.85:
        warnings.append("Excessive local contrast loss")

    if (
        after["highlight_clipping"]
        > before["highlight_clipping"] + 0.02
    ):
        warnings.append("Increased highlight clipping")

    if after["dynamic_range"] < before["dynamic_range"] * 0.80:
        warnings.append("Excessive dynamic range reduction")

    return {
        "accepted": len(warnings) == 0,
        "warnings": warnings
    }
