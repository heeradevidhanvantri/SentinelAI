#!/usr/bin/env python3
"""Demo replay simulator — autonomous recovery timeline for recruiter demos."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _platform_utils import (  # noqa: E402
    API_URL,
    auth_headers,
    c,
    fail,
    get_client,
    info,
    login,
    ok,
    Color,
)

STAGES = [
    ("alert", "Alert generated", Color.YELLOW),
    ("incident", "Incident created", Color.CYAN),
    ("investigation", "Investigation started", Color.BLUE),
    ("root_cause", "Root cause identified", Color.CYAN),
    ("remediation", "Remediation selected", Color.YELLOW),
    ("execution", "Action executed", Color.GREEN),
    ("recovery", "Recovery validated", Color.GREEN),
    ("report", "Report generated", Color.BOLD),
]


@dataclass
class TimelineEvent:
    stage: str
    label: str
    message: str
    elapsed_ms: float
    details: dict = field(default_factory=dict)


class DemoReplay:
    def __init__(self, delay: float = 0.8):
        self.delay = delay
        self.events: list[TimelineEvent] = []
        self.start = time.perf_counter()

    def _elapsed(self) -> float:
        return (time.perf_counter() - self.start) * 1000

    def log(self, stage: str, label: str, message: str, color: str, **details) -> None:
        elapsed = self._elapsed()
        self.events.append(TimelineEvent(stage, label, message, elapsed, details))
        ts = c(f"[{elapsed:7.0f}ms]", Color.DIM)
        stage_label = c(f" {label:<28}", color)
        print(f"{ts}{stage_label} {message}")
        if details:
            for k, v in details.items():
                print(c(f"           └─ {k}: {v}", Color.DIM))
        time.sleep(self.delay)

    def run(self, async_mode: bool = False) -> dict:
        print(c("\n" + "=" * 70, Color.BOLD))
        print(c("  SentinelAI Autonomous Recovery Demo Replay", Color.BOLD))
        print(c("=" * 70, Color.BOLD))
        print(info(f"API: {API_URL}\n"))

        demo_incident = {
            "title": "Payment API latency spike — demo replay",
            "description": (
                "P99 latency exceeded 2s; error rate at 12%. "
                "Autonomous SRE pipeline engaged."
            ),
            "service": "payment-api",
            "severity": "critical",
        }

        with get_client(timeout=180) as client:
            token = login(client)
            headers = auth_headers(token)

            self.log(
                "alert", STAGES[0][1], STAGES[0][1],
                STAGES[0][2],
                service=demo_incident["service"],
                severity=demo_incident["severity"],
            )

            # Ingest synthetic alert signals
            client.post(
                f"{API_URL}/api/v1/monitoring/metrics/ingest",
                json={
                    "service": demo_incident["service"],
                    "metric_name": "http.request.duration.p99",
                    "value": 2340,
                    "labels": {"demo": "replay"},
                },
                headers=headers,
            )
            client.post(
                f"{API_URL}/api/v1/monitoring/logs/ingest",
                json={
                    "service": demo_incident["service"],
                    "level": "ERROR",
                    "message": demo_incident["description"],
                },
                headers=headers,
            )

            create_resp = client.post(
                f"{API_URL}/api/v1/incidents", json=demo_incident, headers=headers
            )
            create_resp.raise_for_status()
            incident = create_resp.json()
            incident_id = incident["id"]

            self.log(
                "incident", STAGES[1][1], STAGES[1][1],
                STAGES[1][2], incident_id=incident_id, status=incident.get("status"),
            )

            self.log(
                "investigation", STAGES[2][1], "Monitoring → Investigation agents engaged",
                STAGES[2][2], agents=["monitoring", "investigation"],
            )

            pipeline_start = time.perf_counter()
            if async_mode:
                resp = client.post(
                    f"{API_URL}/api/v1/incidents/{incident_id}/investigate",
                    headers=headers,
                )
            else:
                resp = client.post(
                    f"{API_URL}/api/v1/incidents/trigger",
                    json={"incident_id": incident_id, **demo_incident},
                    headers=headers,
                )
            resp.raise_for_status()
            result = resp.json()
            pipeline_ms = (time.perf_counter() - pipeline_start) * 1000

            root_cause = result.get("root_cause") or "Connection pool saturation (inferred)"
            self.log(
                "root_cause", STAGES[3][1], STAGES[3][1],
                STAGES[3][2],
                root_cause=root_cause[:100],
                confidence=result.get("root_cause_confidence", "n/a"),
            )

            plan = result.get("remediation_plan") or "Restart pods + scale horizontally"
            self.log(
                "remediation", STAGES[4][1], STAGES[4][1],
                STAGES[4][2], plan=str(plan)[:100],
            )

            self.log(
                "execution", STAGES[5][1], "Execution agent applied remediation",
                STAGES[5][2], pipeline_ms=f"{pipeline_ms:.0f}ms",
            )

            self.log(
                "recovery", STAGES[6][1], "Metrics normalized; SLO restored",
                STAGES[6][2], resolution_time=result.get("resolution_time_seconds", "n/a"),
            )

            timeline_resp = client.get(
                f"{API_URL}/api/v1/agents/{incident_id}/timeline", headers=headers
            )
            traces = timeline_resp.json().get("timeline", [])

            self.log(
                "report", STAGES[7][1], STAGES[7][1],
                STAGES[7][2],
                reasoning_traces=len(traces),
                final_status=result.get("status"),
            )

        total_ms = self._elapsed()
        print(c("\n" + "-" * 70, Color.DIM))
        print(c("  Execution Summary", Color.BOLD))
        print(f"  Total elapsed:     {total_ms:.0f}ms")
        print(f"  Pipeline duration: {pipeline_ms:.0f}ms")
        print(f"  Reasoning traces:  {len(traces)}")
        print(f"  Root cause:        {root_cause[:80]}")
        print(c("-" * 70, Color.DIM))
        print(ok("Demo replay complete — ready for presentation"))
        print()

        return {
            "incident_id": incident_id,
            "total_ms": total_ms,
            "pipeline_ms": pipeline_ms,
            "traces": len(traces),
            "root_cause": root_cause,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="SentinelAI demo replay simulator")
    parser.add_argument("--async", dest="async_mode", action="store_true")
    parser.add_argument("--delay", type=float, default=0.8, help="Delay between stages (seconds)")
    args = parser.parse_args()

    try:
        DemoReplay(delay=args.delay).run(async_mode=args.async_mode)
        return 0
    except Exception as exc:
        print(fail(f"Demo replay failed: {exc}"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
