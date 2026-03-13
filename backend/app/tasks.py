"""Celery tasks — AlpCAN pipeline yürütme.

API → Celery task → Pipeline → DB kayıt akışı.
Celery worker process'inde çalışır (FastAPI process'inden ayrı).
"""

import logging
from datetime import datetime, timezone

from app.core.queue import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="alpcan.run_pipeline")
def run_pipeline_task(self, study_id: str, pipeline_type: str) -> dict:
    """Tam analiz pipeline'ı çalıştır (CXR veya BT).

    Celery worker'da çalışır. Async DB erişimi için event loop oluşturur.

    Args:
        study_id: Çalışma ID'si
        pipeline_type: "cxr" veya "ct"

    Returns:
        Pipeline sonuç dict'i
    """
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            _run_pipeline_async(self, study_id, pipeline_type)
        )
        return result
    finally:
        loop.close()


async def _run_pipeline_async(task, study_id: str, pipeline_type: str) -> dict:
    """Async pipeline yürütme — DB erişimi ve pipeline çalıştırma."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.core.database import async_session
    from app.models.study import Study

    async with async_session() as db:
        # Study'yi bul
        result = await db.execute(
            select(Study).options(selectinload(Study.patient)).where(Study.id == study_id)
        )
        study = result.scalar_one_or_none()
        if not study:
            logger.error(f"Study bulunamadı: {study_id}")
            return {"error": f"Study bulunamadı: {study_id}"}

        # Durumu güncelle
        study.status = "processing"
        await db.commit()

        try:
            if pipeline_type == "cxr":
                pipeline_result = await _run_cxr_pipeline(study, db)
            elif pipeline_type == "ct":
                pipeline_result = await _run_ct_pipeline(study, db)
            else:
                raise ValueError(f"Bilinmeyen pipeline tipi: {pipeline_type}")

            # Sonuçları DB'ye kaydet
            await _save_pipeline_results(study, pipeline_result, pipeline_type, db)

            study.status = "completed"
            study.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"Pipeline tamamlandı: study={study_id}, type={pipeline_type}")
            return pipeline_result

        except Exception as e:
            study.status = "error"
            await db.commit()
            logger.error(f"Pipeline hatası: study={study_id}, error={e}")
            return {"error": str(e), "study_id": study_id}


async def _run_cxr_pipeline(study, db) -> dict:
    """CXR pipeline'ını çalıştır."""
    from app.services.pipeline_cxr import CXRPipeline

    # Orthanc'tan görüntü al
    image_path = await _get_cxr_image(study, db)

    pipeline = CXRPipeline()
    return pipeline.run({"image_path": image_path, "study_id": study.id})


async def _run_ct_pipeline(study, db) -> dict:
    """BT pipeline'ını çalıştır."""
    from app.services.pipeline_bt import BTPipeline

    # Orthanc'tan DICOM serisi al
    dicom_path = await _get_ct_dicom(study, db)

    pipeline = BTPipeline()
    return pipeline.run({
        "dicom_path": dicom_path,
        "study_id": study.id,
        "patient_id": study.patient_id,
    })


async def _get_cxr_image(study, db) -> str:
    """Orthanc'tan CXR görüntüsünü indir ve geçici dosyaya kaydet."""
    import tempfile
    from app.services.dicom_service import DicomService

    svc = DicomService()
    study_data = await svc.get_study(study.study_instance_uid)

    if study_data:
        # Orthanc'tan ilk instance'ı al ve dosyaya kaydet
        import httpx

        series_list = study_data.get("Series", [])
        if series_list:
            async with httpx.AsyncClient() as client:
                # İlk seri, ilk instance
                series_resp = await client.get(
                    f"{svc.orthanc_url}/series/{series_list[0]}"
                )
                if series_resp.status_code == 200:
                    series_data = series_resp.json()
                    instances = series_data.get("Instances", [])
                    if instances:
                        img_resp = await client.get(
                            f"{svc.orthanc_url}/instances/{instances[0]}/file"
                        )
                        if img_resp.status_code == 200:
                            tmp = tempfile.NamedTemporaryFile(
                                suffix=".dcm", delete=False
                            )
                            tmp.write(img_resp.content)
                            tmp.close()
                            return tmp.name

    # Fallback: study_instance_uid ile geçici yol
    logger.warning(f"Orthanc'tan görüntü alınamadı: {study.study_instance_uid}")
    return f"/tmp/dicom/{study.study_instance_uid}.dcm"


