"""Ajan 6 — BT Kalite Kontrol: DICOM header analizi

BT kalite değerlendirmesi — dilim kalınlığı, FOV, SNR, artefakt.
CPU ile <3 s/tarama.
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class CTQualityAgent(BaseAgent):
    name = "CT Quality Control"
    version = "0.2.0"
    requires_gpu = False
    pipeline = "ct"

    QUALITY_THRESHOLDS = {
        "slice_thickness_max": 2.5,
        "fov_min": 300,
        "snr_min": 15,
        "artifact_score_max": 0.3,
    }

    def preprocess(self, input_data: dict) -> dict:
        """DICOM header'dan kalite parametrelerini çıkar."""
        dicom_path = input_data.get("dicom_path")
        metadata = input_data.get("metadata", {})

        if not metadata and dicom_path:
            from ml.preprocessing.dicom_utils import extract_dicom_metadata
            from pathlib import Path

            path = Path(dicom_path)
            dcm_files = list(path.glob("*.dcm")) if path.is_dir() else [path]
            if dcm_files:
                metadata = extract_dicom_metadata(dcm_files[0])

        return {"metadata": metadata, "dicom_path": dicom_path}

    def predict(self, preprocessed: dict) -> dict:
        """DICOM header analizi ile kalite skorlama."""
        from ml.inference.ct_quality_inference import CTQualityInference

        if not CTQualityInference.is_loaded():
            CTQualityInference.load_model(self.QUALITY_THRESHOLDS)

        return CTQualityInference.predict(
            metadata=preprocessed.get("metadata", {}),
            sample_slices=preprocessed.get("sample_slices"),
        )

    def postprocess(self, prediction: dict) -> dict:
        """Kalite kararı: GEÇTİ / UYARI / RED."""
        score = prediction.get("quality_score", 0)
        if score >= 80:
            decision = "GEÇTİ"
        elif score >= 50:
            decision = "UYARI"
        else:
            decision = "RED"

        return {
            "findings": {
                "quality_score": score,
                "decision": decision,
                "details": {
                    "slice_thickness_ok": prediction.get("slice_thickness_ok"),
                    "fov_ok": prediction.get("fov_ok"),
                    "snr_ok": prediction.get("snr_ok"),
                    "artifact_ok": prediction.get("artifact_ok"),
                },
            },
            "confidence": score / 100.0,
        }
