"""YZ analiz (inference) endpoint'leri — Celery task dispatch."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.study import Study

router = APIRouter()


class PipelineType(str, Enum):
    CXR = "cxr"
    CT = "ct"


class InferenceRequest(BaseModel):
    study_id: str
    pipeline: PipelineType


class AgentResult(BaseModel):
    agent_name: str
    status: str
    confidence: float | None = None
    findings: dict | None = None
    duration_seconds: float | None = None


class InferenceResponse(BaseModel):
    task_id: str
    study_id: str
    pipeline: PipelineType
    status: str
    agents: list[AgentResult] = []


@router.post("/run", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    db: AsyncSession = Depends(get_db),
):
    """YZ analizi başlat (CXR veya BT pipeline)."""
    result = await db.execute(select(Study).where(Study.id == request.study_id))
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")

    if study.status == "processing":
        raise HTTPException(status_code=409, detail="Bu çalışma zaten işleniyor")

    study.status = "queued"
    study.pipeline_type = request.pipeline.value
    await db.commit()

    from app.tasks import run_pipeline_task

    task = run_pipeline_task.delay(request.study_id, request.pipeline.value)

    if request.pipeline == PipelineType.CXR:
        agents = [
            AgentResult(agent_name="CXR Quality Control", status="pending"),
            AgentResult(agent_name="Ark+ Foundation", status="pending"),
            AgentResult(agent_name="TorchXRayVision", status="pending"),
            AgentResult(agent_name="X-Raydar", status="pending"),
            AgentResult(agent_name="MedRAX", status="pending"),
        ]
    else:
        agents = [
            AgentResult(agent_name="CT Quality Control", status="pending"),
            AgentResult(agent_name="Preprocessing", status="pending"),
            AgentResult(agent_name="Nodule Detection (nnU-Net)", status="pending"),
            AgentResult(agent_name="Characterization", status="pending"),
            AgentResult(agent_name="Growth Tracking", status="pending"),
            AgentResult(agent_name="Report Generation", status="pending"),
        ]

    return InferenceResponse(
        task_id=task.id,
        study_id=request.study_id,
        pipeline=request.pipeline,
        status="queued",
        agents=agents,
    )


@router.get("/status/{task_id}")
async def get_inference_status(task_id: str):
    """Analiz durumunu sorgula (Celery task status)."""
    from app.core.queue import celery_app

    result = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.ready():
        response["result"] = result.result
    elif result.status == "PROGRESS":
        response["progress"] = result.info

    return response
