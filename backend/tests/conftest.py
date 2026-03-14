"""Pytest fixtures — async SQLite in-memory DB + FastAPI test client."""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

# Models must be imported so Base.metadata has them
import app.models.patient  # noqa: F401
import app.models.study  # noqa: F401
import app.models.nodule  # noqa: F401
import app.models.report  # noqa: F401
import app.models.user  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncSession:
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """FastAPI async test client with overridden DB dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_patient(db_session: AsyncSession):
    """Insert and return a sample patient."""
    from app.models.patient import Patient

    patient = Patient(
        id=str(uuid.uuid4()),
        anonymous_id="TEST-001",
        age=58,
        sex="M",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient


@pytest.fixture
async def sample_study(db_session: AsyncSession, sample_patient):
    """Insert and return a sample study."""
    from app.models.study import Study

    study = Study(
        id=str(uuid.uuid4()),
        study_instance_uid=f"1.2.840.{uuid.uuid4().int}",
        patient_id=sample_patient.id,
        modality="CR",
        study_date=datetime.now(timezone.utc),
        description="PA Chest X-Ray",
        status="uploaded",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(study)
    await db_session.commit()
    await db_session.refresh(study)
    return study
