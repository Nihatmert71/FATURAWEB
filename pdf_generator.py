# DOSYA ADI: pdf_generator.py
# Bu dosya, ReportLab kütüphanesini kullanarak profesyonel fatura PDF'i oluşturur.

import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib import colors

def create_invoice_pdf(file_path, fatura, musteri, profil, kalemler, logo_path):
    """
    Verilen bilgilerle A4 boyutunda, nizami bir fatura PDF'i oluşturur.
    """
    doc = SimpleDocTemplate(
        file_path,
        pagesize=(21*cm, 29.7*cm),
        topMargin=1.8*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RightAlign', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='CenterAlign', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='CustomerAddress', fontSize=11, leading=14, spaceBefore=1.4*cm, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='InvoiceTitle', fontSize=17, fontName='Helvetica-Bold', spaceBefore=2.5*cm))

    story = []

    # --- BAŞLIK BÖLÜMÜ (Logo ve Firma Adresi) ---
    try:
        logo = Image(logo_path, width=4*cm, height=2*cm)
        logo.hAlign = 'RIGHT'
    except Exception:
        logo = Paragraph("Logo bulunamadı", styles['Normal'])

    # Firma ünvanını ve adresi sola, logoyu sağa yerleştiren tablo
    header_data = [[
        Paragraph(f"<b>{profil.firma_unvani}</b><br/>{profil.adres.replace('\n', '<br/>')}", styles['Normal']),
        logo
    ]]
    header_table = Table(header_data, colWidths=[10*cm, 7.5*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(header_table)
    story.append(Spacer(1, 1*cm))

    # --- MÜŞTERİ VE FATURA DETAYLARI ---
    # Müşteri adresi
    customer_address = Paragraph(f"{musteri.firma_adi}<br/>{musteri.adres.replace('\n', '<br/>')}", styles['CustomerAddress'])
    
    # Fatura detayları tablosu
    details_data = [
        ['Datum:', fatura.tarih.strftime('%d.%m.%Y')],
        ['Rechnungs-Nr.:', fatura.fatura_no],
        ['Leistungsdatum:', fatura.vade_tarihi.strftime('%d.%m.%Y') if fatura.vade_tarihi else ''],
        ['Baustelle:', fatura.santiye if fatura.santiye else ''],
        ['Sachbearbeiter:', fatura.sachbearbeiter if fatura.sachbearbeiter else '']
    ]
    details_table = Table(details_data, colWidths=[3.5*cm, 4*cm], hAlign='RIGHT')
    details_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    # Müşteri adresi ve fatura detaylarını yan yana koyan ana tablo
    customer_details_table = Table([[customer_address, details_table]], colWidths=[9.5*cm, 7.5*cm])
    customer_details_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(customer_details_table)
    
    # --- ANA İÇERİK ---
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("<b>Rechnung</b>", styles['h1']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Sehr geehrte Damen und Herren, wir erlauben uns, wie folgt Rechnung zu stellen:", styles['Normal']))
    story.append(Spacer(1, 1*cm))

    # --- FATURA KALEMLERİ TABLOSU ---
    table_header = ['POS', 'BESCHREIBUNG', 'MENGE', 'EINH.', 'EINZELPREIS', 'GESAMTPREIS']
    table_data = [table_header]
    
    for i, kalem in enumerate(kalemler):
        pos = str(i + 1)
        desc = Paragraph(kalem.aciklama, styles['Normal'])
        menge = f"{kalem.miktar:.2f}".replace('.', ',')
        einheit = kalem.birim
        einzelpreis = f"{kalem.birim_fiyat:.2f} €".replace('.', ',')
        gesamtpreis = f"{kalem.satir_toplami:.2f} €".replace('.', ',')
        table_data.append([pos, desc, menge, einheit, einzelpreis, gesamtpreis])

    items_table = Table(table_data, colWidths=[1.5*cm, 6.5*cm, 2*cm, 1.5*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'), # Miktar ve Fiyatları sağa hizala
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('TOPPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(items_table)
    story.append(Spacer(1, 1*cm))

    # --- TOPLAMLAR BÖLÜMÜ ---
    totals_data = [
        ['Zwischensumme Netto:', f"{fatura.ara_toplam:.2f} €".replace('.', ',')],
        ['zzgl. 19% MwSt.:', f"{fatura.kdv_tutari:.2f} €".replace('.', ',')],
        ['<b>GESAMTBETRAG:</b>', f"<b>{fatura.genel_toplam:.2f} €</b>".replace('.', ',')]
    ]
    totals_table = Table(totals_data, colWidths=[4*cm, 3.5*cm], hAlign='RIGHT')
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('TOPPADDING', (0,2), (-1,2), 6),
        ('LINEABOVE', (0,2), (-1,2), 1, colors.black),
    ]))
    story.append(totals_table)
    
    # Alt bilgi metinlerini en sona eklemek için Spacer kullanıyoruz
    story.append(Spacer(1, 4*cm))
    
    footer_text = f"""
    <b>Bankverbindung:</b> {profil.banka_adi} - IBAN: {profil.iban} - BIC: {profil.bic}<br/>
    <b>Steuernummer:</b> {profil.vergi_no} | <b>Amtsgericht:</b> Mainz | <b>HRB-Nr:</b> {profil.sirket_no}<br/><br/>
    <i>Zahlungshinweise: Bitte um Angabe der Rechnungsnummer als Verwendungsnummer.</i><br/>
    <i>Bitte bezahlen sie das rechnung innerhalb den 8-Werktagen.</i>
    """
    story.append(Paragraph(footer_text, styles['Normal']))

    # PDF'i oluştur
    doc.build(story)
