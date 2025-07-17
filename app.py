# DOSYA ADI: app.py (Tüm Hatalar Giderildi - Nihai Sürüm - Login Eklendi)
# app.run() için hata ayıklama parametreleri eklendi.

import os
from flask import Flask, render_template, request, redirect, url_for, flash, g, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from flask_babel import Babel, _, lazy_gettext as _l # _ ve _l burada tanımlı
import re
import json
import traceback
from flask import has_request_context, current_app

# Flask-Login için gerekli importlar
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Basit PDF oluşturma yardımcımızı içeri aktarıyoruz
try:
    from fatura_yardimcisi import resimden_pdf_olustur
except ImportError:
    def resimden_pdf_olustur(*args, **kwargs):
        print("UYARI: 'fatura_yardimcisi.py' dosyası bulunamadı veya içe aktarılamadı. PDF oluşturma devre dışı.")
        return False

# --- UYGULAMA VE VERİTABANI KURULUMU ---
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cok-gizli-bir-anahtar-bunu-mutlaka-degistir') 
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['LANGUAGES'] = ['de', 'tr', 'en']
app.config['BABEL_DEFAULT_LOCALE'] = 'de' # Varsayılan dil Almanca
app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(basedir, 'translations')
db = SQLAlchemy(app)

# --- FLASK-LOGIN KURULUMU ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Kullanıcı girişi gerektiren bir sayfaya erişildiğinde yönlendirilecek sayfa
login_manager.login_message_category = 'info'
login_manager.login_message = _l('Bu sayfaya erişmek için giriş yapmalısınız.') # Giriş yapılması gerektiğini belirten mesaj

# --- BABEL KURULUMU ---
def get_locale():
    if not has_request_context():
        return app.config['BABEL_DEFAULT_LOCALE']

    if 'lang' in request.args and request.args['lang'] in current_app.config['LANGUAGES']:
        session['lang'] = request.args['lang']

    if 'lang' in session:
        return session.get('lang')

    return request.accept_languages.best_match(current_app.config['LANGUAGES']) or current_app.config['BABEL_DEFAULT_LOCALE']

babel = Babel(app, locale_selector=get_locale)
# Babel CLI komutları için init_app'e veya manuel add_command'e gerek yok,
# Flask-Babel 2.x ve üzeri genellikle otomatik olarak kaydeder.

@app.before_request
def before_request_locale():
    g.locale = get_locale()

# --- VERİTABANI MODELLERİ ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class SirketProfili(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    firma_adi = db.Column(db.String(150), nullable=False)
    adres = db.Column(db.String(300), nullable=False)
    vergi_no = db.Column(db.String(50), nullable=True)
    telefon = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    ilgili_kisi = db.Column(db.String(100), nullable=True)
    web_adresi = db.Column(db.String(120), nullable=True)
    notlar = db.Column(db.Text, nullable=True)
    faturalar = db.relationship('Fatura', backref='musteri', lazy=True, cascade="all, delete-orphan")
    is_reverse_charge = db.Column(db.Boolean, default=False)

