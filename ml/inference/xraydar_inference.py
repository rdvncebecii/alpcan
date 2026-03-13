"""X-Raydar — ResNet-50 + Transformer hybrid, 37 bulgu tespiti.

Lancet Digital Health, 2023. Model kodu herkese açık değil.
Bu modül ModelNotAvailableError fırlatır.
"""

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError


class XRaydarInference(BaseInferenceModel):
    """X-Raydar — model kodu mevcut değil.

    Lancet Digital Health 2023'te yayınlanan model kodu
    herkese açık paylaşılmamıştır. Yazarlarla iletişime geçildiğinde
    veya açık kaynak olduğunda bu modül güncellenecektir.
    """

    @classmethod
    def load_model(cls, config: dict) -> None:
        raise ModelNotAvailableError(
            "X-Raydar",
            "Model kodu herkese açık değil (Lancet Digital Health, 2023). "
            "Yazarlarla iletişim bekleniyor.",
        )

    @classmethod
    def predict(cls, image: np.ndarray) -> dict:
        raise ModelNotAvailableError(
            "X-Raydar",
            "Model kodu herkese açık değil.",
        )
