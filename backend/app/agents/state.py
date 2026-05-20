"""Shared graph state for multi-agent communication."""

from datetime import datetime
from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
import operator


class MetricSnapshot(TypedDict, total=False):
    name: str
    value: float
    service: str
    is_anomaly: bool


class LogEntry(TypedDict, total=False):
    level: str
    message: str
    service: str
    trace_id: Optional[str]
    timestamp: str


class RemediationPlan(TypedDict, total=False):
    action_type: str
    parameters: dict[str, Any]
    priority: int
    requires_approval: bool
    rationale: str


class AgentTrace(TypedDict, total=False):
    agent: str
    step: str
    reasoning: str
    tool_calls: list[dict[str, Any]]
    tokens_used: int
    latency_ms: float
    timestamp: str


def merge_traces(left: list[AgentTrace], right: list[AgentTrace]) -> list[AgentTrace]:
    return left + right


def merge_plans(left: list[RemediationPlan], right: list[RemediationPlan]) -> list[RemediationPlan]:
    return left + right


class IncidentGraphState(TypedDict, total=False):
    """Shared state passed between all agents in the LangGraph pipeline."""

    # Identity
    incident_id: str
    tenant_id: str

    # Input signals
    alert_title: str
    alert_description: str
    service: str
    severity: str
    metrics: list[MetricSnapshot]
    logs: list[LogEntry]
    traces: list[dict[str, Any]]

    # Monitoring agent output
    anomalies_detected: list[dict[str, Any]]
    threshold_alerts: list[dict[str, Any]]
    latency_issues: list[dict[str, Any]]
    monitoring_summary: str

    # Investigation agent output
    root_cause_hypothesis: str
    root_cause_confidence: float
    correlated_events: list[dict[str, Any]]
    runbook_context: list[dict[str, Any]]
    architecture_context: list[dict[str, Any]]
    investigation_summary: str

    # Decision agent output
    remediation_plans: Annotated[list[RemediationPlan], merge_plans]
    selected_plan: Optional[RemediationPlan]
    decision_rationale: str
    risk_assessment: str

    # Execution agent output
    execution_results: list[dict[str, Any]]
    execution_success: bool
    rollback_required: bool

    # Reporting agent output
    incident_report: str
    post_mortem_draft: str
    lessons_learned: list[str]

    # Orchestration
    current_agent: str
    retry_count: int
    max_retries: int
    errors: Annotated[list[str], operator.add]
    reasoning_traces: Annotated[list[AgentTrace], merge_traces]
    execution_memory: dict[str, Any]
    should_continue: bool
    pipeline_status: str
