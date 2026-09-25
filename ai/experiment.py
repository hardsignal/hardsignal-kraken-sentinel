"""Grounded AI suggestion for the next controlled Sentinel experiment."""

import json

from ai.analyst import analyse_bundle
from ai.experiment_guard import validate_experiment_suggestion
from ai.llm_client import generate_text
from ai.schemas import validate_evidence_bundle


def build_experiment_prompt(bundle):
    bundle = validate_evidence_bundle(bundle)
    analysis = analyse_bundle(bundle)

    evidence = {
        "session_id": bundle["session_id"],
        "deterministic_analysis": analysis,
        "ml": {
            "assigned_cluster": bundle["ml"]["assigned_cluster"],
            "novelty": bundle["ml"]["novelty"],
            "nearest_distance": bundle["ml"]["nearest_distance"],
            "distance_vs_training_max": (
                bundle["ml"]["distance_vs_training_max"]
            ),
        },
    }

    return (
        "You are Sentinel AI.\n\n"
        "Propose exactly ONE next controlled RF research experiment.\n"
        "The experiment must be non-destructive and based only on the "
        "supplied evidence.\n"
        "Do not add facts about the completed session.\n"
        "Do not infer transmitter identity, environmental causes, or "
        "absolute direction.\n"
        "Write 2-4 sentences describing what to change or repeat, what "
        "to measure, and what comparison would be useful.\n\n"
        "AUTHORITATIVE EVIDENCE:\n"
        + json.dumps(evidence, indent=2, sort_keys=True)
    )


def suggest_experiment_from_prompt(prompt):
    suggestion = generate_text(prompt)
    return validate_experiment_suggestion(suggestion)


def suggest_next_experiment(bundle):
    return suggest_experiment_from_prompt(
        build_experiment_prompt(bundle)
    )
