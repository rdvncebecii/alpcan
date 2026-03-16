"""YZ analiz (inference) endpoint'leri — Celery task dispatch."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.study import Study

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────────────────

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


# Agent tanımları
CXR_AGENTS = [
    {"name": "CXR Quality Control",   "dur": 1.2},
    {"name": "Ark+ Foundation",       "dur": 2.1},
    {"name": "TorchXRayVision",       "dur": 1.8},
    {"name": "X-Raydar",              "dur": 2.3},
    {"name": "MedRAX Segmentasyon",   "dur": 3.1},
]

CT_AGENTS = [
    {"name": "CT Quality Control",          "dur": 2.5},
    {"name": "DICOM Ön İşleme",             "dur": 8.0},
    {"name": "Nodül Tespiti (nnU-Net)",     "dur": 45.0},
    {"name": "Malignite Sınıflandırma",     "dur": 4.0},
    {"name": "Büyüme Takibi",               "dur": 6.0},
    {"name": "Türkçe Rapor LLM",           "dur": 15.0},
]


# ── POST /run ─────────────────────────────────────────────────────────────────

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
    # Analiz başlangıç zamanını kaydet
    study.quality_score = None  # reset
    # queued_at için study'ye ek alan yok; created_at'i proxy olarak kullanacağız
    # Bunun yerine task_id'yi study.study_instance_uid'nin sonuna ekliyoruz
    await db.commit()

    # Celery task başlat (Redis yoksa hata yakalanır, mock mod devreye girer)
    task_id: str
    try:
        from app.tasks import run_pipeline_task
        task = run_pipeline_task.delay(request.study_id, request.pipeline.value)
        task_id = task.id
    except Exception:
        # Celery/Redis yoksa mock task ID ile devam et
        import uuid
        task_id = f"mock-{uuid.uuid4().hex[:16]}"
        # Mock mod: study'yi hemen completed yap (simülasyon için)
        # task_id'yi bir yere saklamamız lazım — study_instance_uid suffix olarak
        study.study_instance_uid = (study.study_instance_uid or "") + f"::task::{task_id}"
        await db.commit()

    agents_def = CXR_AGENTS if request.pipeline == PipelineType.CXR else CT_AGENTS
    agents = [AgentResult(agent_name=a["name"], status="pending") for a in agents_def]

    return InferenceResponse(
        task_id=task_id,
        study_id=request.study_id,
        pipeline=request.pipeline,
        status="queued",
        agents=agents,
    )


# ── GET /status/{task_id} ─────────────────────────────────────────────────────

@router.get("/status/{task_id}")
async def get_inference_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Analiz durumunu sorgula.

    Önce Celery'den dener; Celery yoksa ya da task PENDING kalıyorsa
    DB'deki study.status'a bakarak gerçekçi mock progress döner.
    """
    # Mock task ID mi?
    is_mock = task_id.startswith("mock-")

    celery_status = "PENDING"
    celery_result = None

    if not is_mock:
        try:
            from app.core.queue import celery_app
            celery_result_obj = celery_app.AsyncResult(task_id)
            celery_status = celery_result_obj.status
            if celery_result_obj.ready():
                celery_result = celery_result_obj.result
            elif celery_status == "PROGRESS":
                return {
                    "task_id": task_id,
                    "status": "PROGRESS",
                    "progress": celery_result_obj.info,
                }
        except Exception:
            pass

    # Celery'den anlamlı sonuç geldiyse döndür
    if celery_status == "SUCCESS":
        return {"task_id": task_id, "status": "SUCCESS", "result": celery_result}
    if celery_status == "FAILURE":
        return {"task_id": task_id, "status": "FAILURE", "result": str(celery_result)}

    # Fallback: DB'deki study durumuna bak
    # task_id, study_instance_uid'nin sonunda saklı (mock mod) ya da study'yi tara
    result = await db.execute(
        select(Study).where(Study.study_instance_uid.contains(task_id))
    )
    study = result.scalar_one_or_none()

    if not study:
        # Mock değil, gerçek Celery PENDING durumu
        return {"task_id": task_id, "status": celery_status}

    # Study'nin durumuna göre sentetik ilerleme hesapla
    pipeline_type = study.pipeline_type or "cxr"
    agents_def = CXR_AGENTS if pipeline_type == "cxr" else CT_AGENTS
    total_duration = sum(a["dur"] for a in agents_def)

    if study.status == "completed":
        # Tamamlandı — SUCCESS döndür
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": {
                "study_id": study.id,
                "overall_lung_rads": study.overall_lung_rads,
                "pipeline_type": pipeline_type,
            },
        }

    if study.status == "error":
        return {"task_id": task_id, "status": "FAILURE", "result": "Pipeline hatası"}

    # queued / processing: elapsed time bazlı simülasyon
    # Study'nin created_at'ini başlangıç olarak kullan
    from datetime import datetime, timezone
    elapsed = (datetime.now(timezone.utc) - study.created_at).total_seconds()

    # Simüle edilmiş toplam süre (gerçek pipeline'ın %20'si)
    sim_total = total_duration * 0.2
    elapsed_sim = min(elapsed, sim_total * 0.95)

    # Hangi agent çalışıyor?
    cumulative = 0.0
    current_agent = agents_def[0]["name"]
    step = 0
    for i, ag in enumerate(agents_def):
        ag_sim_dur = ag["dur"] * 0.2
        cumulative += ag_sim_dur
        if elapsed_sim <= cumulative:
            current_agent = ag["name"]
            step = i
            break
        step = i + 1

    pct = min(int((elapsed_sim / sim_total) * 100), 95)

    return {
        "task_id": task_id,
        "status": "PROGRESS",
        "progress": {
            "current_agent": current_agent,
            "step": step + 1,
            "total_steps": len(agents_def),
            "percent": pct,
        },
    }
