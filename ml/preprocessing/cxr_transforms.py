"""CXR (Akciğer Röntgeni) görüntü ön işleme dönüşümleri.

Her model farklı preprocessing gerektirir:
- Ark+: RGB, 768x768, ImageNet normalizasyon
- TorchXRayVision: Grayscale, 224x224, xrv.datasets.normalize
- MedSAM: RGB, SamProcessor
"""

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


def load_cxr_for_ark(image_path: str | Path, img_size: int = 768) -> "torch.Tensor":
    """Ark+ modeli için CXR görüntüsü hazırla.

    Notebook 05, cell 13'ten:
    - RGB, 768x768
    - ImageNet mean/std normalizasyon
    - Çıktı: (1, 3, 768, 768) torch tensor

    Args:
        image_path: Görüntü dosya yolu (PNG, JPEG veya DICOM)
        img_size: Hedef boyut (varsayılan 768)

    Returns:
        (1, 3, img_size, img_size) boyutunda torch tensor
    """
    import torch
    from torchvision import transforms
    from PIL import Image

    image_path = Path(image_path)

    # DICOM ise pixel_array'den oku
    if image_path.suffix.lower() == ".dcm":
        img_array = _load_dicom_pixels(image_path)
        img = Image.fromarray(img_array).convert("RGB")
    else:
        img = Image.open(image_path).convert("RGB")

    transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    tensor = transform(img).unsqueeze(0)  # (1, 3, H, W)
    return tensor


def load_cxr_for_xrv(
    image_path: str | Path, img_size: int = 224
) -> "torch.Tensor":
    """TorchXRayVision modeli için CXR görüntüsü hazırla.

    Notebook 02, cell 14'ten:
    - Grayscale
    - 224x224 resize
    - xrv.datasets.normalize ile [-1024, 1024] aralığına dönüştür
    - Çıktı: (1, 1, 224, 224) torch tensor

    Args:
        image_path: Görüntü dosya yolu
        img_size: Hedef boyut (varsayılan 224)

    Returns:
        (1, 1, img_size, img_size) boyutunda torch tensor
    """
    import torch
    import torchxrayvision as xrv
    from PIL import Image

    image_path = Path(image_path)

    if image_path.suffix.lower() == ".dcm":
        img_array = _load_dicom_pixels(image_path)
    else:
        img = Image.open(image_path).convert("L")
        img = img.resize((img_size, img_size), Image.LANCZOS)
        img_array = np.array(img, dtype=np.float32)

    # xrv normalizasyon: [0, 255] → [-1024, 1024]
    if img_array.max() > 1.0:
        img_array = xrv.datasets.normalize(img_array, 255)

    # (H, W) → (1, 1, H, W)
    if img_array.ndim == 2:
        img_array = img_array[np.newaxis, ...]

    # Resize if needed
    if img_array.shape[-1] != img_size or img_array.shape[-2] != img_size:
        from PIL import Image as PILImage

        resized = PILImage.fromarray(
            ((img_array[0] + 1024) / 2048 * 255).astype(np.uint8)
        ).resize((img_size, img_size), PILImage.LANCZOS)
        img_array = xrv.datasets.normalize(np.array(resized, dtype=np.float32), 255)
        img_array = img_array[np.newaxis, ...]

    tensor = torch.from_numpy(img_array).unsqueeze(0).float()  # (1, 1, H, W)
    return tensor


def load_cxr_for_medsam(image_path: str | Path) -> "PIL.Image.Image":
    """MedSAM modeli için CXR görüntüsü hazırla.

    RGB formatında PIL Image döner. SamProcessor ile işlenecek.

    Args:
        image_path: Görüntü dosya yolu

    Returns:
        RGB PIL Image
    """
    from PIL import Image

    image_path = Path(image_path)

    if image_path.suffix.lower() == ".dcm":
        img_array = _load_dicom_pixels(image_path)
        return Image.fromarray(img_array).convert("RGB")

    return Image.open(image_path).convert("RGB")


def load_cxr_from_dicom(dicom_path: str | Path) -> np.ndarray:
    """DICOM dosyasından CXR pixel array'i çıkar.

    Args:
        dicom_path: DICOM dosya yolu

    Returns:
        2D numpy array (H, W), uint8 [0, 255] aralığında
    """
    return _load_dicom_pixels(dicom_path)


def _load_dicom_pixels(dicom_path: str | Path) -> np.ndarray:
    """DICOM dosyasından pixel array oku ve [0, 255] uint8'e dönüştür."""
    import pydicom

    ds = pydicom.dcmread(str(dicom_path))
    pixel_array = ds.pixel_array.astype(np.float32)

    # Window/Level uygula (varsa)
    if hasattr(ds, "WindowCenter") and hasattr(ds, "WindowWidth"):
        center = float(
            ds.WindowCenter[0]
            if isinstance(ds.WindowCenter, (list, pydicom.multival.MultiValue))
            else ds.WindowCenter
        )
        width = float(
            ds.WindowWidth[0]
            if isinstance(ds.WindowWidth, (list, pydicom.multival.MultiValue))
            else ds.WindowWidth
        )
        lower = center - width / 2
        upper = center + width / 2
        pixel_array = np.clip(pixel_array, lower, upper)

    # [0, 255] aralığına normalize et
    p_min, p_max = pixel_array.min(), pixel_array.max()
    if p_max > p_min:
        pixel_array = (pixel_array - p_min) / (p_max - p_min) * 255.0
    else:
        pixel_array = np.zeros_like(pixel_array)

    # MONOCHROME1 ise ters çevir (beyaz arka plan)
    if getattr(ds, "PhotometricInterpretation", "") == "MONOCHROME1":
        pixel_array = 255.0 - pixel_array

    return pixel_array.astype(np.uint8)
