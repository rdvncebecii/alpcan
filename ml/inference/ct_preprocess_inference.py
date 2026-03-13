"""BT Ön İşleme — DICOM'dan normalize 3D volume.

SimpleITK ve pydicom kullanarak tam preprocessing pipeline.
Model ağırlığı gerektirmez.

Bağımlılıklar: SimpleITK, pydicom, numpy, scipy
"""

import logging
from pathlib import Path

import numpy as np

from ml.inference.base import BaseInferenceModel

logger = logging.getLogger(__name__)


class CTPreprocessInference(BaseInferenceModel):
    """BT Ön İşleme pipeline'ı.

    DICOM serisi → normalize 3D volume:
    1. DICOM serisini oku (SimpleITK)
    2. Metadata çıkar (pydicom)
    3. HU normalizasyon [-1000, 400]
    4. İzotropik resampling 1mm³
    5. Akciğer maskesi çıkarımı
    """

    _model = None
    _config: dict = {}

    @classmethod
    def load_model(cls, config: dict) -> None:
        """Konfigürasyon yükle."""
        cls._config = config
        cls._model = True
        logger.info("BT Ön İşleme hazır")

    @classmethod
    def predict(cls, dicom_dir: str) -> dict:
        """Tam ön işleme pipeline'ını çalıştır.

        Args:
            dicom_dir: DICOM dosyalarını içeren dizin yolu

        Returns:
            {
                "volume": np.ndarray — normalize edilmiş 3D volume,
                "lung_mask": np.ndarray — binary akciğer maskesi,
                "metadata": dict — DICOM metadata,
                "original_shape": tuple,
                "resampled_shape": tuple,
                "spacing": tuple,
            }
        """
        if not cls.is_loaded():
            cls.load_model({})

        from ml.preprocessing.dicom_utils import (
            read_dicom_series,
            normalize_hu,
            resample_isotropic,
            extract_dicom_metadata,
        )
        from ml.preprocessing.lung_segmentation import extract_lung_mask

        dicom_path = Path(dicom_dir)
        hu_min = cls._config.get("hu_min", -1000)
        hu_max = cls._config.get("hu_max", 400)
        target_spacing = tuple(cls._config.get("target_spacing", [1.0, 1.0, 1.0]))
        lung_threshold = cls._config.get("lung_threshold_hu", -600)

        # 1. DICOM serisini oku
        logger.info(f"DICOM serisi okunuyor: {dicom_path}")
        volume, series_metadata = read_dicom_series(dicom_path)
        original_shape = volume.shape

        # 2. DICOM metadata çıkar (ilk dosyadan)
        dcm_files = list(dicom_path.glob("*.dcm"))
        if not dcm_files:
            dcm_files = list(dicom_path.iterdir())
        metadata = {}
        if dcm_files:
            metadata = extract_dicom_metadata(dcm_files[0])
        metadata.update(series_metadata)

        # 3. Akciğer maskesi (ham HU değerleri üzerinde)
        logger.info("Akciğer maskesi çıkarılıyor...")
        lung_mask_raw = extract_lung_mask(volume, threshold_hu=lung_threshold)

        # 4. HU normalizasyon
        logger.info(f"HU normalizasyon: [{hu_min}, {hu_max}]")
        volume_norm = normalize_hu(volume, hu_min=hu_min, hu_max=hu_max)

        # 5. İzotropik resampling
        original_spacing = series_metadata.get("spacing", (1.0, 1.0, 1.0))
        logger.info(f"Resampling: {original_spacing} → {target_spacing}")
        volume_resampled = resample_isotropic(
            volume_norm, original_spacing, target_spacing
        )

        # Akciğer maskesini de resample et
        lung_mask_resampled = resample_isotropic(
            lung_mask_raw.astype(np.float32), original_spacing, target_spacing
        )
        lung_mask_resampled = (lung_mask_resampled > 0.5).astype(bool)

        logger.info(
            f"Ön işleme tamamlandı: {original_shape} → {volume_resampled.shape}"
        )

        return {
            "volume": volume_resampled,
            "lung_mask": lung_mask_resampled,
            "metadata": metadata,
            "original_shape": original_shape,
            "resampled_shape": volume_resampled.shape,
            "spacing": target_spacing,
        }
