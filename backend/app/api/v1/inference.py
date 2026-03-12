from fastapi import APIRouter
from pydantic import BaseModel
from enum import Enum

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
async def run_inference(request: InferenceRequest):
    """YZ analizi başlat (CXR veya BT pipeline)."""
    # TODO: Celery task olarak kuyruğa ekle
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
        task_id="task-001",
        study_id=request.study_id,
        pipeline=request.pipeline,
        status="queued",
        agents=agents,
    )


@router.get("/status/{task_id}")
async def get_inference_status(task_id: str):
    """Analiz durumunu sorgula."""
    # TODO: Celery task durumunu kontrol et
    return {
        "task_id": task_id,
        "status": "processing",
        "progress": 45,
        "current_agent": "Nodule Detection (nnU-Net)",
    }
