# AlpCAN Kaggle Notebook Bilgileri

## Kaggle Hesabı
- **Kullanıcı:** ridvancebec

## Notebook'lar

| # | Notebook | Kaggle Slug | Durum |
|---|---------|-------------|-------|
| 01 | LIDC-IDRI Exploration | ridvancebec/alpcan-lidc-idri-exploration | Complete |
| 02 | CXR TorchXRayVision | ridvancebec/alpcan-cxr-pipeline-torchxrayvision-baseline | Complete |
| 03 | CXR ResNet-50 | ridvancebec/alpcan-cxr-pipeline-resnet-50 | Complete |
| 04 | CXR MedSAM | ridvancebec/alpcan-cxr-pipeline-medsam | Complete |
| 05 | CXR Ark+ | ridvancebec/alpcan-cxr-pipeline-ark-plus | Complete |
| 06 | CT Nodule Segmentation | ridvancebec/alpcan-ct-nodule-segmentation | Complete |
| 07 | CT Characterization | ridvancebec/alpcan-ct-nodule-characterization | Complete |
| 08 | CXR Ensemble | ridvancebec/alpcan-cxr-ensemble-pipeline | Complete |
| 09 | CT Pipeline Integration | ridvancebec/alpcan-ct-pipeline-integration | Complete |
| 10 | System Performance Report | ridvancebec/alpcan-system-performance-report | Complete |
| 11 | nnU-Net Nodule Segmentation | ridvancebec/alpcan-nnu-net-nodule-segmentation | Queued (v6) |
| 12 | Turkish Report LLM | ridvancebec/alpcan-turkish-llm | Complete |
| 13 | Malignancy Classification | ridvancebec/alpcan-ct-malignancy-classification | Queued (v1) |
| 14 | Reporting Engine | ridvancebec/alpcan-reporting-engine | Complete |

## Kaggle CLI Komutları

### Status kontrol
```bash
kaggle kernels status ridvancebec/NOTEBOOK_SLUG
```

### Çıktıları indirme
```bash
kaggle kernels output ridvancebec/NOTEBOOK_SLUG -p notebooks/outputs/
```

### Notebook push
```bash
cd notebooks/kaggle_XX/
kaggle kernels push -p .
```

## Kaggle API Token
- **Konum:** ~/.kaggle/kaggle.json
- Token yoksa: kaggle.com > Account > Create New Token
