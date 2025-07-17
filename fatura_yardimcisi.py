# DOSYA ADI: fatura_yardimcisi.py
# YENİ ÖZELLİK: Açıklamalardaki '|' karakteri manuel olarak satır sonu ekler.

import os
from PIL import Image, ImageDraw, ImageFont
import re
import locale
import io
import traceback

def cm_to_px(cm_val, dpi=300):
    """Santimetreyi piksele çevirir (300 DPI varsayılan)."""
    return int((cm_val / 2.54) * dpi)

def wrap_text(draw, text, font, max_width_px):
    """
    Verilen metni, maksimum genişliği aşmayacak şekilde satırlara böler.
    Metin içindeki '\n' karakterlerini manuel satır sonu olarak kabul eder.
    """
    manual_lines = text.split('\n')
    
    wrapped_lines = []
    for line in manual_lines:
        if draw.textlength(line, font=font) <= max_width_px:
            wrapped_lines.append(line)
        else:
            words = line.split(' ')
            current_line = ''
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if draw.textlength(test_line, font=font) <= max_width_px:
                    current_line = test_line
                else:
                    wrapped_lines.append(current_line)
                    current_line = word
            if current_line:
                wrapped_lines.append(current_line)
            
    return '\n'.join(wrapped_lines)

def resimden_pdf_olustur(fatura_bilgileri, cikti_yolu):
    """
    Verilen fatura bilgileriyle bir arka plan resminin üzerine yazı yazar
    ve sonucu PDF olarak kaydeder.
    """
    try:
        proje_dizini = os.path.abspath(os.path.dirname(__file__))
        
        current_locale = fatura_bilgileri.get("current_locale", "de")
        sablon_resim_adi = f"fatura_{current_locale}.jpg"
        sablon_resim_yolu = os.path.join(proje_dizini, sablon_resim_adi)
        
        if not os.path.exists(sablon_resim_yolu):
            print(f"UYARI: {sablon_resim_adi} bulunamadı. Varsayılan olarak fatura_de.jpg kullanılıyor.")
            sablon_resim_yolu = os.path.join(proje_dizini, "fatura_de.jpg")
            if not os.path.exists(sablon_resim_yolu):
                raise FileNotFoundError(f"Varsayılan fatura_de.jpg dosyası da bulunamadı.")

        try:
                font_yolu = os.path.join(proje_dizini, "Roboto-Regular.ttf")
                font_normal = ImageFont.truetype(font_yolu, 38)
                font_buyuk = ImageFont.truetype(font_yolu, 38)
                font_kalem = ImageFont.truetype(font_yolu, 38)
        except IOError:
                print("UYARI: Roboto-Regular.ttf fontu bulunamadı. Varsayılan fontlar kullanılıyor.")
                font_normal = ImageFont.load_default()
                font_buyuk = ImageFont.load_default()
                font_kalem = ImageFont.load_default()

        koordinatlar_cm = {
            "musteri_firma_adi": (1.98, 4.8),
            "musteri_adres_baslangic_y": 5.2,
            "musteri_adres_x": 1.98,
            "musteri_adres_satir_araligi_cm": 0.45,
            "tarih": (16.70, 6.9),
            "sachbearbeiter": (16.70, 7.25),
            "completion_date": (2.0, 12.5),
            "construction_site": (8.1, 12.5),
            "fatura_no": (18.0, 12.5),
            "ausfuhrungsdatum": (2.0, 12.5),
            "gesamtbetrag": (19.5, 21.4),
            "kalem_baslangic_y": 14.5,
            "kalem_pos_x": 2.2,
            "kalem_menge_x": 3.8,
            "kalem_beschreibung_x": 6.4,
            "kalem_einzelpreis_x": 15.85,
            "kalem_gesamtpreis_x": 19.50,
            "satir_araligi_cm": 0.65
        }

        image = Image.open(sablon_resim_yolu)
        draw = ImageDraw.Draw(image)
        renk_siyah = (0, 0, 0)
        DPI = 300

        # Müşteri bilgileri
        musteri_adres_satirlari = fatura_bilgileri.get("musteri_adres_satirlari", [])
        draw.text((cm_to_px(koordinatlar_cm["musteri_firma_adi"][0], DPI), cm_to_px(koordinatlar_cm["musteri_firma_adi"][1], DPI)), fatura_bilgileri.get("musteri_adi", ""), font=font_normal, fill=renk_siyah)
        current_y_adres = koordinatlar_cm["musteri_adres_baslangic_y"]
        for adres_satiri in musteri_adres_satirlari:
            if adres_satiri.strip():
                draw.text((cm_to_px(koordinatlar_cm["musteri_adres_x"], DPI), cm_to_px(current_y_adres, DPI)), adres_satiri, font=font_normal, fill=renk_siyah)
                current_y_adres += koordinatlar_cm["musteri_adres_satir_araligi_cm"]
        
        # Fatura genel bilgileri
        draw.text((cm_to_px(koordinatlar_cm["fatura_no"][0], DPI), cm_to_px(koordinatlar_cm["fatura_no"][1], DPI)), fatura_bilgileri.get("fatura_no", ""), font=font_buyuk, fill=renk_siyah)
        draw.text((cm_to_px(koordinatlar_cm["tarih"][0], DPI), cm_to_px(koordinatlar_cm["tarih"][1], DPI)), fatura_bilgileri.get("tarih", ""), font=font_buyuk, fill=renk_siyah)
        draw.text((cm_to_px(koordinatlar_cm["sachbearbeiter"][0], DPI), cm_to_px(koordinatlar_cm["sachbearbeiter"][1], DPI)), fatura_bilgileri.get("sachbearbeiter", ""), font=font_buyuk, fill=renk_siyah)
        draw.text((cm_to_px(koordinatlar_cm["construction_site"][0], DPI), cm_to_px(koordinatlar_cm["construction_site"][1], DPI)), fatura_bilgileri.get("santiye", ""), font=font_buyuk, fill=renk_siyah)
        draw.text((cm_to_px(koordinatlar_cm["ausfuhrungsdatum"][0], DPI), cm_to_px(koordinatlar_cm["ausfuhrungsdatum"][1], DPI)), fatura_bilgileri.get("ausfuhrungsdatum", ""), font=font_buyuk, fill=renk_siyah)
        
        # Toplam tutar
        if current_locale == 'de':
            locale_str = 'de_DE'
            currency_symbol = ' €'
        elif current_locale == 'en':
            locale_str = 'en_US'
            currency_symbol = ' €'
        elif current_locale == 'tr':
            locale_str = 'tr_TR'
            currency_symbol = ' TL'
        else:
            locale_str = 'de_DE'
            currency_symbol = ' €'
        
        try:
            locale.setlocale(locale.LC_ALL, locale_str)
        except locale.Error:
            print(f"UYARI: '{locale_str}' locale ayarlanamadı. Varsayılan sayı formatı kullanılıyor.")
        
        genel_toplam_val = fatura_bilgileri.get('genel_toplam', 0.0)
        genel_toplam_str = locale.format_string("%.2f", genel_toplam_val, grouping=True)
        
        if current_locale in ['de', 'tr']:
             genel_toplam_str = genel_toplam_str.replace('.', 'X').replace(',', '.').replace('X', ',')
        else:
             pass

        if current_locale == 'de': 
            genel_toplam_str += " €"
        else: 
            genel_toplam_str += currency_symbol

        draw.text((cm_to_px(koordinatlar_cm["gesamtbetrag"][0], DPI), cm_to_px(koordinatlar_cm["gesamtbetrag"][1], DPI)), genel_toplam_str, font=font_buyuk, fill=renk_siyah, anchor="ra")
        
        
        mevcut_y_cm = koordinatlar_cm["kalem_baslangic_y"]
        kalemler = fatura_bilgileri.get("kalemler", [])
        
        aciklama_max_genislik_cm = koordinatlar_cm["kalem_einzelpreis_x"] - koordinatlar_cm["kalem_beschreibung_x"] - 0.2
        aciklama_max_genislik_px = cm_to_px(aciklama_max_genislik_cm, DPI)

        for i, kalem in enumerate(kalemler):
            pos = str(i + 1)
            original_aciklama = kalem['aciklama']

            processed_aciklama = original_aciklama.replace('|', '\n')
            
            match = re.match(r'^(.*?)\s*\(DE:.*?\)\s*\(EN:.*?\)$', processed_aciklama)
            if match:
                display_aciklama = match.group(1).strip()
            else:
                display_aciklama = processed_aciklama.strip()

            wrapped_aciklama = wrap_text(draw, display_aciklama, font_kalem, aciklama_max_genislik_px)
            
            menge_val = kalem['miktar']
            if menge_val == int(menge_val):
                menge_str = str(int(menge_val))
            else:
                menge_str = locale.format_string("%.2f", menge_val, grouping=True)
            
            if current_locale in ['de', 'tr']:
                menge_str = menge_str.replace('.', 'X').replace(',', '.').replace('X', ',')
            
            # Düzeltme: Miktar ve birimi her zaman birleştirerek göster.
            # is_goturu durumunda bile, eğer birim 'Pauschal' değilse göster, veya varsayılan bir birim ata.
            # NOT: Bu durumda 'Pauschal' birim fiyatın yanında görünecek.
            menge_birim_text = f"{menge_str} {kalem['birim']}"

            display_birim_fiyat = ""
            if kalem['is_goturu']:
                if current_locale == 'de': display_birim_fiyat = "Pauschal"
                elif current_locale == 'en': display_birim_fiyat = "Lump Sum"
                else: display_birim_fiyat = "Götürü"
            else:
                birim_fiyat_str = locale.format_string("%.2f", kalem['birim_fiyat'], grouping=True)
                if current_locale in ['de', 'tr']:
                    birim_fiyat_str = birim_fiyat_str.replace('.', 'X').replace(',', '.').replace('X', ',')
                display_birim_fiyat = birim_fiyat_str + currency_symbol
            
            gesamtpreis = locale.format_string("%.2f", kalem['satir_toplami'], grouping=True)
            if current_locale in ['de', 'tr']:
                gesamtpreis = gesamtpreis.replace('.', 'X').replace(',', '.').replace('X', ',')
            if current_locale == 'de': gesamtpreis += " €"
            else: gesamtpreis += currency_symbol

            mevcut_y_px = cm_to_px(mevcut_y_cm, DPI)
            
            draw.text((cm_to_px(koordinatlar_cm["kalem_pos_x"], DPI), mevcut_y_px), pos, font=font_kalem, fill=renk_siyah)
            draw.text((cm_to_px(koordinatlar_cm["kalem_menge_x"], DPI), mevcut_y_px), menge_birim_text, font=font_kalem, fill=renk_siyah)
            draw.multiline_text((cm_to_px(koordinatlar_cm["kalem_beschreibung_x"], DPI), mevcut_y_px), wrapped_aciklama, font=font_kalem, fill=renk_siyah, spacing=15)
            draw.text((cm_to_px(koordinatlar_cm["kalem_einzelpreis_x"], DPI), mevcut_y_px), display_birim_fiyat, font=font_kalem, fill=renk_siyah, anchor="ra")
            draw.text((cm_to_px(koordinatlar_cm["kalem_gesamtpreis_x"], DPI), mevcut_y_px), gesamtpreis, font=font_kalem, fill=renk_siyah, anchor="ra")

            satir_sayisi = wrapped_aciklama.count('\n') + 1
            mevcut_y_cm += koordinatlar_cm["satir_araligi_cm"] * satir_sayisi

        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(cikti_yolu, "PDF", resolution=300.0, quality=95)
        
        return True

    except Exception as e:
        print(f"PDF oluşturma hatası: {e}")
        traceback.print_exc()
        return False