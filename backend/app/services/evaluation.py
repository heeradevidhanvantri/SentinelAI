"""AI evaluation framework for agent quality."""

from typing import Any
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationResult:
    hallucination_score: float  # 0=high hallucination, 1=grounded
    root_cause_accuracy: float
    remediation_success: float
    resolution_time_seconds: float
    overall_score: float
    details: dict[str, Any]


class EvaluationFramework:
    """Score agent outputs against ground truth and outcomes."""

    def evaluate_incident(
        self,
        predicted_root_cause: str,
        actual_root_cause: str | None,
        execution_success: bool,
        resolution_time_seconds: float,
        reasoning_traces: list[dict],
        ground_truth_runbooks: list[str] | None = None,
    ) -> EvaluationResult:
        # Root cause accuracy (semantic overlap proxy)
        rc_accuracy = self._root_cause_accuracy(
            predicted_root_cause, actual_root_cause
        )

        # Hallucination: check if reasoning cites tool results
        hallucination = self._hallucination_score(reasoning_traces)

        # Remediation success
        remediation = 1.0 if execution_success else 0.0

        # Resolution time score (target: < 15 min = 900s)
        time_score = max(0, 1 - (resolution_time_seconds / 900))

        overall = (
            rc_accuracy * 0.35
            + hallucination * 0.25
            + remediation * 0.25
            + time_score * 0.15
        )

        return EvaluationResult(
            hallucination_score=hallucination,
            root_cause_accuracy=rc_accuracy,
            remediation_success=remediation,
            resolution_time_seconds=resolution_time_seconds,
            overall_score=overall,
            details={
                "trace_count": len(reasoning_traces),
                "time_score": time_score,
            },
        )

    def _root_cause_accuracy(self, predicted: str, actual: str | None) -> float:
        if not actual:
            return 0.7  # no ground truth
        pred_words = set(predicted.lower().split())
        actual_words = set(actual.lower().split())
        if not actual_words:
            return 0.0
        overlap = len(pred_words & actual_words) / len(actual_words)
        return min(1.0, overlap)

    def _hallucination_score(self, traces: list[dict]) -> float:
        if not traces:
            return 0.5
        tool_backed = sum(
            1 for t in traces if t.get("tool_calls")
        )
        return min(1.0, 0.5 + (tool_backed / len(traces)) * 0.5)
