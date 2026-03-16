# AlpCAN Kaggle Notebook Bilgileri

## Kaggle Hesabı
- **Kullanıcı:** rdvncebecii (doğrulamak için: `kaggle config view`)

## Notebook'lar

### 1. ark-foundation-lung-nodule-detection (Ark+ Foundation Model)
- **Kaggle slug:** rdvncebecii/ark-foundation-lung-nodule-detection
- **Durum:** v4 push edildi, ÇIKTI YOK (hata var, düzeltilmeli)
- **Sorun:** `ml.evaluation` import hatası veya model weight indirme problemi
- **Lokal dosya:** /Users/rdvncebeci/alpcan/notebooks/ark_foundation_lung_nodule_detection.ipynb
- **Çıktılar:** /Users/rdvncebeci/alpcan/notebooks/outputs/ark/ (boş)

### 2. Diğer Notebook'lar (çıktıları mevcut)
- LUNA16 analiz
- CXR DenseNet
- MedSAM segmentation
- ViT classification
- VFNet detection
- EfficientNet
- MONAI preprocessing

## Kaggle CLI Komutları

### Status kontrol
```bash
kaggle kernels status rdvncebecii/ark-foundation-lung-nodule-detection
```

### Notebook push (güncelleme sonrası)
```bash
cd /Users/rdvncebeci/alpcan/notebooks
kaggle kernels push -p . --kernel-name ark-foundation-lung-nodule-detection
```

### Çıktıları indirme
```bash
kaggle kernels output rdvncebecii/ark-foundation-lung-nodule-detection -p notebooks/outputs/ark/
```

### Yeni notebook push template
```bash
# 1. kernel-metadata.json oluştur (veya güncelle)
cat > kernel-metadata.json <<EOF
{
  "id": "rdvncebecii/NOTEBOOK_NAME",
  "title": "NOTEBOOK TITLE",
  "code_file": "notebook.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": false,
  "enable_gpu": true,
  "enable_internet": true,
  "competition_sources": [],
  "dataset_sources": []
}
EOF

# 2. Push
kaggle kernels push -p .
```

## Kaggle API Token
- **Konum:** ~/.kaggle/kaggle.json
- Token yoksa: kaggle.com > Account > Create New Token
