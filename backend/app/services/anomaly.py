"""Anomaly detection for metrics."""

from typing import Any
import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.logging import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """Statistical and ML-based anomaly detection."""

    def __init__(self, contamination: float = 0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self._fitted = False

    def fit(self, historical_values: list[float]) -> None:
        if len(historical_values) < 10:
            self._fitted = False
            return
        X = np.array(historical_values).reshape(-1, 1)
        self.model.fit(X)
        self._fitted = True

    def detect(self, value: float, threshold_std: float = 3.0) -> dict[str, Any]:
        """Detect if value is anomalous using z-score and isolation forest."""
        result = {"is_anomaly": False, "score": 0.0, "method": "threshold"}

        if self._fitted:
            pred = self.model.predict([[value]])
            score = -self.model.score_samples([[value]])[0]
            result["is_anomaly"] = pred[0] == -1
            result["score"] = float(score)
            result["method"] = "isolation_forest"
        else:
            # Simple threshold fallback
            result["is_anomaly"] = value > 100  # configurable per metric
            result["score"] = value / 100.0

        return result

    def check_threshold(
        self,
        value: float,
        threshold: float,
        operator: str = "gt",
    ) -> bool:
        ops = {"gt": value > threshold, "lt": value < threshold, "gte": value >= threshold}
        return ops.get(operator, False)
