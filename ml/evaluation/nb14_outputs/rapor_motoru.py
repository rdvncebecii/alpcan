#!/usr/bin/env python3
"""AlpCAN RPT-1: Yapilandirilmis Radyoloji Rapor Motoru.

Bu modul, AlpCAN pipeline ciktilarindan otomatik yapilandirilmis
radyoloji raporu uretir. Bagimsiz olarak kullanilabilir.

Kullanim:
    from rapor_motoru import generate_report
    result = generate_report(pipeline_json)
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional


def generate_report(pipeline_json: dict) -> dict:
    """Pipeline JSON ciktisini alir, yapilandirilmis rapor uretir.

    Args:
        pipeline_json: Pipeline ciktisi. Beklenen alanlar:
            - hasta_id, hasta_adi, yas, cinsiyet, protokol_no
            - modalite: 'CXR' veya 'BT'
            - cxr_patolojiler: dict (patoloji -> olasilik)  [CXR icin]
            - bt_noduller: list of dict  [BT icin]

    Returns:
        dict: Rapor sonucu (bulgular, izlenim, aciliyet, takip, html, text)
    """
    modalite = pipeline_json.get('modalite', 'CXR')
    tarih = pipeline_json.get('tarih', datetime.now().strftime('%d.%m.%Y %H:%M'))

    # Hasta bilgisi
    hasta = {
        'hasta_id': pipeline_json.get('hasta_id', 'UNKNOWN'),
        'hasta_adi': pipeline_json.get('hasta_adi', 'Bilinmiyor'),
        'yas': int(pipeline_json.get('yas', 0)),
        'cinsiyet': pipeline_json.get('cinsiyet', '-'),
        'protokol_no': pipeline_json.get('protokol_no', '-'),
        'tarih': tarih,
        'klinik_bilgi': pipeline_json.get('klinik_bilgi', ''),
    }

    # CXR bulgu olusturma
    bulgular = []
    izlenim = []
    aciliyet = 'Normal'
    lung_rads = None
    takip = 'Rutin takip yeterlidir.'

    if modalite == 'CXR':
        patolojiler = pipeline_json.get('cxr_patolojiler', {})
        pozitif = {k: v for k, v in patolojiler.items() if v >= 0.5}
        if not pozitif:
            bulgular.append('Akciger parankiminde belirgin patolojik bulgu izlenmemistir.')
            izlenim.append('Normal gogus rontgenogrami.')
        else:
            for pat, prob in sorted(pozitif.items(), key=lambda x: -x[1]):
                bulgular.append(f'{pat}: AI skoru {prob:.2f}')
            izlenim.append(f'{len(pozitif)} adet patolojik bulgu saptanmistir.')
            if patolojiler.get('Pneumothorax', 0) >= 0.6:
                aciliyet = 'Kritik - Hemen Bildirim'
            elif patolojiler.get('Mass', 0) >= 0.7:
                aciliyet = 'Acil Konsultasyon'
            elif any(v >= 0.5 for v in patolojiler.values()):
                aciliyet = 'Takip Gerekli'

    elif modalite == 'BT':
        noduller = pipeline_json.get('bt_noduller', [])
        if not noduller:
            bulgular.append('Noduler lezyon saptanmamistir.')
            izlenim.append('Normal BT incelemesi.')
            lung_rads = '1'
        else:
            bulgular.append(f'{len(noduller)} adet nodul saptanmistir.')
            max_lr = '1'
            lr_order = {'1':0,'2':1,'3':2,'4A':3,'4B':4,'4X':5}
            for n in noduller:
                lr = n.get('lung_rads', '1')
                if lr_order.get(lr, 0) > lr_order.get(max_lr, 0):
                    max_lr = lr
                bulgular.append(
                    f"  Nodul: {n.get('lokasyon','?')} - "
                    f"{n.get('boyut_mm',0):.1f} mm - Lung-RADS {lr}"
                )
            lung_rads = max_lr
            izlenim.append(f'Lung-RADS Kategori {max_lr}.')

            lungrads_takip = {
                '1': 'Yillik tarama.',
                '2': 'Yillik tarama.',
                '3': '6 ay sonra kontrol.',
                '4A': '3 ay sonra kontrol veya PET/BT.',
                '4B': 'Biyopsi/PET-BT onerilir.',
                '4X': 'Acil cerrahi konsultasyon.',
            }
            takip = lungrads_takip.get(max_lr, 'Klinik korelasyon.')
            lungrads_aciliyet = {
                '1': 'Normal', '2': 'Normal', '3': 'Takip Gerekli',
                '4A': 'Takip Gerekli', '4B': 'Acil Konsultasyon',
                '4X': 'Kritik - Hemen Bildirim',
            }
            aciliyet = lungrads_aciliyet.get(max_lr, 'Normal')

    return {
        'hasta': hasta,
        'modalite': modalite,
        'bulgular': bulgular,
        'izlenim': izlenim,
        'aciliyet': aciliyet,
        'lung_rads': lung_rads,
        'takip_onerisi': takip,
        'pipeline_version': 'AlpCAN v1.0',
        'tarih': tarih,
    }


if __name__ == '__main__':
    # Ornek kullanim
    test_input = {
        'hasta_id': 'TEST-001',
        'hasta_adi': 'Test Hasta',
        'yas': 55,
        'cinsiyet': 'E',
        'protokol_no': 'TEST-P001',
        'modalite': 'CXR',
        'cxr_patolojiler': {
            'Consolidation': 0.82,
            'Pneumonia': 0.75,
            'Effusion': 0.45,
        },
    }
    result = generate_report(test_input)
    print(json.dumps(result, ensure_ascii=False, indent=2))
