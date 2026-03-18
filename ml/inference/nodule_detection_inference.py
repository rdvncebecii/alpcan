"""NB06 U-Net — 2D CT nodül segmentasyonu.

smp.Unet(encoder=resnet34) ile her CT slice üzerinde nodül tespiti.
Lung maskesi içinde kalan slice'lar için slice-by-slice 2D inference.

Model: ct_seg_best_model.pth (280MB)
Giriş: (D, H, W) HU değerli 3D CT volume
Çıkış: Nodül listesi — merkez, çap, alan, slice indeksi
"""

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

HU_CENTER = -600
HU_WIDTH = 1500
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
INPUT_SIZE = 256
SEG_THRESHOLD = 0.5
MIN_NODULE_AREA = 20
MAX_NODULE_AREA = 8000


def _weights_path() -> Path:
    base = Path(os.environ.get(
        "ALPCAN_WEIGHTS_DIR",
        Path(__file__).parents[2] / "ml" / "weights"
    ))
    return base / "nb06_ct_seg" / "ct_seg_best_model.pth"


def _hu_window(slice_hu: np.ndarray) -> np.ndarray:
    vmin = HU_CENTER - HU_WIDTH / 2
    vmax = HU_CENTER + HU_WIDTH / 2
    return (np.clip(slice_hu, vmin, vmax) - vmin) / (vmax - vmin)


def _preprocess_slice(slice_2d: np.ndarray) -> "torch.Tensor":
    import cv2
    import torch
    gray = _hu_window(slice_2d.astype(np.float32))
    rgb = np.stack([gray, gray, gray], axis=-1)
    rgb = cv2.resize(rgb, (INPUT_SIZE, INPUT_SIZE))
    rgb = (rgb - IMAGENET_MEAN) / IMAGENET_STD
    return torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0).float()


def _extract_nodules(mask: np.ndarray, slice_idx: int,
                     orig_h: int, orig_w: int) -> list:
    from scipy import ndimage
    labeled, n_labels = ndimage.label(mask)
    scale = orig_h / INPUT_SIZE
    nodules = []
    for lid in range(1, n_labels + 1):
        comp = labeled == lid
        area = int(comp.sum())
        if not (MIN_NODULE_AREA <= area <= MAX_NODULE_AREA):
            continue
        ys, xs = np.where(comp)
        nodules.append({
            "slice_idx": slice_idx,
            "center_y": float(ys.mean() / INPUT_SIZE * orig_h),
            "center_x": float(xs.mean() / INPUT_SIZE * orig_w),
            "diameter_px": float(2 * np.sqrt(area / np.pi) * scale),
            "area_px": float(area * scale ** 2),
            "mask_resized": comp,
        })
    return nodules


def _merge_nearby_nodules(nodules: list, z_gap: int = 3) -> list:
    if not nodules:
        return []
    nodules = sorted(nodules, key=lambda n: (n["slice_idx"], n["center_y"], n["center_x"]))
    used = [False] * len(nodules)
    merged = []
    for i, n in enumerate(nodules):
        if used[i]:
            continue
        group = [n]
        used[i] = True
        for j in range(i + 1, len(nodules)):
            if used[j]:
                continue
            m = nodules[j]
            if (abs(m["slice_idx"] - n["slice_idx"]) <= z_gap
                    and abs(m["center_y"] - n["center_y"]) < 20
                    and abs(m["center_x"] - n["center_x"]) < 20):
                group.append(m)
                used[j] = True
        rep = group[0].copy()
        rep["center_y"] = float(np.mean([g["center_y"] for g in group]))
        rep["center_x"] = float(np.mean([g["center_x"] for g in group]))
        rep["diameter_px"] = float(np.max([g["diameter_px"] for g in group]))
        rep["area_px"] = float(np.mean([g["area_px"] for g in group]))
        rep["n_slices"] = len(group)
        merged.append(rep)
    return merged


class NoduleDetectionInference(BaseInferenceModel):
    """NB06 U-Net 2D — CT nodül segmentasyonu."""

    _model = None
    _device: str = "cpu"

    @classmethod
    def load_model(cls, config: dict) -> None:
        import torch
        import segmentation_models_pytorch as smp

        weights = _weights_path()
        if not weights.exists():
            raise ModelNotAvailableError(
                "NB06 U-Net",
                f"Ağırlık bulunamadı: {weights}  "
                "Sunucuya ml/weights/nb06_ct_seg/ct_seg_best_model.pth kopyalayın.",
            )

        cls._device = "cuda" if torch.cuda.is_available() else "cpu"
        model = smp.Unet(
            encoder_name="resnet34",
            encoder_weights=None,
            in_channels=3,
            classes=1,
            activation=None,
        )
        ckpt = torch.load(weights, map_location=cls._device)
        model.load_state_dict(ckpt.get("model_state_dict", ckpt))
        model.eval()
        model.to(cls._device)
        cls._model = model
        logger.info(f"NB06 U-Net yüklendi — {cls._device}")

    @classmethod
    def predict(
        cls,
        volume: np.ndarray,
        lung_mask: Optional[np.ndarray] = None,
    ) -> dict:
        """
        Args:
            volume: (D, H, W) HU değerleri
            lung_mask: (D, H, W) binary akciğer maskesi

        Returns:
            {
                "nodules": [{"slice_idx", "center_y", "center_x",
                             "diameter_px", "area_px", "n_slices"}, ...],
                "total_nodules": int,
                "processed_slices": int,
            }
        """
        import torch

        if not cls.is_loaded():
            cls.load_model({})

        D, H, W = volume.shape
        all_nodules = []
        processed = 0

        with torch.no_grad():
            for z in range(D):
                if lung_mask is not None and lung_mask[z].sum() < 100:
                    continue
                t = _preprocess_slice(volume[z]).to(cls._device)
                out = cls._model(t)
                prob = torch.sigmoid(out).cpu().numpy()[0, 0]
                mask = (prob > SEG_THRESHOLD).astype(np.uint8)
                if mask.sum() == 0:
                    continue
                all_nodules.extend(_extract_nodules(mask, z, H, W))
                processed += 1

        all_nodules = _merge_nearby_nodules(all_nodules)
        logger.info(f"Nodül tespiti: {len(all_nodules)} nodül / {processed} slice")
        return {
            "nodules": all_nodules,
            "total_nodules": len(all_nodules),
            "processed_slices": processed,
        }
