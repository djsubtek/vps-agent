from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetLimits:
    max_output_tokens: int = 800
    max_files_changed: int = 12
    max_iterations_per_run: int = 1
    max_escalation_calls_per_run: int = 1


def enforce_limits(
    limits: BudgetLimits,
    output_tokens: int,
    files_changed: int,
    iterations_used: int,
    escalation_calls: int,
) -> None:
    if output_tokens > limits.max_output_tokens:
        raise ValueError("Output token budget exceeded")
    if files_changed > limits.max_files_changed:
        raise ValueError("File change budget exceeded")
    if iterations_used > limits.max_iterations_per_run:
        raise ValueError("Iteration budget exceeded")
    if escalation_calls > limits.max_escalation_calls_per_run:
        raise ValueError("Escalation call budget exceeded")
