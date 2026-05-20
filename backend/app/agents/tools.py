"""Agent tool definitions for infrastructure operations."""

from typing import Any, Optional
import json

from langchain_core.tools import tool

from app.core.logging import get_logger

logger = get_logger(__name__)


@tool
def query_prometheus(metric: str, service: str, window: str = "5m") -> str:
    """Query Prometheus for metric data. Returns JSON with values and anomalies."""
    logger.info("tool_query_prometheus", metric=metric, service=service)
    # Mock response for development; wire to real Prometheus in production
    return json.dumps({
        "metric": metric,
        "service": service,
        "window": window,
        "values": [45.2, 48.1, 120.5, 115.3, 52.0],
        "p99_latency_ms": 245,
        "anomaly_detected": metric == "error_rate" or "latency" in metric,
    })


@tool
def search_logs(
    service: str,
    query: str,
    level: str = "error",
    limit: int = 50,
) -> str:
    """Search application logs for patterns. Returns matching log entries as JSON."""
    logger.info("tool_search_logs", service=service, query=query)
    return json.dumps({
        "service": service,
        "query": query,
        "entries": [
            {"level": "error", "message": f"Connection timeout to {service}-db", "trace_id": "abc123"},
            {"level": "error", "message": f"Pool exhausted for {service}", "trace_id": "def456"},
            {"level": "warn", "message": f"Retry attempt 3/3 for {service}", "trace_id": "ghi789"},
        ][:limit],
    })


@tool
def retrieve_runbook(incident_type: str, service: str) -> str:
    """Semantic retrieval of runbooks from vector store. Returns relevant procedures."""
    logger.info("tool_retrieve_runbook", incident_type=incident_type, service=service)
    return json.dumps({
        "runbooks": [
            {
                "title": f"{service} Database Connection Pool Exhaustion",
                "steps": [
                    "Check connection pool metrics",
                    "Identify long-running queries",
                    "Restart connection pool or scale replicas",
                    "Verify recovery within 5 minutes",
                ],
                "relevance_score": 0.92,
            }
        ],
    })


@tool
def retrieve_architecture_docs(component: str) -> str:
    """Retrieve architecture documentation for a system component."""
    logger.info("tool_retrieve_architecture", component=component)
    return json.dumps({
        "component": component,
        "dependencies": ["postgres", "redis", "kafka"],
        "sla": "99.9%",
        "on_call": "platform-team",
        "blast_radius": "payment-processing",
    })


@tool
def restart_kubernetes_pod(namespace: str, pod_name: str) -> str:
    """Restart a Kubernetes pod. Requires operator approval in production."""
    logger.info("tool_k8s_restart", namespace=namespace, pod= pod_name)
    return json.dumps({
        "action": "k8s_pod_restart",
        "namespace": namespace,
        "pod": pod_name,
        "status": "simulated_success",
        "message": f"Pod {pod_name} restarted in {namespace}",
    })


@tool
def rollback_ecs_service(cluster: str, service: str, revision: str) -> str:
    """Rollback ECS service to a previous task definition revision."""
    logger.info("tool_ecs_rollback", cluster=cluster, service=service)
    return json.dumps({
        "action": "ecs_rollback",
        "cluster": cluster,
        "service": service,
        "revision": revision,
        "status": "simulated_success",
    })


@tool
def trigger_autoscale(
    service: str,
    min_capacity: int,
    max_capacity: int,
    target_cpu: int = 70,
) -> str:
    """Trigger autoscaling for a service based on CPU/memory targets."""
    logger.info("tool_autoscale", service=service)
    return json.dumps({
        "action": "autoscale",
        "service": service,
        "min": min_capacity,
        "max": max_capacity,
        "target_cpu": target_cpu,
        "status": "simulated_success",
    })


@tool
def restart_service(service: str, environment: str = "production") -> str:
    """Restart a failed microservice."""
    logger.info("tool_restart_service", service=service)
    return json.dumps({
        "action": "service_restart",
        "service": service,
        "environment": environment,
        "status": "simulated_success",
    })


@tool
def reroute_traffic(
    service: str,
    from_region: str,
    to_region: str,
    percentage: int = 100,
) -> str:
    """Reroute traffic between regions or availability zones."""
    logger.info("tool_reroute_traffic", service=service)
    return json.dumps({
        "action": "traffic_reroute",
        "service": service,
        "from": from_region,
        "to": to_region,
        "percentage": percentage,
        "status": "simulated_success",
    })


MONITORING_TOOLS = [query_prometheus, search_logs]
INVESTIGATION_TOOLS = [query_prometheus, search_logs, retrieve_runbook, retrieve_architecture_docs]
EXECUTION_TOOLS = [
    restart_kubernetes_pod,
    rollback_ecs_service,
    trigger_autoscale,
    restart_service,
    reroute_traffic,
]
ALL_TOOLS = list({t.name: t for t in MONITORING_TOOLS + INVESTIGATION_TOOLS + EXECUTION_TOOLS}.values())
