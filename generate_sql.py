# -*- coding: utf-8 -*-
# generate_sql.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import CreateTable
from datetime import datetime

# UYGULAMA VE VERİTABANI KURULUMU
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# VERİTABANI MODELLERİ (app.py dosyanızdan kopyalandı)
class SirketProfili(db.Model):
    __tablename__ = 'sirket_profili'
    id = db.Column(db.Integer, primary_key=True)
    firma_unvani = db.Column(db.String(200), default="PFÄLZER BODENBAU&SANIERUNG GmbH")
    adres = db.Column(db.String(300), default="Mergenthaler Allee 15-21\n65760 Eschborn")
    telefon = db.Column(db.String(50), default="0176-1234567")
    email = db.Column(db.String(120), default="info@pfaelzer-bodenbau-sanierung.com")
    web_adresi = db.Column(db.String(120), default="www.pfaelzer-bau-saniereung.com")
    iban = db.Column(db.String(50), default="LT03 3250 0744 3938 2376")
    bic = db.Column(db.String(50), default="REVOLT21")
    vergi_no = db.Column(db.String(50), default="44 665")
    sirket_no = db.Column(db.String(50), default="HRB-Nr. 49351")
    banka_adi = db.Column(db.String(100), default="OONTO.")

class Musteri(db.Model):
    __tablename__ = 'musteri'
    id = db.Column(db.Integer, primary_key=True)
    firma_adi = db.Column(db.String(150), nullable=False)
    adres = db.Column(db.String(300), nullable=False)
    vergi_no = db.Column(db.String(50), nullable=True)
    telefon = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    ilgili_kisi = db.Column(db.String(100), nullable=True)
    web_adresi = db.Column(db.String(120), nullable=True)
    notlar = db.Column(db.Text, nullable=True)
    is_reverse_charge = db.Column(db.Boolean, default=False)

class Urun(db.Model):
    __tablename__ = 'urun'
    id = db.Column(db.Integer, primary_key=True)
    aciklama = db.Column(db.String(500), nullable=False)
    birim = db.Column(db.String(50), nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    is_goturu = db.Column(db.Boolean, default=False)

class Fatura(db.Model):
    __tablename__ = 'fatura'
    id = db.Column(db.Integer, primary_key=True)
    fatura_no = db.Column(db.String(50), nullable=False, unique=True)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    ausfuhrungsdatum = db.Column(db.DateTime, nullable=True)
    santiye = db.Column(db.String(200), nullable=True)
    sachbearbeiter = db.Column(db.String(100), nullable=True)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=False)
    ara_toplam = db.Column(db.Float, nullable=False, default=0.0)
    kdv_tutari = db.Column(db.Float, nullable=False, default=0.0)
    genel_toplam = db.Column(db.Float, nullable=False, default=0.0)
    odeme_durumu = db.Column(db.String(50), default="Bekliyor", nullable=False)
    is_reverse_charge_invoice = db.Column(db.Boolean, default=False)

class FaturaKalemi(db.Model):
    __tablename__ = 'fatura_kalemi'
    id = db.Column(db.Integer, primary_key=True)
    aciklama = db.Column(db.String(500), nullable=False)
    miktar = db.Column(db.Float, nullable=False)
    birim = db.Column(db.String(50), nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    satir_toplami = db.Column(db.Float, nullable=False)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=False)
    is_goturu = db.Column(db.Boolean, default=False)

# SQL CREATE TABLE komutlarını ve INSERT komutlarını üret
# ve doğrudan bir dosyaya yaz
output_filename = "sql_commands.sql"

with app.app_context():
    metadata = db.metadata
    
    with open(output_filename, "w", encoding="utf-8") as f: # Dosyaya yazma modu
        f.write("-- SQL DDL for Table Creation --\n")
        f.write("BEGIN;\n")
        for table in metadata.sorted_tables:
            # PostgreSQL için DATETIME yerine TIMESTAMP kullanılması düzeltildi
            ddl_sql = str(CreateTable(table).compile(db.engine)).replace("DATETIME", "TIMESTAMP")
            f.write(ddl_sql)
            f.write(";\n")
        f.write("COMMIT;\n")

        f.write("\n-- SQL DML for Initial Data Insertion --\n")
        f.write("BEGIN;\n")
        # Şirket Profili (SirketProfili)
        f.write("INSERT INTO sirket_profili (firma_unvani, adres, telefon, email, web_adresi, iban, bic, vergi_no, sirket_no, banka_adi) VALUES ('PFÄLZER BODENBAU&SANIERUNG GmbH', 'Mergenthaler Allee 15-21\\n65760 Eschborn', '0176-1234567', 'info@pfaelzer-bodenbau-sanierung.com', 'www.pfaelzer-bau-saniereung.com', 'LT03 3250 0744 3938 2376', 'REVOLT21', '44 665', 'HRB-Nr. 49351', 'OONTO.');\n")
        # Test Müşterileri (Musteri)
        f.write("INSERT INTO musteri (firma_adi, adres, vergi_no, telefon, email, ilgili_kisi, web_adresi, notlar, is_reverse_charge) VALUES ('Muster Bau GmbH', 'Hauptstrasse 123\\n10115 Berlin', 'DE123456789', '+49 30 1234567', 'info@musterbau.de', 'Hans Müller', 'www.musterbau.de', 'Önemli müşteri.', TRUE);\n")
        f.write("INSERT INTO musteri (firma_adi, adres, vergi_no, telefon, email, ilgili_kisi, web_adresi, notlar, is_reverse_charge) VALUES ('Innovate GmbH', 'Schulweg 45\\n20095 Hamburg', 'DE987654321', '+49 40 9876543', 'kontakt@innovate.de', 'Lena Schmidt', 'www.innovate-hamburg.de', 'Hızlı ödeme yaparlar.', FALSE);\n")
        f.write("INSERT INTO musteri (firma_adi, adres, vergi_no, telefon, email, ilgili_kisi, web_adresi, notlar, is_reverse_charge) VALUES ('Global Solutions AG', 'Am Stadtwald 1\\n60329 Frankfurt', 'DE112233445', '+49 69 1122334', 'support@globalsolutions.com', 'Max Mustermann', 'www.globalsolutions.com', 'Büyük projeler için.', TRUE);\n")
        # Test Ürünleri (Urun)
        f.write("INSERT INTO urun (aciklama, birim, birim_fiyat, is_goturu) VALUES ('Beton C25/30 - Temel Uygulama (DE: Beton C25/30 - Fundamentanwendung, EN: Concrete C25/30 - Foundation Application)', 'm³', 120.00, FALSE);\n")
        f.write("INSERT INTO urun (aciklama, birim, birim_fiyat, is_goturu) VALUES ('Şap Atımı - İç Mekan (DE: Estrichverlegung - Innenbereich, EN: Screed Application - Interior)', 'm²', 25.00, FALSE);\n")
        f.write("INSERT INTO urun (aciklama, birim, birim_fiyat, is_goturu) VALUES ('Sıhhi Tesisat Altyapı Hazırlığı (Götürü) (DE: Sanitärinfrastruktur Vorbereitung (Pauschal), EN: Plumbing Infrastructure Preparation (Lump Sum))', 'Pauschal', 750.00, TRUE);\n")
        f.write("COMMIT;\n")

print(f"SQL komutları '{output_filename}' dosyasına başarıyla yazıldı.")