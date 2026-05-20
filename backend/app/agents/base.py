"""Base agent utilities: LLM, tracing, memory."""

import time
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentTrace, IncidentGraphState
from app.config import get_settings
from app.core.logging import get_logger
from app.core.observability import AGENT_INVOCATIONS, AGENT_LATENCY, TOKEN_USAGE

logger = get_logger(__name__)


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key or "sk-mock",
        temperature=temperature,
        timeout=settings.agent_timeout_seconds,
    )


def append_trace(
    state: IncidentGraphState,
    agent: str,
    step: str,
    reasoning: str,
    tool_calls: Optional[list[dict]] = None,
    tokens_used: int = 0,
    latency_ms: float = 0,
) -> list[AgentTrace]:
    trace: AgentTrace = {
        "agent": agent,
        "step": step,
        "reasoning": reasoning,
        "tool_calls": tool_calls or [],
        "tokens_used": tokens_used,
        "latency_ms": latency_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return [trace]


def record_agent_metrics(agent: str, status: str, duration: float, tokens: int = 0) -> None:
    AGENT_INVOCATIONS.labels(agent=agent, status=status).inc()
    AGENT_LATENCY.labels(agent=agent).observe(duration)
    if tokens:
        TOKEN_USAGE.labels(model=get_settings().openai_model, type="total").inc(tokens)


async def invoke_llm(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    state: IncidentGraphState,
) -> tuple[str, list[AgentTrace]]:
    start = time.perf_counter()
    settings = get_settings()

    try:
        if not settings.openai_api_key:
            # Deterministic mock for dev without API key
            response = _mock_llm_response(agent_name, user_prompt)
            tokens = 0
        else:
            llm = get_llm()
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            result = await llm.ainvoke(messages)
            response = result.content
            tokens = getattr(result, "usage_metadata", {}) or {}
            tokens = tokens.get("total_tokens", 500) if isinstance(tokens, dict) else 500

        duration = time.perf_counter() - start
        record_agent_metrics(agent_name, "success", duration, tokens)

        traces = append_trace(
            state,
            agent_name,
            "llm_inference",
            reasoning=response[:2000],
            tokens_used=tokens,
            latency_ms=duration * 1000,
        )
        return response, traces

    except Exception as e:
        duration = time.perf_counter() - start
        record_agent_metrics(agent_name, "error", duration)
        logger.error("agent_llm_error", agent=agent_name, error=str(e))
        raise


def _mock_llm_response(agent_name: str, prompt: str) -> str:
    mocks = {
        "monitoring": "Detected elevated error rate (3.2%) and p99 latency spike (450ms) on payment-api. Threshold alerts triggered for error_rate and latency.",
        "investigation": "Root cause: database connection pool exhaustion due to long-running analytics query. Confidence: 0.87. Correlated with deployment at 14:32 UTC.",
        "decision": "Recommended remediation: restart connection pool pods and scale read replicas. Risk: low. Requires approval for production restart.",
        "execution": "Executed k8s_pod_restart on payment-api pods. Autoscale triggered to 5 replicas. Service health restored.",
        "reporting": "Incident resolved in 12 minutes. Root cause confirmed. Post-mortem draft generated with 3 action items.",
    }
    return mocks.get(agent_name, f"Agent {agent_name} completed analysis.")
