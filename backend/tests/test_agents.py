import pytest
from app.agents.graph import run_incident_pipeline


@pytest.mark.asyncio
async def test_incident_pipeline():
    result = await run_incident_pipeline(
        incident_id="test-001",
        tenant_id="default",
        alert_title="High error rate on payment-api",
        alert_description="Error rate exceeded 3%",
        service="payment-api",
        severity="high",
    )
    assert result.get("pipeline_status") == "complete"
    assert result.get("root_cause_hypothesis")
    assert len(result.get("reasoning_traces", [])) > 0
