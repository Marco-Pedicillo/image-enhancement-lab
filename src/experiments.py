
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from src.metrics import (
    calculate_metrics,
    calculate_preservation_metrics,
)


#Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
CSV_PATH = RESULTS_DIR / "experiments.csv"


#Consistent columns for every experiment
CSV_FIELDS = [
    "run_id",
    "timestamp_utc",
    "image_hash",
    "source_filename",
    "workflow",
    "status",
    "reason",
    "processing_time_s",
    "model",
    "parameters_json",
    "input_tokens",
    "output_tokens",
    "quality_gate_accepted",
    "quality_warnings",
    "manual_override",
    "brightness",
    "contrast",
    "sharpness",
    "shadow_fraction",
    "highlight_clipping",
    "dynamic_range",
    "local_contrast",
    "black_region_change",
    "mean_rgb_change",
    "visual_quality",
    "naturalness",
    "property_fidelity",
    "potentially_misleading_alteration",
    "preferred",
    "feedback",
]


def _json_text(value):
    """Serialize structured values for CSV storage."""
    if value is None:
        return ""

    return json.dumps(value, ensure_ascii=False)


def _existing_run_ids():
    """Read saved IDs to prevent duplicate experiments."""
    if not CSV_PATH.exists():
        return set()

    with CSV_PATH.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file, delimiter=";")

        if reader.fieldnames != CSV_FIELDS:
            raise ValueError(
                "Existing CSV schema does not match "
                "the current experiment schema."
            )

        return {
            row["run_id"]
            for row in reader
        }


def save_experiment(
    experiment,
    image_hash,
    source_filename,
):
    """
    Save one experiment as three workflow rows.

    Returns True when newly saved.
    Returns False when already saved.
    """

    evaluation = experiment.get("human_evaluation")

    if not evaluation:
        raise ValueError(
            "Human evaluation must be completed before saving."
        )

    if not experiment.get("run_id"):
        raise ValueError("Experiment run_id is missing.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    run_id = str(experiment["run_id"])

    if run_id in _existing_run_ids():
        return False

    timestamp = datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    original = experiment["original"]

    workflows = [
        (
            "Original",
            original,
            {"status": "original", "reason": "Input image"},
            None,
            None,
        ),
        (
            "Traditional",
            experiment["traditional"],
            experiment["traditional_decision"],
            experiment["traditional_time"],
            experiment["traditional_error"],
        ),
        (
            "AI-Assisted",
            experiment["ai"],
            experiment["ai_decision"],
            experiment["ai_time"],
            experiment["ai_error"],
        ),
    ]

    rows = []

    for name, output, decision, elapsed, error in workflows:

        decision = decision or {}

        metrics = (
            calculate_metrics(output)
            if output is not None else {}
        )

        preservation = (
            calculate_preservation_metrics(original, output)
            if output is not None else {}
        )

        scores = evaluation["scores"].get(name, {})

        usage = decision.get("usage") or {}
        params = decision.get("parameters")

        quality_check = (
            decision.get("quality_check") or {}
        )

        gate_accepted = quality_check.get("accepted")

        row = {
            "run_id": run_id,
            "timestamp_utc": timestamp,
            "image_hash": image_hash,
            "source_filename": Path(source_filename).name,
            "workflow": name,
            "status": (
                "error" if error
                else decision.get("status", "unknown")
            ),
            "reason": error or decision.get("reason", ""),
            "processing_time_s": (
                round(elapsed, 4)
                if elapsed is not None else ""
            ),
            "model": decision.get("model", ""),
            "parameters_json": _json_text(params),
            "input_tokens": usage.get("input_tokens", ""),
            "output_tokens": usage.get("output_tokens", ""),
            "quality_gate_accepted": (
                gate_accepted
                if gate_accepted is not None else ""
            ),
            "quality_warnings": _json_text(
                quality_check.get("warnings", [])
            ),
            "manual_override": (
                experiment.get("ai_blended", False)
                if name == "AI-Assisted" else False
            ),
            "black_region_change": preservation.get(
                "black_region_change", ""
            ),
            "mean_rgb_change": preservation.get(
                "mean_rgb_change", ""
            ),
            "visual_quality": scores.get(
                "visual_quality", ""
            ),
            "naturalness": scores.get(
                "naturalness", ""
            ),
            "property_fidelity": scores.get(
                "property_fidelity", ""
            ),
            "potentially_misleading_alteration": scores.get(
                "material_change", ""
            ),
            "preferred": (
                evaluation["preferred"] == name
            ),
            "feedback": evaluation.get("feedback", ""),
        }

        for metric in [
            "brightness",
            "contrast",
            "sharpness",
            "shadow_fraction",
            "highlight_clipping",
            "dynamic_range",
            "local_contrast",
        ]:
            row[metric] = (
                round(metrics[metric], 4)
                if metric in metrics else ""
            )

        rows.append(row)

    file_exists = CSV_PATH.exists()

    with CSV_PATH.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
            delimiter=";",
        )

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)

    return True