class Urun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aciklama = db.Column(db.String(500), nullable=False) 
    birim = db.Column(db.String(50), nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    is_goturu = db.Column(db.Boolean, default=False)

class Fatura(db.Model):
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
    kalemler = db.relationship('FaturaKalemi', backref='fatura', lazy=True, cascade="all, delete-orphan")
    is_reverse_charge_invoice = db.Column(db.Boolean, default=False)

class FaturaKalemi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aciklama = db.Column(db.String(500), nullable=False) 
    miktar = db.Column(db.Float, nullable=False)
    birim = db.Column(db.String(50), nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    satir_toplami = db.Column(db.Float, nullable=False)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=False)
    is_goturu = db.Column(db.Boolean, default=False)

@app.context_processor
def inject_global_data_for_all_templates():
    sirket_profili = SirketProfili.query.first() 
    if not sirket_profili:
        sirket_profili = {
            'firma_unvani': _('Yükleniyor...'),
            'adres': '', 'telefon': '', 'email': '', 'web_adresi': '',
            'iban': '', 'bic': '', 'vergi_no': '', 'sirket_no': '', 'banka_adi': ''
        }
    return dict(app=app, profil=sirket_profili, current_user=current_user)

# --- VERİTABANI BAŞLATMA VE TEST VERİSİ EKLEME KOMUTU ---
@app.cli.command('init-db')
def init_db_command():
    """Veritabanı tablolarını oluşturur ve varsayılan verileri ekler."""
    with app.app_context(): 
        db.create_all() 

        if SirketProfili.query.first() is None:
            db.session.add(SirketProfili())
            db.session.commit()
            print(_("Varsayılan şirket profili oluşturuldu."))

        if User.query.filter_by(username='admin').first() is None:
            admin_user = User(username='admin')
            admin_user.set_password('admin123') 
            db.session.add(admin_user)
            db.session.commit()
            print(_("Varsayılan yönetici kullanıcı 'admin' (şifre: admin123) oluşturuldu. Lütfen şifreyi değiştirin!"))
        else:
            print(_("Yönetici kullanıcı zaten mevcut."))

        if Musteri.query.count() == 0:
            print(_("Test müşterileri ekleniyor (3 adet)..."))
            test_musteriler_data = [
                { "firma_adi": "Muster Bau GmbH", "adres": "Hauptstrasse 123\n10115 Berlin", "vergi_no": "DE123456789", "telefon": "+49 30 1234567", "email": "info@musterbau.de", "ilgili_kisi": "Hans Müller", "web_adresi": "www.musterbau.de", "notlar": "Önemli müşteri.", "is_reverse_charge": True },
                { "firma_adi": "Innovate GmbH", "adres": "Schulweg 45\n20095 Hamburg", "vergi_no": "DE987654321", "telefon": "+49 40 9876543", "email": "kontakt@innovate.de", "ilgili_kisi": "Lena Schmidt", "web_adresi": "www.innovate-hamburg.de", "notlar": "Hızlı ödeme yaparlar.", "is_reverse_charge": False },
                { "firma_adi": "Global Solutions AG", "adres": "Am Stadtwald 1\n60329 Frankfurt", "vergi_no": "DE112233445", "telefon": "+49 69 1122334", "email": "support@globalsolutions.com", "ilgili_kisi": "Max Mustermann", "web_adresi": "www.globalsolutions.com", "notlar": "Büyük projeler için.", "is_reverse_charge": True }
            ]
            for data in test_musteriler_data:
                existing_customer = Musteri.query.filter_by(firma_adi=data['firma_adi']).first()
                if not existing_customer:
                    new_customer = Musteri(**data)
                    db.session.add(new_customer)
                    print(_(f"Müşteri eklendi: {data['firma_adi']}"))
                else:
                    for key, value in data.items():
                        setattr(existing_customer, key, value)
                    print(_(f"Müşteri güncellendi: {data['firma_adi']}"))
            db.session.commit()
            print(_("Test müşterileri eklendi/güncellendi."))
        else:
            print(_("Müşteriler zaten mevcut, test verileri atlandı."))

        if Urun.query.count() == 0:
            print(_("Test ürünleri ekleniyor (3 adet)..."))
            test_urunler_data = [
                {"aciklama": "Beton C25/30 - Temel Uygulama (DE: Beton C25/30 - Fundamentanwendung, EN: Concrete C25/30 - Foundation Application)", "birim": "m³", "birim_fiyat": 120.00, "is_goturu": False},
                {"aciklama": "Şap Atımı - İç Mekan (DE: Estrichverlegung - Innenbereich, EN: Screed Application - Interior)", "birim": "m²", "birim_fiyat": 25.00, "is_goturu": False},
                {"aciklama": "Sıhhi Tesisat Altyapı Hazırlığı (Götürü) (DE: Sanitärinfrastruktur Vorbereitung (Pauschal), EN: Plumbing Infrastructure Preparation (Lump Sum))", "birim": "Pauschal", "birim_fiyat": 750.00, "is_goturu": True}
            ]
            for data in test_urunler_data:
                existing_urun = Urun.query.filter_by(aciklama=data['aciklama']).first()
                if not existing_urun:
                    new_urun = Urun(**data)
                    db.session.add(new_urun)
                    print(_(f"Ürün eklendi: {data['aciklama']}"))
                else:
                    for key, value in data.items():
                        setattr(existing_urun, key, value)
                    print(_(f"Ürün güncellendi: {data['aciklama']}"))
            db.session.commit()
            print(_("Test ürünleri eklendi/güncellendi."))
        else:
            print(_("Ürünler zaten mevcut, test verileri atlandı."))
        print(_('Veritabanı başlatıldı.'))

# --- ANA ROUTE'LAR (Login Eklendi) ---

# Ana URL'ye erişim: Eğer oturum açık değilse login'e yönlendir, açıksa dashboard'a
@app.route('/')
def root_redirect():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required # Doğrudan /dashboard'a erişim için hala giriş gerekiyor
def dashboard():
    toplam_musteri_sayisi = db.session.query(Musteri).count()
    toplam_urun_sayisi = db.session.query(Urun).count()
    toplam_fatura_sayisi = db.session.query(Fatura).count()
    toplam_fatura_tutari_obj = db.session.query(db.func.sum(Fatura.genel_toplam)).scalar()
    toplam_fatura_tutari = toplam_fatura_tutari_obj if toplam_fatura_tutari_obj is not None else 0.0

    musteriler = Musteri.query.order_by(Musteri.firma_adi).limit(5).all()
    faturalar = Fatura.query.order_by(Fatura.tarih.desc()).limit(5).all()

    return render_template('index.html', musteriler=musteriler, faturalar=faturalar,
                            toplam_musteri_sayisi=toplam_musteri_sayisi, toplam_urun_sayisi=toplam_urun_sayisi,
                            toplam_fatura_sayisi=toplam_fatura_sayisi, toplam_fatura_tutari=toplam_fatura_tutari)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(_('Başarıyla giriş yapıldı.'), 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash(_('Geçersiz kullanıcı adı veya şifre.'), 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and current_user.username != 'admin':
        flash(_('Zaten giriş yapmışsınız veya kayıt olmaya yetkiniz yok.'), 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if not username or not password or not password_confirm:
            flash(_('Tüm alanları doldurmanız gerekmektedir.'), 'danger')
            return render_template('register.html')

        if password != password_confirm:
            flash(_('Şifreler eşleşmiyor.'), 'danger')
            return render_template('register.html', username=username)

        if User.query.filter_by(username=username).first():
            flash(_('Bu kullanıcı adı zaten mevcut.'), 'danger')
            return render_template('register.html', username=username)

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(_('Kullanıcı başarıyla kaydedildi! Şimdi giriş yapabilirsiniz.'), 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('Başarıyla çıkış yapıldı.'), 'info')
    return redirect(url_for('login'))

# --- PROGRAM ROUTE'LARI (Login required dekoratörleri eklendi) ---
@app.route('/fatura_olustur', methods=['GET', 'POST'])
@login_required
def fatura_olustur():
    musteriler = Musteri.query.order_by(Musteri.firma_adi).all()
    urunler = Urun.query.order_by(Urun.aciklama).all()

    if request.method == 'POST':
        musteri_id = request.form['musteri_id']
        fatura_no = request.form['fatura_no']
        santiye = request.form.get('santiye')
        sachbearbeiter = request.form.get('sachbearbeiter')
        tarih_str = request.form['tarih']
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d')
        odeme_durumu = request.form.get('odeme_durumu', 'Bekliyor')
        ausfuhrungsdatum_str = request.form.get('ausfuhrungsdatum')
        ausfuhrungsdatum = datetime.strptime(ausfuhrungsdatum_str, '%Y-%m-%d') if ausfuhrungsdatum_str else None

        ara_toplam = float(request.form.get('ara_toplam', '0.0'))
        kdv_tutari = float(request.form.get('kdv_tutari', '0.0'))
        genel_toplam = float(request.form.get('genel_toplam', '0.0'))

        musteri = Musteri.query.get(musteri_id)
        is_reverse_charge_invoice = musteri.is_reverse_charge if musteri else False

        kalem_aciklamalari = request.form.getlist('kalem_aciklama[]')

        if not kalem_aciklamalari:
            flash(_('Faturaya en az bir kalem eklemelisiniz.'), 'danger')

            fatura_kalemleri_json = []
            if 'kalem_aciklama[]' in request.form:
                kalem_miktarlari = request.form.getlist('kalem_miktar[]')
                kalem_birimleri = request.form.getlist('kalem_birim[]')
                kalem_birim_fiyatlari = request.form.getlist('kalem_birim_fiyat[]')
                kalem_is_goturu = request.form.getlist('kalem_is_goturu[]')
                kalem_satir_toplamlari = request.form.getlist('kalem_satir_toplamlari[]')

                for i in range(len(kalem_aciklamalari)):
                    try:
                        fatura_kalemleri_json.append({
                            'aciklama': kalem_aciklamalari[i],
                            'miktar': float(kalem_miktarlari[i] if kalem_miktarlari[i] else '0.0'),
                            'birim': kalem_birimleri[i],
                            'birim_fiyat': float(kalem_birim_fiyatlari[i] if kalem_birim_fiyatlari[i] else '0.0'),
                            'satir_toplami': float(kalem_satir_toplamlari[i] if kalem_satir_toplamlari[i] else '0.0'),
                            'is_goturu': kalem_is_goturu[i].lower() == 'true'
                        })
                    except ValueError:
                        pass 

            return render_template('fatura_olustur.html', musteri_listesi=musteriler, urunler=urunler,
                                    today=tarih.isoformat(),
                                    fatura_no=fatura_no, santiye=santiye, sachbearbeiter=sachbearbeiter,
                                    selected_musteri_id=int(musteri_id),
                                    odeme_durumu=odeme_durumu,
                                    ausfuhrungsdatum=ausfuhrungsdatum.isoformat() if ausfuhrungsdatum else '',
                                    fatura_kalemleri_json=json.dumps(fatura_kalemleri_json)
                                    )

        try:
            yeni_fatura = Fatura(fatura_no=fatura_no, tarih=tarih, santiye=santiye, sachbearbeiter=sachbearbeiter,
                                 musteri_id=musteri_id, ara_toplam=ara_toplam, kdv_tutari=kdv_tutari,
                                 genel_toplam=genel_toplam, odeme_durumu=odeme_durumu,
                                 ausfuhrungsdatum=ausfuhrungsdatum,
                                 is_reverse_charge_invoice=is_reverse_charge_invoice)
            db.session.add(yeni_fatura)
            db.session.flush() 

            kalem_miktarlari = request.form.getlist('kalem_miktar[]')
            kalem_birimleri = request.form.getlist('kalem_birim[]')
            kalem_birim_fiyatlari = request.form.getlist('kalem_birim_fiyat[]')
            kalem_is_goturu = request.form.getlist('kalem_is_goturu[]')
            kalem_satir_toplamlari = request.form.getlist('kalem_satir_toplamlari[]')

            if not (len(kalem_aciklamalari) == len(kalem_miktarlari) == len(kalem_birimleri) == len(kalem_birim_fiyatlari) == len(kalem_is_goturu) == len(kalem_satir_toplamlari)):
                flash(_('Fatura kalem verilerinde tutarsızlık var.'), 'danger')
                db.session.rollback()
                return redirect(url_for('fatura_olustur'))

            for i in range(len(kalem_aciklamalari)):
                try:
                    kalem_miktar = float(kalem_miktarlari[i] if kalem_miktarlari[i] else '0.0')
                    kalem_birim_fiyat = float(kalem_birim_fiyatlari[i] if kalem_birim_fiyatlari[i] else '0.0')
                    is_goturu_bool = kalem_is_goturu[i].lower() == 'true'
                    satir_toplami = float(kalem_satir_toplamlari[i] if kalem_satir_toplamlari[i] else '0.0')
                except ValueError:
                    flash(_('Fatura kalemlerinde geçersiz sayısal değerler var.'), 'danger')
                    db.session.rollback()
                    return redirect(url_for('fatura_olustur'))

                yeni_kalem = FaturaKalemi(aciklama=kalem_aciklamalari[i],
                                          miktar=kalem_miktar,
                                          birim=kalem_birimleri[i],
                                          birim_fiyat=kalem_birim_fiyat,
                                          satir_toplami=satir_toplami,
                                          fatura_id=yeni_fatura.id,
                                          is_goturu=is_goturu_bool)
                db.session.add(yeni_kalem)

            db.session.commit()
            flash(_('Fatura başarıyla oluşturuldu!'), 'success')
            return redirect(url_for('fatura_detay', fatura_id=yeni_fatura.id))
        except Exception as e:
            db.session.rollback()
            flash(_(f'Fatura oluşturulurken bir hata oluştu: {e}'), 'danger')
            print(f"Fatura oluşturma hatası: {e}")
            traceback.print_exc()
            fatura_kalemleri_json = []
            try:
                kalem_miktarlari = request.form.getlist('kalem_miktar[]')
                kalem_birimleri = request.form.getlist('kalem_birim[]')
                kalem_birim_fiyatlari = request.form.getlist('kalem_birim_fiyat[]')
                kalem_is_goturu = request.form.getlist('kalem_is_goturu[]')
                kalem_satir_toplamlari = request.form.getlist('kalem_satir_toplamlari[]')
                for i in range(len(kalem_aciklamalari)):
                    fatura_kalemleri_json.append({
                        'aciklama': kalem_aciklamalari[i],
                        'miktar': float(kalem_miktarlari[i] if kalem_miktarlari[i] else '0.0'),
                        'birim': kalem_birimleri[i],
                        'birim_fiyat': float(kalem_birim_fiyatlari[i] if kalem_birim_fiyatlari[i] else '0.0'),
                        'satir_toplami': float(kalem_satir_toplamlari[i] if kalem_satir_toplamlari[i] else '0.0'),
                        'is_goturu': kalem_is_goturu[i].lower() == 'true'
                    })
            except Exception:
                pass 

            return render_template('fatura_olustur.html', musteri_listesi=musteriler, urunler=urunler,
                                   today=date.today().isoformat(),
                                   default_ausfuhrungsdatum=date.today().isoformat(),
                                   fatura_no=fatura_no, santiye=santiye, sachbearbeiter=sachbearbeiter,
                                   selected_musteri_id=int(musteri_id),
                                   odeme_durumu=odeme_durumu,
                                   ausfuhrungsdatum=ausfuhrungsdatum.isoformat() if ausfuhrungsdatum else '',
                                   fatura_kalemleri_json=json.dumps(fatura_kalemleri_json))

    return render_template('fatura_olustur.html', musteri_listesi=musteriler, urunler=urunler,
                            today=date.today().isoformat(),
                            default_ausfuhrungsdatum=date.today().isoformat(),
                            fatura_kalemleri_json="[]")

# API Endpoints (Müşteri reverse charge durumunu almak için)
@app.route('/api/musteri/<int:musteri_id>/reverse_charge', methods=['GET'])
@login_required
def get_musteri_reverse_charge(musteri_id):
    musteri = Musteri.query.get_or_404(musteri_id)
    return {'is_reverse_charge': musteri.is_reverse_charge}


# --- PDF OLUŞTURMA ROUTE'U (SON HALİ) ---
@app.route('/fatura_pdf/<int:fatura_id>')
@login_required
def fatura_pdf(fatura_id):
    fatura = Fatura.query.get_or_404(fatura_id)
    sirket_profili = SirketProfili.query.first()

    current_locale = g.locale

    processed_kalemler = []
    for kalem in fatura.kalemler:
        processed_kalemler.append({
            'aciklama': kalem.aciklama,
            'miktar': kalem.miktar,
            'birim': kalem.birim,
            'birim_fiyat': kalem.birim_fiyat,
            'satir_toplami': kalem.satir_toplami,
            'is_goturu': kalem.is_goturu
        })

    fatura_bilgileri = {
        "sirket_adi": sirket_profili.firma_unvani if sirket_profili else "PFÄLZER BODENBAU & SANIERUNG GmbH",
        "sirket_adres_satirlari": sirket_profili.adres.split('\n') if sirket_profili and sirket_profili.adres else ["Mergenthaler Allee 15-21", "65760 Eschborn"],
        "sirket_telefon": sirket_profili.telefon if sirket_profili else "0176-1234567",
        "sirket_email": sirket_profili.email if sirket_profili else "info@pfaelzer-bodenbau-sanierung.com",
        "sirket_web": sirket_profili.web_adresi if sirket_profili else "www.pfaelzer-bau-saniereung.com",
        "sirket_iban": sirket_profili.iban if sirket_profili else "LT03 3250 0744 3938 2376",
        "sirket_bic": sirket_profili.bic if sirket_profili else "REVOLT21",
        "sirket_vergi_no": sirket_profili.vergi_no if sirket_profili else "44 665",
        "sirket_sirket_no": sirket_profili.sirket_no if sirket_profili else "HRB-Nr. 49351",
        "sirket_banka_adi": sirket_profili.banka_adi if sirket_profili else "OONTO.",
        "musteri_adi": fatura.musteri.firma_adi,
        "musteri_adres_satirlari": fatura.musteri.adres.split('\n') if fatura.musteri.adres else [],
        "fatura_no": fatura.fatura_no,
        "tarih": fatura.tarih.strftime('%d.%m.%Y'),
        "santiye": fatura.santiye if fatura.santiye else '',
        "sachbearbeiter": fatura.sachbearbeiter if fatura.sachbearbeiter else '',
        "ausfuhrungsdatum": fatura.ausfuhrungsdatum.strftime('%d.%m.%Y') if fatura.ausfuhrungsdatum else '',
        "kalemler": processed_kalemler,
        "ara_toplam": fatura.ara_toplam if fatura.ara_toplam is not None else 0.0,
        "kdv_tutari": fatura.kdv_tutari if fatura.kdv_tutari is not None else 0.0,
        "genel_toplam": fatura.genel_toplam if fatura.genel_toplam is not None else 0.0,
        "is_reverse_charge_invoice": fatura.is_reverse_charge_invoice,
        "current_locale": current_locale
    }

    cikti_dizini = os.path.join(basedir, "olusturulan_faturalar")
    if not os.path.exists(cikti_dizini):
        os.makedirs(cikti_dizini)

    pdf_cikti_yolu = os.path.join(cikti_dizini, f"fatura_{fatura.fatura_no}.pdf")

    try:
        basarili = resimden_pdf_olustur(fatura_bilgileri, pdf_cikti_yolu)
    except Exception as e:
        flash(_('PDF oluşturulurken beklenmedik bir hata oluştu. Lütfen konsol çıktısını kontrol edin.'), 'danger')
        print(f"PDF oluşturma hatası: {e}")
        traceback.print_exc()
        return redirect(request.referrer or url_for('dashboard'))

    if basarili:
        return send_from_directory(directory=cikti_dizini, path=os.path.basename(pdf_cikti_yolu), as_attachment=False)
    else:
        flash(_('PDF oluşturulurken bir hata oluştu. Lütfen "fatura_yardimcisi.py" dosyasının projenizin ana dizininde olduğundan, "arial.ttf" font dosyasının mevcut olduğundan ve fatura bilgilerinin doğru olduğundan emin olun.'), 'danger')
        return redirect(request.referrer or url_for('dashboard'))


@app.route('/musteri_listesi')
@login_required
def musteri_listesi():
    musteriler = Musteri.query.order_by(Musteri.firma_adi).all()
    return render_template('musteri_listesi.html', musteri_listesi=musteriler)

@app.route('/musteri_detay/<int:musteri_id>')
@login_required
def musteri_detay(musteri_id):
    musteri = Musteri.query.get_or_404(musteri_id)
    faturalar = Fatura.query.filter_by(musteri_id=musteri.id).order_by(Fatura.tarih.desc()).all()
    return render_template('musteri_detay.html', musteri=musteri, faturalar=faturalar)

@app.route('/ayarlar', methods=['GET', 'POST'])
@login_required
def ayarlar():
    profil = SirketProfili.query.first()
    if not profil:
        profil = SirketProfili()
        db.session.add(profil)
        db.session.commit()

    if request.method == 'POST':
        profil.firma_unvani = request.form['firma_unvani']
        profil.adres = request.form['adres']
        profil.telefon = request.form['telefon']
        profil.email = request.form['email']
        profil.web_adresi = request.form['web_adresi']
        profil.iban = request.form['iban']
        profil.bic = request.form['bic']
        profil.vergi_no = request.form['vergi_no']
        profil.sirket_no = request.form['sirket_no']
        profil.banka_adi = request.form['banka_adi']
        db.session.commit()
        flash(_('Şirket profili başarıyla güncellendi!'), 'success')
        return redirect(url_for('ayarlar'))
    return render_template('ayarlar.html', profil=profil)

@app.route('/musteri_ekle', methods=['GET', 'POST'])
@login_required
def musteri_ekle():
    if request.method == 'POST':
        is_reverse_charge = 'is_reverse_charge' in request.form
        yeni_musteri = Musteri(firma_adi=request.form['firma_adi'],
                               adres=request.form['adres'].strip(),
                               vergi_no=request.form.get('vergi_no'),
                               telefon=request.form.get('telefon'),
                               email=request.form.get('email'),
                               ilgili_kisi=request.form.get('ilgili_kisi'),
                               web_adresi=request.form.get('web_adresi'),
                               notlar=request.form.get('notlar'),
                               is_reverse_charge=is_reverse_charge)
        db.session.add(yeni_musteri)
        db.session.commit()
        flash(_('Müşteri başarıyla eklendi!'), 'success')
        return redirect(url_for('musteri_listesi'))
    return render_template('musteri_ekle.html')

@app.route('/urunler')
@login_required
def urun_listesi():
    urunler = Urun.query.order_by(Urun.aciklama).all()
    return render_template('urunler.html', urunler=urunler)

@app.route('/urun_ekle', methods=['GET', 'POST'])
@login_required
def urun_ekle():
    if request.method == 'POST':
        yeni_urun = Urun(aciklama=request.form['aciklama'], birim=request.form['birim'], birim_fiyat=float(request.form['birim_fiyat']), is_goturu='is_goturu' in request.form)
        db.session.add(yeni_urun)
        db.session.commit()
        flash(_('Ürün başarıyla eklendi!'), 'success')
        return redirect(url_for('urun_listesi'))
    return render_template('urun_ekle.html')

@app.route('/fatura_sil/<int:fatura_id>', methods=['POST'])
@login_required
def fatura_sil(fatura_id):
    fatura = Fatura.query.get_or_404(fatura_id)
    db.session.delete(fatura)
    db.session.commit()
    flash(_('Fatura başarıyla silindi.'), 'success')
    return redirect(url_for('fatura_listesi'))

@app.route('/musteri_sil/<int:musteri_id>', methods=['POST'])
@login_required
def musteri_sil(musteri_id):
    musteri = Musteri.query.get_or_404(musteri_id)
    if musteri.faturalar:
        flash(_('Bu müşteriye ait faturalar olduğu için silinemez. Önce faturaları silin.'), 'danger')
    else:
        db.session.delete(musteri)
        db.session.commit()
        flash(_('Müşteri başarıyla silindi.'), 'success')
    return redirect(url_for('musteri_listesi'))

@app.route('/urun_sil/<int:urun_id>', methods=['POST'])
@login_required
def urun_sil(urun_id):
    urun = Urun.query.get_or_404(urun_id)
    db.session.delete(urun)
    db.session.commit()
    flash(_('Ürün başarıyla silindi.'), 'success')
    return redirect(url_for('urun_listesi'))

@app.route('/fatura_listesi')
@login_required
def fatura_listesi():
    faturalar = Fatura.query.order_by(Fatura.tarih.desc()).all()
    return render_template('fatura_listesi.html', faturalar=faturalar)

@app.route('/fatura_detay/<int:fatura_id>')
@login_required
def fatura_detay(fatura_id):
    fatura = Fatura.query.get_or_404(fatura_id)
    return render_template('fatura_detay.html', fatura=fatura)

@app.route('/fatura_duzenle/<int:fatura_id>', methods=['GET', 'POST'])
@login_required
def fatura_duzenle(fatura_id):
    fatura = Fatura.query.get_or_404(fatura_id)
    musteriler = Musteri.query.order_by(Musteri.firma_adi).all()
    urunler = Urun.query.order_by(Urun.aciklama).all()

    if request.method == 'POST':
        fatura.musteri_id = request.form['musteri_id']
        fatura.fatura_no = request.form['fatura_no']
        santiye = request.form.get('santiye')
        sachbearbeiter = request.form.get('sachbearbeiter')
        tarih = datetime.strptime(request.form['tarih'], '%Y-%m-%d')
        odeme_durumu = request.form.get('odeme_durumu', 'Bekliyor')
        ausfuhrungsdatum_str = request.form.get('ausfuhrungsdatum')
        ausfuhrungsdatum = datetime.strptime(ausfuhrungsdatum_str, '%Y-%m-%d') if ausfuhrungsdatum_str else None

        ara_toplam = float(request.form.get('ara_toplam', '0.0'))
        kdv_tutari = float(request.form.get('kdv_tutari', '0.0'))
        genel_toplam = float(request.form.get('genel_toplam', '0.0'))

        musteri = Musteri.query.get(fatura.musteri_id)
        is_reverse_charge_invoice = musteri.is_reverse_charge if musteri else False

        kalem_aciklamalari = request.form.getlist('kalem_aciklama[]')

        if not kalem_aciklamalari:
            flash(_('Faturaya en az bir kalem eklemelisiniz.'), 'danger')

            fatura_kalemleri_json = []
            if 'kalem_aciklama[]' in request.form:
                kalem_miktarlari = request.form.getlist('kalem_miktar[]')
                kalem_birimleri = request.form.getlist('kalem_birim[]')
                kalem_birim_fiyatlari = request.form.getlist('kalem_birim_fiyat[]')
                kalem_is_goturu = request.form.getlist('kalem_is_goturu[]')
                kalem_satir_toplamlari = request.form.getlist('kalem_satir_toplamlari[]')

                for i in range(len(kalem_aciklamalari)):
                    try:
                        fatura_kalemleri_json.append({
                            'aciklama': kalem_aciklamalari[i],
                            'miktar': float(kalem_miktarlari[i] if kalem_miktarlari[i] else '0.0'),
                            'birim': kalem_birimleri[i],
                            'birim_fiyat': float(kalem_birim_fiyatlari[i] if kalem_birim_fiyatlari[i] else '0.0'),
                            'satir_toplami': float(kalem_satir_toplamlari[i] if kalem_satir_toplamlari[i] else '0.0'),
                            'is_goturu': kalem_is_goturu[i].lower() == 'true'
                        })
                    except ValueError:
                        pass 

            return render_template('fatura_duzenle.html', fatura=fatura, musteri_listesi=musteriler, urunler=urunler,
                                    fatura_kalemleri_json=json.dumps(fatura_kalemleri_json)
                                    )

        FaturaKalemi.query.filter_by(fatura_id=fatura.id).delete()
        db.session.flush()

        kalem_miktarlari = request.form.getlist('kalem_miktar[]')
        kalem_birimleri = request.form.getlist('kalem_birim[]')
        kalem_birim_fiyatlari = request.form.getlist('kalem_birim_fiyat[]')
        kalem_is_goturu = request.form.getlist('kalem_is_goturu[]')
        kalem_satir_toplamlari = request.form.getlist('kalem_satir_toplamlari[]')

        if not (len(kalem_aciklamalari) == len(kalem_miktarlari) == len(kalem_birimleri) == len(kalem_birim_fiyatlari) == len(kalem_is_goturu) == len(kalem_satir_toplamlari)):
            flash(_('Fatura kalem verilerinde tutarsızlık var.'), 'danger')
            db.session.rollback()
            return redirect(url_for('fatura_duzenle', fatura_id=fatura.id))

        for i in range(len(kalem_aciklamalari)):
            try:
                kalem_miktar = float(kalem_miktarlari[i] if kalem_miktarlari[i] else '0.0')
                kalem_birim_fiyat = float(kalem_birim_fiyatlari[i] if kalem_birim_fiyatlari[i] else '0.0')
                is_goturu_bool = kalem_is_goturu[i].lower() == 'true'
                satir_toplami = float(kalem_satir_toplamlari[i] if kalem_satir_toplamlari[i] else '0.0')
            except ValueError:
                flash(_('Fatura kalemlerinde geçersiz sayısal değerler var.'), 'danger')
                db.session.rollback()
                return redirect(url_for('fatura_duzenle', fatura_id=fatura.id))

            yeni_kalem = FaturaKalemi(aciklama=kalem_aciklamalari[i],
                                      miktar=kalem_miktar,
                                      birim=kalem_birimleri[i],
                                      birim_fiyat=kalem_birim_fiyat,
                                      satir_toplami=satir_toplami,
                                      fatura_id=fatura.id,
                                      is_goturu=is_goturu_bool)
            db.session.add(yeni_kalem)

        db.session.commit()
        flash(_('Fatura başarıyla güncellendi!'), 'success')
        return redirect(url_for('fatura_detay', fatura_id=fatura.id))

    fatura_kalemleri_data = []
    for kalem in fatura.kalemler:
        fatura_kalemleri_data.append({
            'aciklama': kalem.aciklama,
            'miktar': kalem.miktar,
            'birim': kalem.birim,
            'birim_fiyat': kalem.birim_fiyat,
            'satir_toplami': kalem.satir_toplami,
            'is_goturu': kalem.is_goturu
        })

    return render_template('fatura_duzenle.html', fatura=fatura, musteri_listesi=musteriler, urunler=urunler,
                            fatura_kalemleri_json=json.dumps(fatura_kalemleri_data))


@app.route('/musteri_duzenle/<int:musteri_id>', methods=['GET', 'POST'])
@login_required
def musteri_duzenle(musteri_id):
    musteri = Musteri.query.get_or_404(musteri_id)
    if request.method == 'POST':
        musteri.firma_adi = request.form['firma_adi']
        musteri.adres = request.form['adres'].strip()
        musteri.vergi_no = request.form.get('vergi_no')
        musteri.telefon = request.form.get('telefon')
        musteri.email = request.form.get('email')
        musteri.ilgili_kisi = request.form.get('ilgili_kisi')
        musteri.web_adresi = request.form.get('web_adresi')
        musteri.notlar = request.form.get('notlar')
        musteri.is_reverse_charge = 'is_reverse_charge' in request.form
        db.session.commit()
        flash(_('Müşteri bilgileri başarıyla güncellendi!'), 'success')
        return redirect(url_for('musteri_detay', musteri_id=musteri.id))
    return render_template('musteri_duzenle.html', musteri=musteri)

@app.route('/urun_duzenle/<int:urun_id>', methods=['GET', 'POST'])
@login_required
def urun_duzenle(urun_id):
    urun = Urun.query.get_or_404(urun_id)
    if request.method == 'POST':
        urun.aciklama = request.form['aciklama']
        urun.birim = request.form['birim']
        urun.birim_fiyat = float(request.form['birim_fiyat'])
        urun.is_goturu = 'is_goturu' in request.form
        db.session.commit()
        flash(_('Ürün başarıyla güncellendi!'), 'success')
        return redirect(url_for('urun_listesi'))
    return render_template('urun_duzenle.html', urun=urun)

@app.route('/kullanim_kilavuzu')
@login_required
def kullanim_kilavuzu():
    """Kullanım kılavuzu sayfasını, seçili dile göre render eder."""

    lang = g.locale

# BUNU YAPIŞTIRIN
if lang == 'en':
    template_name = "kullanim_kilavuzu_ing.html" # Bu zaten çalışıyordu
elif lang == 'de':
    template_name = "kullanim_kilavuzu_de.html" # Hata buradaydı: 'deu' -> 'de' olarak düzeltildi
else: # Varsayılan Türkçe
    template_name = "kullanim_kilavuzu_tr.html" # Hata buradaydı: 'tur' -> 'tr' olarak düzeltildi

    print(f"Aranan kılavuz dosyası: {template_name}")

    try:
        return render_template(template_name)
    except Exception as e:
        print(f"HATA: {template_name} bulunamadı veya render edilemedi. Hata: {e}")
        flash(_('Kullanım kılavuzu yüklenirken bir sorun oluştu.'), 'danger')
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)