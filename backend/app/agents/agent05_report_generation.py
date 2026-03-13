"""Ajan 5 — Rapor Üretimi: Template tabanlı (ilk sürüm)

Türkçe Lung-RADS 2022 yapılandırılmış rapor üretimi.
İlk sürüm: şablon tabanlı. Gelecek: Llama-3-8B-Instruct (Q4_K_M).
CPU ile <1 s/rapor (template), ~10-30 s (LLM).
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ReportGenerationAgent(BaseAgent):
    name = "Report Generation (Llama-3)"
    version = "0.2.0"
    requires_gpu = False
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """Tüm pipeline çıktılarını rapor verisi olarak topla."""
        return {
            "nodules": input_data.get("nodules", []),
            "nodule_results": input_data.get("nodule_results", []),
            "overall_lung_rads": input_data.get("overall_lung_rads", "1"),
            "growth_results": input_data.get("growth_results", []),
            "quality_score": input_data.get("quality_score"),
            "quality": input_data.get("quality", {}),
            "patient_id": input_data.get("patient_id", "ANON"),
            "study_id": input_data.get("study_id", ""),
        }

    def predict(self, preprocessed: dict) -> dict:
        """Template tabanlı Türkçe rapor oluştur."""
        from ml.inference.report_generation_inference import ReportGenerationInference

        if not ReportGenerationInference.is_loaded():
            ReportGenerationInference.load_model({"method": "template"})

        return ReportGenerationInference.predict(preprocessed)

    def postprocess(self, prediction: dict) -> dict:
        """Rapor çıktısını yapılandır."""
        return {
            "findings": {
                "report_text": prediction.get("report_text", ""),
                "summary_tr": prediction.get("summary_tr", ""),
                "recommendation_tr": prediction.get("recommendation_tr", ""),
                "lung_rads": prediction.get("lung_rads", "1"),
                "pdf_generated": False,
                "dicom_sr_generated": False,
            },
            "confidence": 1.0,
        }
