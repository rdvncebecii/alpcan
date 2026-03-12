"""Ajan 6 — BT Kalite Kontrol: EfficientNet-B0

BT kalite değerlendirmesi — slice kalınlığı, FOV, SNR, artefakt.
CPU ile <3 s/tarama.
"""

from app.agents.base import BaseAgent


class CTQualityAgent(BaseAgent):
    name = "CT Quality Control"
    version = "0.1.0"
    requires_gpu = False
    pipeline = "ct"

    QUALITY_THRESHOLDS = {
        "slice_thickness_max": 2.5,  # mm
        "fov_min": 300,  # mm
        "snr_min": 15,  # dB
        "artifact_score_max": 0.3,
    }

    def preprocess(self, input_data: dict) -> dict:
        """DICOM header'dan kalite parametrelerini çıkar."""
        # TODO: pydicom ile header okuma
        return {
            "slice_thickness": input_data.get("slice_thickness", 1.5),
            "fov": input_data.get("fov", 350),
            "status": "stub",
        }

    def predict(self, preprocessed: dict) -> dict:
        """EfficientNet-B0 ile kalite skorlama."""
        # TODO: Model inference
        return {
            "quality_score": 85,
            "slice_thickness_ok": True,
            "fov_ok": True,
            "snr_ok": True,
            "artifact_ok": True,
            "status": "stub",
        }

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
