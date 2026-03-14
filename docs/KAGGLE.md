# AlpCAN Kaggle Notebook Bilgileri

## Kaggle Hesabı
- **Kullanıcı:** ridvancebec
- **Profil:** https://www.kaggle.com/ridvancebec

## Notebook'lar

| Notebook | Kaggle Slug | Durum |
|----------|-------------|-------|
| Ark+ Zero-Shot | ridvancebec/alpcan-cxr-pipeline-ark-plus-zero-shot-baseline | Çalışıyor |
| CXR TorchXRayVision | ridvancebec/alpcan-cxr-pipeline-torchxrayvision-baseline | Çıktı var |
| LIDC-IDRI Exploration | ridvancebec/alpcan-lidc-idri-exploration | Çıktı var |
| MedSAM Segmentation | ridvancebec/alpcan-cxr-pipeline-medsam-segmentation-baseline | Çıktı var |
| ResNet-50 | ridvancebec/alpcan-cxr-pipeline-resnet-50-512-baseline | Çıktı var |

## Kaggle CLI Komutları

### Status kontrol
```bash
kaggle kernels status ridvancebec/alpcan-cxr-pipeline-ark-plus-zero-shot-baseline
```

### Çıktıları indirme
```bash
kaggle kernels output ridvancebec/alpcan-cxr-pipeline-ark-plus-zero-shot-baseline -p notebooks/outputs/ark/
```

### Notebook push
```bash
cd notebooks
kaggle kernels push -p .
```

## Kaggle API Token
- **Konum:** ~/.kaggle/kaggle.json
- Token yoksa: kaggle.com > Account > Create New Token
