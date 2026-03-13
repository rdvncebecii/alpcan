"""BT Kalite Kontrol — DICOM header ve görüntü analizi.

Deep learning modeli gerektirmez. DICOM metadata ve temel
görüntü istatistikleri ile kalite değerlendirmesi yapar.

Bağımlılıklar: numpy
"""

import logging

import numpy as np

from ml.inference.base import BaseInferenceModel

logger = logging.getLogger(__name__)


class CTQualityInference(BaseInferenceModel):
    """BT Kalite Kontrol — DICOM header analizi.

    Kontroller:
    1. Dilim kalınlığı: ≤ 2.5 mm (ince kesit zorunlu)
    2. FOV: ≥ 300 mm (tam akciğer kapsamı)
    3. SNR: ≥ 15 dB (temsili dilimlerden hesaplanır)
    4. Artefakt: yüksek intensite outlier oranı
    """

    _model = None
    _config: dict = {}

    @classmethod
    def load_model(cls, config: dict) -> None:
        """Konfigürasyon yükle."""
        cls._config = config
        cls._model = True
        logger.info("BT Kalite Kontrol hazır (header analizi modu)")

    @classmethod
    def predict(
        cls,
        metadata: dict,
        sample_slices: np.ndarray | None = None,
    ) -> dict:
        """BT kalitesini değerlendir.

        Args:
            metadata: DICOM metadata dict (extract_dicom_metadata çıktısı)
            sample_slices: Opsiyonel — temsili dilimler (SNR hesabı için)

        Returns:
            {
                "quality_score": int (0-100),
                "slice_thickness_ok": bool,
                "fov_ok": bool,
                "snr_ok": bool,
                "artifact_ok": bool,
                "details": {...},
            }
        """
        if not cls.is_loaded():
            cls.load_model({})

        max_thickness = cls._config.get("slice_thickness_max", 2.5)
        min_fov = cls._config.get("fov_min", 300)
        min_snr = cls._config.get("snr_min", 15)

        # 1. Dilim kalınlığı
        slice_thickness = metadata.get("slice_thickness", 0)
        slice_thickness_ok = 0 < slice_thickness <= max_thickness

        # 2. FOV (Field of View)
        fov = metadata.get("reconstruction_diameter", 0)
        if fov == 0:
            # Pixel spacing x satır sayısından hesapla
            pixel_spacing = metadata.get("pixel_spacing", [0, 0])
            rows = metadata.get("rows", 0)
            if pixel_spacing[0] > 0 and rows > 0:
                fov = pixel_spacing[0] * rows
        fov_ok = fov >= min_fov

        # 3. SNR (Signal-to-Noise Ratio)
        snr_value = 0.0
        snr_ok = True
        if sample_slices is not None and sample_slices.size > 0:
            # Basit SNR: ortalama / standart sapma
            mean_val = float(np.mean(sample_slices))
            std_val = float(np.std(sample_slices))
            if std_val > 0:
                snr_value = 20 * np.log10(abs(mean_val) / std_val)
            snr_ok = snr_value >= min_snr

        # 4. Artefakt kontrolü
        artifact_ok = True
        artifact_score = 0.0
        if sample_slices is not None and sample_slices.size > 0:
            # Yüksek intensite outlier oranı
            p99 = np.percentile(sample_slices, 99)
            p1 = np.percentile(sample_slices, 1)
            iqr = p99 - p1
            if iqr > 0:
                outlier_ratio = float(
                    np.sum((sample_slices > p99 + iqr) | (sample_slices < p1 - iqr))
                    / sample_slices.size
                )
                artifact_score = outlier_ratio
                artifact_ok = artifact_score < cls._config.get("artifact_score_max", 0.3)

        # Genel skor
        score = 0
        score += 30 if slice_thickness_ok else max(0, int((1 - slice_thickness / 5) * 30))
        score += 25 if fov_ok else max(0, int(fov / min_fov * 25))
        score += 25 if snr_ok else max(0, int(snr_value / min_snr * 25))
        score += 20 if artifact_ok else max(0, int((1 - artifact_score) * 20))

        return {
            "quality_score": min(100, max(0, score)),
            "slice_thickness_ok": slice_thickness_ok,
            "fov_ok": fov_ok,
            "snr_ok": snr_ok,
            "artifact_ok": artifact_ok,
            "details": {
                "slice_thickness": slice_thickness,
                "fov": round(fov, 1),
                "snr_db": round(snr_value, 2),
                "artifact_score": round(artifact_score, 4),
            },
        }
