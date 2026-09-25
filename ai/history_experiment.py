"""History-grounded experiment reasoning for Sentinel AI v0.2."""

from ai.history_experiment_guard import validate_history_experiment
from ai.history_report import build_history_report
from ai.llm_client import generate_text


def build_history_experiment_prompt(
    target_session_id,
    *,
    results_dir="results/ml/prospective",
):
    report = build_history_report(
        target_session_id,
        results_dir=results_dir,
    )

    return (
        "You are Sentinel AI v0.2.\n\n"
        "The historical comparison below is authoritative and was "
        "computed deterministically.\n"
        "Do not recalculate it, change its values, or introduce future "
        "sessions not listed in the report.\n\n"
        "Propose exactly ONE next controlled RF experiment based on the "
        "historical comparison.\n"
        "The experiment must be non-destructive.\n"
        "Do not attempt transmitter identification or calibration-grade "
        "absolute direction.\n"
        "Prefer repeating or varying only quantities actually present in "
        "the deterministic historical report. Do not invent environmental, "
        "propagation, reflectivity, interference, or causal variables.\n"
        "Describe what to repeat or change, what to measure, and what "
        "historical comparison would test the hypothesis.\n"
        "Use 2-4 sentences.\n\n"
        "DETERMINISTIC HISTORICAL REPORT:\n"
        + report["text"]
    )


def suggest_history_experiment(
    target_session_id,
    *,
    results_dir="results/ml/prospective",
    max_attempts=2,
    generate_fn=None,
):
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    if generate_fn is None:
        generate_fn = generate_text

    prompt = build_history_experiment_prompt(
        target_session_id,
        results_dir=results_dir,
    )

    current_prompt = prompt

    for attempt in range(1, max_attempts + 1):
        suggestion = generate_fn(current_prompt)

        try:
            return validate_history_experiment(suggestion)
        except Exception as exc:
            if attempt == max_attempts:
                raise

            current_prompt = (
                prompt
                + "\n\nREPAIR INSTRUCTION:\n"
                + f"The previous suggestion was rejected: {exc}\n"
                + "Generate a fresh experiment using only quantities "
                  "explicitly present in the deterministic historical report.\n"
                + "Do not introduce propagation, reflection, reflectivity, "
                  "interference, environmental causes, directional accuracy, "
                  "or transmitter identity.\n"
                + "Prefer a repeatability experiment comparing the target "
                  "session with its prior same-cluster mean or nearest prior "
                  "sessions.\n"
            )

    raise RuntimeError("unreachable")
