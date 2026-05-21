"""ORM model relationship and schema validation tests."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import configure_mappers

from app.db.base import Base
from app.models.incident import Incident, IncidentSeverity, IncidentStatus, ReasoningTrace

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def test_mapper_configuration_succeeds():
    """Ensure all ORM mappers configure without NoForeignKeysError."""
    configure_mappers()


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_incident_owns_multiple_reasoning_traces(db_session: AsyncSession):
    incident = Incident(
        id="inc-001",
        tenant_id="default",
        title="Test incident",
        status=IncidentStatus.OPEN,
        severity=IncidentSeverity.HIGH,
        service="test-service",
    )
    db_session.add(incident)
    await db_session.flush()

    traces = [
        ReasoningTrace(
            id=f"trace-{i}",
            incident_id=incident.id,
            tenant_id="default",
            agent_name=agent,
            step=f"step-{i}",
            reasoning=f"Reasoning from {agent}",
        )
        for i, agent in enumerate(["monitoring", "investigation", "decision"], start=1)
    ]
    db_session.add_all(traces)
    await db_session.commit()

    result = await db_session.execute(select(Incident).where(Incident.id == "inc-001"))
    loaded = result.scalar_one()
    assert len(loaded.reasoning_traces) == 3
    assert {t.agent_name for t in loaded.reasoning_traces} == {
        "monitoring",
        "investigation",
        "decision",
    }


@pytest.mark.asyncio
async def test_reasoning_trace_incident_relationship(db_session: AsyncSession):
    incident = Incident(
        id="inc-002",
        tenant_id="default",
        title="Relationship test",
        status=IncidentStatus.INVESTIGATING,
        severity=IncidentSeverity.MEDIUM,
    )
    trace = ReasoningTrace(
        id="trace-100",
        incident_id="inc-002",
        tenant_id="default",
        agent_name="execution",
        step="execute",
        reasoning="Applied remediation",
    )
    db_session.add(incident)
    db_session.add(trace)
    await db_session.commit()

    result = await db_session.get(ReasoningTrace, "trace-100")
    assert result is not None
    assert result.incident is not None
    assert result.incident.id == "inc-002"
    assert result.incident.title == "Relationship test"


@pytest.mark.asyncio
async def test_cascade_delete_orphan_traces(db_session: AsyncSession):
    incident = Incident(
        id="inc-003",
        tenant_id="default",
        title="Cascade delete test",
        status=IncidentStatus.OPEN,
        severity=IncidentSeverity.LOW,
    )
    trace = ReasoningTrace(
        id="trace-200",
        incident_id="inc-003",
        tenant_id="default",
        agent_name="reporting",
        step="report",
        reasoning="Final report",
    )
    db_session.add(incident)
    db_session.add(trace)
    await db_session.commit()

    await db_session.delete(incident)
    await db_session.commit()

    orphan = await db_session.get(ReasoningTrace, "trace-200")
    assert orphan is None


@pytest.mark.asyncio
async def test_orm_join_compiles(db_session: AsyncSession):
    stmt = (
        select(Incident)
        .join(ReasoningTrace, ReasoningTrace.incident_id == Incident.id)
        .where(ReasoningTrace.agent_name == "monitoring")
    )
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "reasoning_traces" in compiled
    assert "incidents" in compiled
