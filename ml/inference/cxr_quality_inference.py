"""CXR Kalite Kontrol — heuristik tabanlı.

Deep learning modeli gerektirmez. Görüntü işleme heuristikleri ile
netlik, pozisyon, rotasyon ve artefakt kontrolü yapar.

Bağımlılıklar: numpy, opencv-python-headless
"""

import logging

import numpy as np

from ml.inference.base import BaseInferenceModel

logger = logging.getLogger(__name__)


class CXRQualityInference(BaseInferenceModel):
    """CXR Kalite Kontrol — heuristik tabanlı.

    Kontroller:
    1. Netlik: Laplacian varyans > eşik (100)
    2. Dinamik aralık: histogram genişliği > 50
    3. Boyut: minimum 256x256 piksel
    4. Rotasyon: yatay simetri analizi
    5. Artefakt: yüksek frekanslı gürültü tespiti
    """

    _model = None  # Model yok, heuristik
    _config: dict = {}

    @classmethod
    def load_model(cls, config: dict) -> None:
        """Konfigürasyon yükle (model yüklenmez)."""
        cls._config = config
        cls._model = True  # is_loaded() için
        logger.info("CXR Kalite Kontrol hazır (heuristik mod)")

    @classmethod
    def predict(cls, image: np.ndarray) -> dict:
        """CXR görüntü kalitesini değerlendir.

        Args:
            image: Grayscale numpy array (H, W), uint8 veya float

        Returns:
            {
                "quality_score": int (0-100),
                "sharpness_ok": bool,
                "dynamic_range_ok": bool,
                "size_ok": bool,
                "rotation_ok": bool,
                "artifact_ok": bool,
                "details": {...},
            }
        """
        if not cls.is_loaded():
            cls.load_model({})

        import cv2

        # uint8'e dönüştür
        if image.dtype != np.uint8:
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)

        # 2D kontrolü
        if image.ndim == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        h, w = image.shape
        laplacian_threshold = cls._config.get("laplacian_threshold", 100.0)
        min_size = cls._config.get("min_image_size", 256)
        min_dynamic_range = cls._config.get("min_dynamic_range", 50)

        # 1. Netlik — Laplacian varyans
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        laplacian_var = float(laplacian.var())
        sharpness_ok = laplacian_var > laplacian_threshold

        # 2. Dinamik aralık — histogram genişliği
        p5, p95 = float(np.percentile(image, 5)), float(np.percentile(image, 95))
        dynamic_range = p95 - p5
        dynamic_range_ok = dynamic_range > min_dynamic_range

        # 3. Boyut kontrolü
        size_ok = h >= min_size and w >= min_size

        # 4. Rotasyon — yatay simetri analizi
        # Sol ve sağ yarının ortalama yoğunluğunu karşılaştır
        left_half = image[:, : w // 2]
        right_half = image[:, w // 2 :]
        # Sağ yarıyı aynala
        right_flipped = np.fliplr(right_half)
        min_w = min(left_half.shape[1], right_flipped.shape[1])
        symmetry_diff = float(
            np.abs(
                left_half[:, :min_w].astype(float)
                - right_flipped[:, :min_w].astype(float)
            ).mean()
        )
        rotation_ok = symmetry_diff < 30.0  # Ortalama fark < 30

        # 5. Artefakt — kenar bölgelerde yüksek yoğunluk kontrolü
        border_width = max(10, min(h, w) // 20)
        border_mean = float(
            np.mean([
                image[:border_width, :].mean(),
                image[-border_width:, :].mean(),
                image[:, :border_width].mean(),
                image[:, -border_width:].mean(),
            ])
        )
        # Normal CXR'da kenarlar genellikle koyu (düşük değer)
        artifact_ok = border_mean < 200

        # Genel skor hesapla (0-100)
        score = 0
        score += 30 if sharpness_ok else max(0, int(laplacian_var / laplacian_threshold * 30))
        score += 20 if dynamic_range_ok else max(0, int(dynamic_range / min_dynamic_range * 20))
        score += 20 if size_ok else 10
        score += 15 if rotation_ok else max(0, int((1 - symmetry_diff / 60) * 15))
        score += 15 if artifact_ok else 5

        return {
            "quality_score": min(100, max(0, score)),
            "sharpness_ok": sharpness_ok,
            "dynamic_range_ok": dynamic_range_ok,
            "size_ok": size_ok,
            "rotation_ok": rotation_ok,
            "artifact_ok": artifact_ok,
            "details": {
                "laplacian_variance": round(laplacian_var, 2),
                "dynamic_range": round(dynamic_range, 2),
                "image_size": [h, w],
                "symmetry_diff": round(symmetry_diff, 2),
                "border_mean": round(border_mean, 2),
            },
        }