async def _get_ct_dicom(study, db) -> str:
    """Orthanc'tan BT DICOM serisini indir."""
    import tempfile
    from pathlib import Path
    from app.services.dicom_service import DicomService

    svc = DicomService()
    study_data = await svc.get_study(study.study_instance_uid)

    if study_data:
        import httpx

        series_list = study_data.get("Series", [])
        if series_list:
            # Geçici dizin oluştur
            tmp_dir = tempfile.mkdtemp(prefix="alpcan_ct_")

            async with httpx.AsyncClient() as client:
                series_resp = await client.get(
                    f"{svc.orthanc_url}/series/{series_list[0]}"
                )
                if series_resp.status_code == 200:
                    series_data = series_resp.json()
                    instances = series_data.get("Instances", [])

                    for i, inst_id in enumerate(instances):
                        dcm_resp = await client.get(
                            f"{svc.orthanc_url}/instances/{inst_id}/file"
                        )
                        if dcm_resp.status_code == 200:
                            dcm_path = Path(tmp_dir) / f"slice_{i:04d}.dcm"
                            dcm_path.write_bytes(dcm_resp.content)

                    return tmp_dir

    logger.warning(f"Orthanc'tan DICOM serisi alınamadı: {study.study_instance_uid}")
    return f"/tmp/dicom/{study.study_instance_uid}/"


async def _save_pipeline_results(
    study, result: dict, pipeline_type: str, db
) -> None:
    """Pipeline sonuçlarını DB'ye kaydet (Nodule + Report)."""
    from app.models.nodule import Nodule
    from app.models.report import Report

    # Nodüller (BT pipeline'dan)
    if pipeline_type == "ct":
        nodules_data = result.get("agent_results", [])
        # Nodule Detection ajanının çıktısındaki nodüller
        for agent_result in nodules_data:
            if isinstance(agent_result, dict):
                findings = agent_result.get("findings", {})
                for nod in findings.get("nodules", []):
                    center = nod.get("center", [0, 0, 0])
                    nodule = Nodule(
                        study_id=study.id,
                        coord_x=float(center[0]) if len(center) > 0 else None,
                        coord_y=float(center[1]) if len(center) > 1 else None,
                        coord_z=float(center[2]) if len(center) > 2 else None,
                        diameter_mm=nod.get("diameter_mm", 0),
                        volume_mm3=nod.get("volume_mm3"),
                        density=nod.get("density"),
                        morphology=nod.get("morphology"),
                        malignancy_score=nod.get("malignancy_score"),
                        detection_confidence=nod.get("confidence"),
                        lung_rads_category=nod.get("lung_rads"),
                        agent_metadata=nod,
                    )
                    db.add(nodule)

    # Rapor
    overall_lr = result.get("overall_lung_rads", "1")
    study.overall_lung_rads = overall_lr
    study.quality_score = (
        result.get("quality", {}).get("quality_score")
        if isinstance(result.get("quality"), dict)
        else None
    )

    report = Report(
        study_id=study.id,
        overall_lung_rads=overall_lr,
        lung_rads_details=result.get("report", {}),
        total_processing_seconds=sum(
            ar.get("duration_seconds", 0)
            for ar in result.get("agent_results", [])
            if isinstance(ar, dict)
        ),
        agent_results=result.get("agent_results"),
    )

    # CXR pipeline sonuçları
    if pipeline_type == "cxr":
        report.cxr_ensemble_score = result.get("suspicious_votes")
        report.cxr_model_votes = result.get("model_votes")
        report.cxr_recommendation = result.get("recommendation")

    # Rapor metni (BT pipeline'da report ajanından gelir)
    report_findings = result.get("report", {})
    if isinstance(report_findings, dict):
        report.summary_tr = report_findings.get("summary_tr")
        report.recommendation_tr = report_findings.get("recommendation_tr")
        report.full_report_tr = report_findings.get("report_text")

    db.add(report)
    await db.commit()
