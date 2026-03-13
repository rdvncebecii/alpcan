"""ML Inference temel sınıfları.

Tüm inference modülleri bu sınıfları kullanır.
Web framework bağımlılığı yoktur — saf PyTorch/numpy.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class ModelNotAvailableError(Exception):
    """Model ağırlıkları veya implementasyonu henüz mevcut değil."""

    def __init__(self, model_name: str, reason: str):
        self.model_name = model_name
        self.reason = reason
        super().__init__(f"{model_name}: {reason}")


class BaseInferenceModel(ABC):
    """Tüm ML inference modüllerinin temel sınıfı.

    Kurallar:
    - Web framework bağımlılığı YOK (FastAPI, SQLAlchemy, Celery yok)
    - Girdi: numpy array veya torch tensor
    - Çıktı: plain dict
    - Thread-safe lazy singleton pattern
    """

    _model: Any = None
    _device: str = "cpu"
    _config: dict = {}

    @classmethod
    @abstractmethod
    def load_model(cls, config: dict) -> None:
        """Model ağırlıklarını belleğe yükle."""
        ...

    @classmethod
    def unload_model(cls) -> None:
        """Modeli bellekten kaldır."""
        if cls._model is not None:
            del cls._model
            cls._model = None
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            logger.info(f"{cls.__name__} model unloaded")

    @classmethod
    def is_loaded(cls) -> bool:
        """Model belleğe yüklü mü?"""
        return cls._model is not None

    @classmethod
    @abstractmethod
    def predict(cls, input_data: Any) -> dict:
        """Çıkarım yap. Model yüklü değilse load_model() çağrılmalı."""
        ...
