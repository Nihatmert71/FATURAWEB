-- SQL DDL for Table Creation --
BEGIN;

-- Adım 1: Mevcut Tabloları Silin (Eğer varsa)
DROP TABLE IF EXISTS fatura_kalemi;
DROP TABLE IF EXISTS fatura;
DROP TABLE IF EXISTS urun;
DROP TABLE IF EXISTS musteri;
DROP TABLE IF EXISTS sirket_profili;

-- Tablo Oluşturma Komutları (id sütunları SERIAL olarak güncellendi)
CREATE TABLE musteri (
    id SERIAL PRIMARY KEY,
    firma_adi VARCHAR(150) NOT NULL,
    adres VARCHAR(300) NOT NULL,
    vergi_no VARCHAR(50),
    telefon VARCHAR(50),
    email VARCHAR(120),
    ilgili_kisi VARCHAR(100),
    web_adresi VARCHAR(120),
    notlar TEXT,
    is_reverse_charge BOOLEAN
);

CREATE TABLE sirket_profili (
    id SERIAL PRIMARY KEY,
    firma_unvani VARCHAR(200),
    adres VARCHAR(300),
    telefon VARCHAR(50),
    email VARCHAR(120),
    web_adresi VARCHAR(120),
    iban VARCHAR(50),
    bic VARCHAR(50),
    vergi_no VARCHAR(50),
    sirket_no VARCHAR(50),
    banka_adi VARCHAR(100)
);

CREATE TABLE urun (
    id SERIAL PRIMARY KEY,
    aciklama VARCHAR(500) NOT NULL,
    birim VARCHAR(50) NOT NULL,
    birim_fiyat FLOAT NOT NULL,
    is_goturu BOOLEAN
);

CREATE TABLE fatura (
    id SERIAL PRIMARY KEY,
    fatura_no VARCHAR(50) NOT NULL UNIQUE,
    tarih TIMESTAMP,
    ausfuhrungsdatum TIMESTAMP,
    santiye VARCHAR(200),
    sachbearbeiter VARCHAR(100),
    musteri_id INTEGER NOT NULL,
    ara_toplam FLOAT NOT NULL,
    kdv_tutari FLOAT NOT NULL,
    genel_toplam FLOAT NOT NULL,
    odeme_durumu VARCHAR(50) NOT NULL,
    is_reverse_charge_invoice BOOLEAN,
    FOREIGN KEY(musteri_id) REFERENCES musteri (id)
);

CREATE TABLE fatura_kalemi (
    id SERIAL PRIMARY KEY,
    aciklama VARCHAR(500) NOT NULL,
    miktar FLOAT NOT NULL,
    birim VARCHAR(50) NOT NULL,
    birim_fiyat FLOAT NOT NULL,
    satir_toplami FLOAT NOT NULL,
    fatura_id INTEGER NOT NULL,
    is_goturu BOOLEAN,
    FOREIGN KEY(fatura_id) REFERENCES fatura (id)
);
COMMIT;

-- SQL DML for Initial Data Insertion --
BEGIN;
INSERT INTO sirket_profili (firma_unvani, adres, telefon, email, web_adresi, iban, bic, vergi_no, sirket_no, banka_adi) VALUES ('PFÄLZER BODENBAU&SANIERUNG GmbH', 'Mergenthaler Allee 15-21\n65760 Eschborn', '0176-1234567', 'info@pfaelzer-bodenbau-sanierung.com', 'www.pfaelzer-bau-saniereung.com', 'LT03 3250 0744 3938 2376', 'REVOLT21', '44 665', 'HRB-Nr. 49351', 'OONTO.');
INSERT INTO musteri (firma_adi, adres, vergi_no, telefon, email, ilgili_kisi, web_adresi, notlar, is_reverse_charge) VALUES ('Muster Bau GmbH', 'Hauptstrasse 123\n10115 Berlin', 'DE123456789', '+49 30 1234567', 'info@musterbau.de', 'Hans Müller', 'www.musterbau.de', 'Önemli müşteri.', TRUE);
INSERT INTO musteri (firma_adi, adres, vergi_no, telefon, email, ilgili_kisi, web_adresi, notlar, is_reverse_charge) VALUES ('Innovate GmbH', 'Schulweg 45\n20095 Hamburg', 'DE987654321', '+49 40 9876543', 'kontakt@innovate.de', 'Lena Schmidt', 'www.innovate-hamburg.de', 'Hızlı ödeme yaparlar.', FALSE);
INSERT INTO musteri (firma_adi, adres, vergi_no, telefon, email, ilgili_kisi, web_adresi, notlar, is_reverse_charge) VALUES ('Global Solutions AG', 'Am Stadtwald 1\n60329 Frankfurt', 'DE112233445', '+49 69 1122334', 'support@globalsolutions.com', 'Max Mustermann', 'www.globalsolutions.com', 'Büyük projeler için.', TRUE);
INSERT INTO urun (aciklama, birim, birim_fiyat, is_goturu) VALUES ('Beton C25/30 - Temel Uygulama (DE: Beton C25/30 - Fundamentanwendung, EN: Concrete C25/30 - Foundation Application)', 'm³', 120.00, FALSE);
INSERT INTO urun (aciklama, birim, birim_fiyat, is_goturu) VALUES ('Şap Atımı - İç Mekan (DE: Estrichverlegung - Innenbereich, EN: Screed Application - Interior)', 'm²', 25.00, FALSE);
INSERT INTO urun (aciklama, birim, birim_fiyat, is_goturu) VALUES ('Sıhhi Tesisat Altyapı Hazırlığı (Götürü) (DE: Sanitärinfrastruktur Vorbereitung (Pauschal), EN: Plumbing Infrastructure Preparation (Lump Sum))', 'Pauschal', 750.00, TRUE);
COMMIT;