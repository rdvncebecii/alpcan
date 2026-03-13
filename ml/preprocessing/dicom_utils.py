"""DICOM okuma, HU normalizasyon, izotropik resampling, anonimleştirme.

Bağımlılıklar: SimpleITK, pydicom, numpy, scipy
Web framework bağımlılığı yoktur.
"""

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Anonimleştirilecek DICOM tag'leri
PHI_TAGS = [
    "PatientName",
    "PatientBirthDate",
    "PatientAddress",
    "InstitutionName",
    "InstitutionAddress",
    "ReferringPhysicianName",
    "PhysicianOfRecord",
    "PerformingPhysicianName",
    "OperatorsName",
    "OtherPatientIDs",
    "OtherPatientNames",
    "PatientTelephoneNumbers",
]


def read_dicom_series(dicom_dir: str | Path) -> tuple[np.ndarray, dict]:
    """DICOM serisini oku ve 3D numpy volume olarak döndür.

    Args:
        dicom_dir: DICOM dosyalarını içeren dizin yolu

    Returns:
        (volume, metadata) — volume: (D, H, W) numpy array, metadata: spacing, origin vs.
    """
    import SimpleITK as sitk

    dicom_dir = Path(dicom_dir)
    if not dicom_dir.is_dir():
        raise FileNotFoundError(f"DICOM dizini bulunamadı: {dicom_dir}")

    reader = sitk.ImageSeriesReader()
    dicom_files = reader.GetGDCMSeriesFileNames(str(dicom_dir))
    if not dicom_files:
        raise ValueError(f"DICOM dosyası bulunamadı: {dicom_dir}")

    reader.SetFileNames(dicom_files)
    reader.MetaDataDictionaryArrayUpdateOn()
    reader.LoadPrivateTagsOn()
    image = reader.Execute()

    volume = sitk.GetArrayFromImage(image)  # (D, H, W)
    spacing = image.GetSpacing()  # (x, y, z)
    origin = image.GetOrigin()
    direction = image.GetDirection()

    metadata = {
        "spacing": spacing,
        "origin": origin,
        "direction": direction,
        "size": image.GetSize(),
        "slice_count": volume.shape[0],
        "pixel_type": image.GetPixelIDTypeAsString(),
    }

    logger.info(
        f"DICOM serisi okundu: {volume.shape}, spacing={spacing}, "
        f"{len(dicom_files)} dosya"
    )
    return volume, metadata


def normalize_hu(
    volume: np.ndarray,
    hu_min: int = -1000,
    hu_max: int = 400,
) -> np.ndarray:
    """HU değerlerini [0, 1] aralığına normalize et.

    Args:
        volume: Ham HU değerli 3D numpy array
        hu_min: Minimum HU değeri (alt kırpma)
        hu_max: Maximum HU değeri (üst kırpma)

    Returns:
        [0, 1] aralığında normalize edilmiş volume
    """
    volume = np.clip(volume, hu_min, hu_max).astype(np.float32)
    volume = (volume - hu_min) / (hu_max - hu_min)
    return volume


def resample_isotropic(
    volume: np.ndarray,
    original_spacing: tuple[float, float, float],
    target_spacing: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> np.ndarray:
    """İzotropik yeniden örnekleme.

    Args:
        volume: 3D numpy array (D, H, W)
        original_spacing: Orijinal voxel spacing (x, y, z) mm
        target_spacing: Hedef voxel spacing (x, y, z) mm

    Returns:
        Yeniden örneklenmiş 3D volume
    """
    from scipy.ndimage import zoom

    # Spacing oranları (SimpleITK spacing: x, y, z → numpy index: z, y, x)
    resize_factor = np.array(
        [original_spacing[2], original_spacing[1], original_spacing[0]]
    ) / np.array([target_spacing[2], target_spacing[1], target_spacing[0]])

    new_shape = np.round(np.array(volume.shape) * resize_factor).astype(int)
    zoom_factors = new_shape / np.array(volume.shape)

    resampled = zoom(volume.astype(np.float32), zoom_factors, order=1)
    logger.info(f"Resampled: {volume.shape} → {resampled.shape}")
    return resampled


def extract_dicom_metadata(dicom_path: str | Path) -> dict:
    """Tek bir DICOM dosyasından hasta/çalışma metadata'sı çıkar.

    Args:
        dicom_path: DICOM dosya yolu

    Returns:
        dict: patient_id, patient_name, study_uid, series_uid, modality, vs.
    """
    import pydicom

    ds = pydicom.dcmread(str(dicom_path), stop_before_pixels=True)

    return {
        "patient_id": str(getattr(ds, "PatientID", "UNKNOWN")),
        "patient_name": str(getattr(ds, "PatientName", "")),
        "patient_age": str(getattr(ds, "PatientAge", "")),
        "patient_sex": str(getattr(ds, "PatientSex", "")),
        "study_instance_uid": str(getattr(ds, "StudyInstanceUID", "")),
        "series_instance_uid": str(getattr(ds, "SeriesInstanceUID", "")),
        "sop_instance_uid": str(getattr(ds, "SOPInstanceUID", "")),
        "modality": str(getattr(ds, "Modality", "")),
        "study_date": str(getattr(ds, "StudyDate", "")),
        "study_description": str(getattr(ds, "StudyDescription", "")),
        "slice_thickness": float(getattr(ds, "SliceThickness", 0)),
        "pixel_spacing": [float(x) for x in getattr(ds, "PixelSpacing", [0, 0])],
        "rows": int(getattr(ds, "Rows", 0)),
        "columns": int(getattr(ds, "Columns", 0)),
        "bits_allocated": int(getattr(ds, "BitsAllocated", 0)),
        "photometric_interpretation": str(
            getattr(ds, "PhotometricInterpretation", "")
        ),
        "reconstruction_diameter": float(
            getattr(ds, "ReconstructionDiameter", 0)
        ),
    }


def anonymize_dicom(dicom_path: str | Path) -> "pydicom.Dataset":
    """DICOM dosyasından PHI (Protected Health Information) kaldır.

    Args:
        dicom_path: DICOM dosya yolu

    Returns:
        Anonimleştirilmiş pydicom Dataset
    """
    import pydicom

    ds = pydicom.dcmread(str(dicom_path))
    for tag_name in PHI_TAGS:
        if hasattr(ds, tag_name):
            delattr(ds, tag_name)

    # PatientID'yi anonim yap
    if hasattr(ds, "PatientID"):
        import hashlib

        original_id = str(ds.PatientID)
        ds.PatientID = "ANON-" + hashlib.sha256(original_id.encode()).hexdigest()[:8]

    return ds
