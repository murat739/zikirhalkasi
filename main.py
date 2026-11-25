from datetime import datetime
import json
import sqlite3
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import pandas as pd
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="ZİKİR HALKASI",
    page_icon="📿",
    layout="centered",
)

# YÖNETİCİ VE MİSAFİR YAZAR ŞİFRELERİ (Streamlit Secrets'tan okunur, yoksa varsayılan kullanılır)
try:
    YONETICI_SIFRESI = st.secrets["YONETICI_SIFRESI"]
except Exception:
    YONETICI_SIFRESI = "lebis9791."

try:
    MISAFIR_YAZAR_SIFRESI = st.secrets["MISAFIR_YAZAR_SIFRESI"]
except Exception:
    MISAFIR_YAZAR_SIFRESI = "lebis9791."

# --- SORUMLULUK REDDİ VE BİLGİLENDİRME METNİ ---
SORUMLULUK_REDDI_BASLIK = "⚠️ Çeviri, Yapay Zekâ ve Sorumluluk Reddi Bilgilendirmesi"
SORUMLULUK_REDDI_METNI = (
    "Yazılımda yer alan ayet, hadis ve âlim görüşlerine ilişkin çeviriler (otomatik veya yapay zekâ destekli çeviriler dahil) "
    "kolaylık ve genel bilgilendirme amacıyla sunulmaktadır. Kavram incelikleri, bağlam ve yorum farkları nedeniyle çevirilerde "
    "anlam kayması oluşabilir; bu çeviriler tek başına kesin veya bağlayıcı kaynak yerine geçmez ve asıl metinlerin, muteber "
    "meallerin ile ilgili kaynak eserlerin esas alınması gerekir. Yazılımdaki metin ve kaynak atıfları yapay zekâ desteğiyle "
    "oluşturulmuş olabilir; yalnızca bilgilendirme amaçlıdır ve resmî, teknik, idari, mali veya hukuki görüş/onay yerine geçmez. "
    "Yapay zekâ sistemleri eksik, güncel olmayan veya hatalı bilgi ve kaynak üretebileceğinden, tüm içerik ve atıfların "
    "kullanılmadan önce birincil kaynaklardan teyit edilmesi kullanıcının sorumluluğundadır. Yazılım \"olduğu gibi\" (AS-IS) sunulur; "
    "doğrulanmamış içeriklerin kullanımından doğabilecek zararlardan geliştirici ve dağıtıcı sorumlu tutulamaz."
)

# --- ARAYÜZ METİNLERİ ---
METINLER = {
    "top_marquee": (
        '📖 "BENİ ANIN Kİ, BEN DE SİZİ ANAYIM; BANA ŞÜKREDİN, SAKIN NANKÖRLÜK ETMEYİN." '
        "<strong>[BAKARA SURESİ, 2/152]</strong>"
        " &nbsp;&nbsp;&nbsp;✦&nbsp;&nbsp;&nbsp; "
        "BİRLİKTE GÜÇLENEREK BÜYÜYELİM VE KAİNATA ZİKRİMİZ DAĞILSIN."
    ),
    "participant_header": "🌍 Katılımcı Bilgileri",
    "name_label": "Adınız / Rumuzunuz:",
    "default_name": "Misafir",
    "guest_writer_mode": "✍️ Misafir Yazar Modu (Paylaş ve Güncelle)",
    "guest_writer_hint": "Yüksek metin kapasiteli paylaşım, güncelleme ve tarihçe alanını açmak için bu seçeneği işaretleyin.",
    "admin_header": "🔐 Yönetici / Kurucu Paneli",
    "admin_pass_label": "Yönetici Şifresi:",
    "login_btn": "Giriş Yap",
    "wrong_pass": "Hatalı yönetici şifresi!",
    "admin_active": "Yönetici yetkisi aktif.",
    "select_dhikr_admin": "Ortak Çekilecek Zikri Belirle:",
    "admin_dhikr_catalog_title": "📚 Zikir Çeşitleri ve Anlamları (Sadece Yönetici)",
    "short_dhikr_group": "🔹 Kısa Zikirler",
    "long_dhikr_group": "🔸 Uzun Zikirler",
    "target_label": "Ortak Hedef Sayısı:",
    "admin_pool_metric": "Ortak Havuz Toplamı (Yönetici)",
    "reset_pool_btn": "🗑️ Ortak Havuzu Sıfırla",
    "pool_reset_msg": "Havuz sıfırlandı!",
    "logout_btn": "🚪 Yönetici Çıkışı",
    "daily_report_title": "📊 Günlük Zikir Raporu (Sadece Yönetici)",
    "daily_total_label": "Bugün Çekilen Toplam Zikir",
    "col_dhikr": "Zikir",
    "col_count": "Adet",
    "no_daily_records": "Bugün henüz zikir çekilmemiş.",
    "sleep_note": (
        "💡 *Not:* Bu web uygulaması ücretsiz sunucularda barındırılmaktadır. "
        "Uzun süre işlem yapılmadığında uygulama uyku moduna geçebilir "
        "(ekranda 'Zzzz' simgesi çıkabilir).\n\n"
        "💤 Eğer böyle bir ekranla karşılaşırsanız, ekranda beliren mavi renkli "
        "*'Yes, get this app back up!'* butonuna tıklayın ve uygulamanın "
        "yeniden uyanması için 15-30 saniye bekleyin."
    ),
    "main_title": "ZİKİR HALKASI",
    "main_subtitle": (
        "Gönüllerin ortak niyet ve zikirle bir araya geldiği manevi dijital halka."
    ),
    "active_dhikr_heading": "### 📌 ÇEKİLECEK ORTAK ZİKİR:",
    "active_dhikr_meaning_label": "Anlamı:",
    "target_count_label": "Belirlenen Hedef",
    "shared_pool_reached_label": "Ortak Havuzda Ulaşılan",
    "your_contribution": "Sizin Katkınız (Kişisel)",
    "your_goal_impact_label": "Hedefe Etkisi (Toplam Katkı)",
    "goal_progress_caption": "Ortak Hedef İlerlemesi: %{pct} ({current:,} / {target:,})",
    "unit_count": "Adet",
    "goal_reached_msg": "🎉 ELHAMDÜLİLLAH! BELİRLENEN {hedef:,} ADETLİK ORTAK HEDEF TAMAMLANDI!",
    "pull_btn": "📿 BİR ZİKİR ÇEK (Tıkla)",
    "reset_personal_btn": "🔄 Kişisel Sayacı Sıfırla",
    "personal_reset_toast": "Kişisel sayacınız sıfırlandı. Ortak havuzdaki toplam ve hedefe katkınız korundu!",
    "goal_marquee": (
        '📜 KUR\'AN-I KERİM (AYET): "BENİ ANIN Kİ, BEN DE SİZİ ANAYIM." '
        "(BAKARA SURESİ, 152) &nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp; 📜 "
        'HADİS-İ ŞERİF: "ALLAH\'I ANAN İLE ANMAYAN KİMSENİN MİSALİ, DİRİ İLE '
        'ÖLÜ GİBİDİR." (BUHARİ) &nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp; ✨ '
        'HZ. MEVLANA (K.S.): "ZİKİR, KALBİN CİLASI VE PASININ '
        'SÖKÜCÜSÜDÜR; RUHUN GIDASIDIR." '
        "&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp; 💡 MANEVİ ŞİAR: "
        '"BİRLİKTEN GÜÇ DOĞAR; KALPLER ORTAK NİYET VE ZİKİRLE BİRLEŞİR."'
    ),
    "writer_section_heading": "✍️ MİSAFİR YAZAR KÖŞESİ (GÜZEL SÖZ & BİLGİ PAYLAŞIMI)",
    "writer_section_desc": "Sadece Misafir Yazar tarafından oluşturulan, güncellenebilen ve tarihçesi saklanan yüksek metin kapasiteli paylaşım alanı:",
    "writer_pass_label": "Misafir Yazar Şifresi:",
    "writer_login_btn": "🔓 Yazar Girişi",
    "writer_logout_btn": "🔒 Yazar Çıkışı",
    "writer_wrong_pass": "Hatalı Misafir Yazar şifresi!",
    "writer_auth_active": "Misafir Yazar yetkisi aktif. Paylaşım yapabilir, güncelleyebilir ve tarihçeyi yönetebilirsiniz.",
    "writer_title_label": "Başlık / Konu:",
    "writer_default_title": "Günün Güzel Sözü ve Manevi Not",
    "writer_body_label": "Güzel Söz / Bilgi / Uzun Metin (En fazla 10.000 karakter):",
    "writer_body_placeholder": "Buraya dilediğiniz uzunlukta güzel söz, hikmetli not veya bilgi yazabilir ve istediğiniz zaman güncelleyebilirsiniz...",
    "writer_save_btn": "💾 Paylaşımı Kaydet / Güncelle",
    "writer_clear_btn": "🧹 Aktif Paylaşımı Temizle",
    "writer_saved_msg": "Paylaşım kaydedildi, güncellendi ve tarihçeye eklendi!",
    "writer_cleared_msg": "Aktif paylaşım alanı temizlendi.",
    "writer_empty_warning": "Lütfen kaydedilecek bir metin girin.",
    "writer_locked_note": "Paylaşım ve güncelleme formunu açmak için yukarıda **Misafir Yazar Modu**'nu işaretleyip yazar şifresiyle giriş yapın.",
    "writer_no_post": "Henüz Misafir Yazar tarafından paylaşılmış bir söz veya bilgi bulunmuyor.",
    "writer_updated_at": "Son Güncelleme",
    "writer_char_count": "Karakter",
    "writer_history_heading": "🗂️ Eski Paylaşımlar Tarihçesi",
    "writer_no_history": "Henüz geçmiş paylaşım kaydı bulunmuyor.",
    "writer_restore_btn": "↩️ Aktif Yap",
    "writer_restored_msg": "Seçilen geçmiş paylaşım aktif alana geri yüklendi!",
    "writer_clear_history_btn": "🗑️ Tarihçeyi Temizle",
    "writer_history_cleared_msg": "Geçmiş paylaşımlar temizlendi.",
    "copy_blocked_toast": "Bu sitedeki içeriklerin kopyalanması ve paylaşılması engellenmiştir.",
    "footer_html": (
        "<div style='text-align: center; color: gray; font-size: 0.85em; line-height: 1.6;'>"
        "<b>🔒 Hukuki Koruma ve Kullanım Şartları:</b> Bu yazılım ve altyapı münhasıran manevi gelişim, dua ve ibadet amaçlı tasarlanmıştır. "
        "Başka hiçbir ticari, siyasi veya farklı amaç için kullanılamaz, kopyalanamaz ve çoğaltılamaz.<br>"
        '<b>"Birlikten güç doğar."</b> • Zikir Halkası Altyapısı • Manevi Gelişim Projesi'
        "</div>"
    ),
}

# --- EN ÖNEMLİ ZİKİRLER LİSTESİ (ÇEŞİTLERİ VE DOĞRU YAZILIŞLARIYLA) ---
KISA_ZIKIRLER = [
    "Allah",
    "Sübhanallah",
    "Elhamdülillah",
    "Allahu Ekber",
    "La ilahe illallah",
    "Estağfirullah",
    "Maşallah",
    "İnşallah",
    "Bismillah",
    "Ya Hayy Ya Kayyum",
    "Ya Rahim",
    "Ya Gaffar",
]

UZUN_ZIKIRLER = [
    "Sübhanallahi ve bihamdihi",
    "Sübhanallahil azim",
    "Sübhanallahi ve bihamdihi, Sübhanallahil azim",
    "Sübhanallahi vel hamdülillahi ve la ilahe illallahu vallahu ekber",
    "Estağfirullah el-azim ve etübü ileyh",
    "La havle vela kuvvete illa billahil aliyyil azim",
    "Hasbiyallahu ve ni'mel vekil",
    "Hasbiyallahu la ilahe illa hu, aleyhi tevekkeltu ve huve rabbul arşil azim",
    "La ilahe illa ente sübhaneke inni kuntu minez zalimin (Hz. Yunus Duası)",
    "Allahümme salli ala seyyidina Muhammedin ve ala ali seyyidina Muhammed (Salavat-ı Şerife)",
    "Allahümme barik ala seyyidina Muhammedin ve ala ali seyyidina Muhammed",
    "Salli ala seyyidina Muhammedin ve ala alihi ve sahbihi ve sellim",
    "Rabbena atina fid-dünya haseneten ve fil-ahireti haseneten ve kına azaben-nar",
    "Rabbi zidni ilmen ve fehmen ve elhıkni bis-salihin",
    "Allahümme ente rabbi la ilahe illa ente, halakteni ve ene abduke... (Seyyidü'l-İstiğfar)",
    "Allahümme inni es'elükel-afve vel-afiyete fid-dünya vel-ahireh",
    "Rabbanağfirli ve li-valideyye ve lil-mü'minine yevme yekumul-hisab",
]

ZIKIR_LISTESI = KISA_ZIKIRLER + UZUN_ZIKIRLER

# --- ZİKİRLERİN ANLAMLARI ---
ZIKIR_ANLAMLARI = {
    "Allah": "Her türlü noksanlıktan uzak, bütün kemal sıfatların sahibi olan tek gerçek İlah'ın özel adıdır.",
    "Sübhanallah": "Allah'ı her türlü eksiklikten, acizlikten ve yakışıksız sıfatlardan tenzih ederim; O yücedir.",
    "Elhamdülillah": "Her türlü hamd, övgü ve şükür yalnızca Allah'a mahsustur.",
    "Allahu Ekber": "Allah her şeyden, her varlıktan ve her tasavvurdan en büyüktür.",
    "La ilahe illallah": "Allah'tan başka ibadete ve kulluğa layık hiçbir ilah yoktur.",
    "Estağfirullah": "Allah'tan bağışlanma ve mağfiret dilerim.",
    "Maşallah": "Allah dilemiş, böyle yaratmıştır; güzellik ve bereket Allah'ın lütfundandır.",
    "İnşallah": "Allah dilerse; her işin gerçekleşmesi Allah'ın dilemesine bağlıdır.",
    "Bismillah": "Allah'ın adıyla (başlarım).",
    "Ya Hayy Ya Kayyum": "Ey ebedi ve gerçek Diri olan, varlıkları ayakta tutan ve idare eden Rabbim!",
    "Ya Rahim": "Ey müminlere ve yaratılmışlara sonsuz merhamet ve ikramda bulunan Rabbim!",
    "Ya Gaffar": "Ey kullarının günahlarını tekrar tekrar örten ve çokça bağışlayan Rabbim!",
    "Sübhanallahi ve bihamdihi": "Allah'ı O'na hamd ederek her türlü eksiklikten tenzih ederim.",
    "Sübhanallahil azim": "Azamet ve yücelik sahibi olan Allah'ı her türlü eksiklikten tenzih ederim.",
    "Sübhanallahi ve bihamdihi, Sübhanallahil azim": "Allah'ı O'na hamd ederek tenzih ederim; yüce ve azametli olan Allah'ı da her türlü eksiklikten tenzih ederim.",
    "Sübhanallahi vel hamdülillahi ve la ilahe illallahu vallahu ekber": "Allah her türlü eksiklikten münezzehtir, hamd Allah'adır, Allah'tan başka ilah yoktur ve Allah en büyüktür.",
    "Estağfirullah el-azim ve etübü ileyh": "Azamet sahibi olan Yüce Allah'tan bağışlanma diler ve tövbe ederek O'na yönelirim.",
    "La havle vela kuvvete illa billahil aliyyil azim": "Günahlardan kaçınmaya ve ibadete güç yetirmek, ancak yüce ve azametli olan Allah'ın yardımıyla mümkündür.",
    "Hasbiyallahu ve ni'mel vekil": "Allah bana yeter; O ne güzel vekil ve koruyucudur.",
    "Hasbiyallahu la ilahe illa hu, aleyhi tevekkeltu ve huve rabbul arşil azim": "Allah bana yeter; O'ndan başka ilah yoktur. Yalnız O'na tevekkül ettim ve O, büyük Arş'ın Rabbidir.",
    "La ilahe illa ente sübhaneke inni kuntu minez zalimin (Hz. Yunus Duası)": "Senden başka hiçbir ilah yoktur; Seni her türlü eksiklikten tenzih ederim. Gerçekten ben nefsine zulmedenlerden oldum.",
    "Allahümme salli ala seyyidina Muhammedin ve ala ali seyyidina Muhammed (Salavat-ı Şerife)": "Allah'ım! Efendimiz Muhammed'e ve efendimiz Muhammed'in ailesine rahmet ve bereket ihsan eyle.",
    "Allahümme barik ala seyyidina Muhammedin ve ala ali seyyidina Muhammed": "Allah'ım! Efendimiz Muhammed'i ve ailesini mübarek kıl ve bereketlerini artır.",
    "Salli ala seyyidina Muhammedin ve ala alihi ve sahbihi ve sellim": "Allah'ım! Efendimiz Muhammed'e, ailesine ve bütün ashabına rahmet eyle ve onlara selamlık/esenlik ver.",
    "Rabbena atina fid-dünya haseneten ve fil-ahireti haseneten ve kına azaben-nar": "Rabbimiz! Bize dünyada da iyilik ve güzellik ver, ahirette de iyilik ve güzellik ver; bizi cehennem azabından koru.",
    "Rabbi zidni ilmen ve fehmen ve elhıkni bis-salihin": "Rabbim! İlmimi ve anlayışımı artır ve beni salih kullar arasına kat.",
    "Allahümme ente rabbi la ilahe illa ente, halakteni ve ene abduke... (Seyyidü'l-İstiğfar)": "Allah'ım! Sen benim Rabbimsin, Senden başka ilah yoktur. Beni Sen yarattın ve ben Senin kulunum; gücüm yettiğince Senin ahdine ve vaadine bağlıyım. Yaptıklarımın şerrinden Sana sığınırım, bana verdiğin nimetleri itiraf eder ve günahlarımı da ikrar ederim; beni bağışla, çünkü günahları ancak Sen bağışlarsın.",
    "Allahümme inni es'elükel-afve vel-afiyete fid-dünya vel-ahireh": "Allah'ım! Senden dünyada ve ahirette af ve afiyet (esenlik, sağlık ve korunma) dilerim.",
    "Rabbanağfirli ve li-valideyye ve lil-mü'minine yevme yekumul-hisab": "Rabbimiz! Hesap gününde beni, anne-babamı ve bütün müminleri bağışla.",
}
# --- 1. VERİTABANI BAĞLANTISI VE KURULUMU ---
def init_db():
    conn = sqlite3.connect("global_zikir.db", timeout=15, check_same_thread=False)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")

    c.execute("""
        CREATE TABLE IF NOT EXISTS zikir_portal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secilen_zikir TEXT,
            toplam_zikir INTEGER,
            hedef_adet INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS katilimlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT,
            sehir TEXT,
            adet INTEGER,
            tarih TEXT,
            zikir_adi TEXT,
            gun TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS misafir_yazar_notu (
            id INTEGER PRIMARY KEY,
            baslik TEXT,
            icerik TEXT,
            guncellenme TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS misafir_yazar_gecmisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT,
            icerik TEXT,
            tarih TEXT
        )
    """)

    c.execute("PRAGMA table_info(katilimlar)")
    mevcut_sutunlar = {row[1] for row in c.fetchall()}
    if "zikir_adi" not in mevcut_sutunlar:
        c.execute("ALTER TABLE katilimlar ADD COLUMN zikir_adi TEXT")
    if "gun" not in mevcut_sutunlar:
        c.execute("ALTER TABLE katilimlar ADD COLUMN gun TEXT")

    c.execute("SELECT COUNT(*) FROM zikir_portal")
    if c.fetchone()[0] == 0:
        c.execute(
            """
            INSERT INTO zikir_portal (secilen_zikir, toplam_zikir, hedef_adet)
            VALUES (?, ?, ?)
            """,
            (ZIKIR_LISTESI[0], 0, 5000),
        )

    c.execute("SELECT COUNT(*) FROM misafir_yazar_notu WHERE id = 1")
    if c.fetchone()[0] == 0:
        c.execute(
            """
            INSERT INTO misafir_yazar_notu (id, baslik, icerik, guncellenme)
            VALUES (1, '', '', '')
            """
        )

    conn.commit()
    return conn


conn = init_db()
c = conn.cursor()


def veri_cek():
    cur = conn.cursor()
    cur.execute(
        "SELECT secilen_zikir, toplam_zikir, hedef_adet FROM zikir_portal WHERE id = 1"
    )
    row = cur.fetchone()
    if row:
        return row[0], int(row[1] or 0), int(row[2] or 5000)
    return ZIKIR_LISTESI[0], 0, 5000


def veri_guncelle(secilen_zikir, toplam_zikir, hedef_adet):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE zikir_portal
        SET secilen_zikir = ?, toplam_zikir = ?, hedef_adet = ?
        WHERE id = 1
        """,
        (secilen_zikir, toplam_zikir, hedef_adet),
    )
    conn.commit()


def katilim_ekle(kullanici_adi, adet, zikir_adi):
    simdi = datetime.now()
    zaman = simdi.strftime("%H:%M:%S")
    gun = simdi.strftime("%Y-%m-%d")
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO katilimlar (kullanici_adi, sehir, adet, tarih, zikir_adi, gun)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (kullanici_adi or "Misafir", "", adet, zaman, zikir_adi, gun),
    )
    conn.commit()


def ortak_havuzu_atomik_artir(kullanici_adi, zikir_adi):
    simdi = datetime.now()
    zaman = simdi.strftime("%H:%M:%S")
    gun = simdi.strftime("%Y-%m-%d")
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE zikir_portal
        SET toplam_zikir = COALESCE(toplam_zikir, 0) + 1
        WHERE id = 1
        """
    )
    cur.execute(
        """
        INSERT INTO katilimlar (kullanici_adi, sehir, adet, tarih, zikir_adi, gun)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (kullanici_adi or "Misafir", "", 1, zaman, zikir_adi, gun),
    )
    conn.commit()


def kullanici_toplam_etki_cek(kullanici_adi):
    temiz_ad = (kullanici_adi or "").strip() or "Misafir"
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COALESCE(SUM(adet), 0)
        FROM katilimlar
        WHERE COALESCE(NULLIF(TRIM(kullanici_adi), ''), 'Misafir') = ?
        """,
        (temiz_ad,),
    )
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def gunluk_zikir_ozeti(gun_str, varsayilan_zikir):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COALESCE(NULLIF(zikir_adi, ''), ?), COALESCE(SUM(adet), 0) AS adet
        FROM katilimlar
        WHERE COALESCE(gun, ?) = ?
        GROUP BY COALESCE(NULLIF(zikir_adi, ''), ?)
        ORDER BY adet DESC, 1 ASC
        """,
        (varsayilan_zikir, gun_str, gun_str, varsayilan_zikir),
    )
    return cur.fetchall()


def yazar_notu_cek():
    cur = conn.cursor()
    cur.execute(
        "SELECT baslik, icerik, guncellenme FROM misafir_yazar_notu WHERE id = 1"
    )
    row = cur.fetchone()
    return row if row else ("", "", "")


def yazar_notu_kaydet(baslik, icerik, gecmise_ekle=True):
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temiz_baslik = baslik.strip()
    temiz_icerik = icerik.strip()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE misafir_yazar_notu
        SET baslik = ?, icerik = ?, guncellenme = ?
        WHERE id = 1
        """,
        (temiz_baslik, temiz_icerik, zaman),
    )
    if gecmise_ekle and temiz_icerik:
        cur.execute(
            """
            INSERT INTO misafir_yazar_gecmisi (baslik, icerik, tarih)
            VALUES (?, ?, ?)
            """,
            (temiz_baslik, temiz_icerik, zaman),
        )
    conn.commit()


def yazar_gecmisi_cek(limit=20):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, baslik, icerik, tarih
        FROM misafir_yazar_gecmisi
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return cur.fetchall()


def yazar_gecmisi_temizle():
    cur = conn.cursor()
    cur.execute("DELETE FROM misafir_yazar_gecmisi")
    conn.commit()


# Session State Başlatma
if "kullanici_sayac" not in st.session_state:
    st.session_state.kullanici_sayac = 0
if "yonetici_yetkisi" not in st.session_state:
    st.session_state.yonetici_yetkisi = False
if "yazar_yetkisi" not in st.session_state:
    st.session_state.yazar_yetkisi = False
if "baloncuk_goster" not in st.session_state:
    st.session_state.baloncuk_goster = False

t = METINLER
yazar_yetkili_mi = bool(st.session_state.get("yazar_yetkisi", False))

# --- KOPYALAMA VE PAYLAŞIM ENGELLEYİCİ (CSS + JS) ---
st.markdown(
    """
    <style>
        html, body, .stApp, .main, .block-container,
        [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
        div, p, span, h1, h2, h3, h4, h5, h6, label, marquee, .quote-box {
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
            -webkit-touch-callout: none !important;
            -webkit-user-drag: none !important;
        }
        [data-yazar-kopya-yapistir="true"],
        [data-yazar-kopya-yapistir="true"] * {
            -webkit-user-select: text !important;
            -moz-user-select: text !important;
            -ms-user-select: text !important;
            user-select: text !important;
            -webkit-touch-callout: default !important;
        }
        @media print {
            body * {
                display: none !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.components.v1.html(
    f"""
    <script>
    (function() {{
        const uyariMesaji = {json.dumps(t["copy_blocked_toast"])};
        const yazarYetkili = {json.dumps(yazar_yetkili_mi)};
        let sonUyari = 0;

        function uyariGoster() {{
            const simdi = Date.now();
            if (simdi - sonUyari > 2500) {{
                sonUyari = simdi;
                try {{
                    const toast = document.createElement("div");
                    toast.textContent = uyariMesaji;
                    toast.style.position = "fixed";
                    toast.style.bottom = "20px";
                    toast.style.right = "20px";
                    toast.style.background = "#111827";
                    toast.style.color = "#ffffff";
                    toast.style.padding = "10px 16px";
                    toast.style.borderRadius = "8px";
                    toast.style.fontSize = "13px";
                    toast.style.fontWeight = "600";
                    toast.style.zIndex = "999999";
                    toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.25)";
                    const hedefDoc = window.parent && window.parent.document ? window.parent.document : document;
                    hedefDoc.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 2200);
                }} catch (e) {{}}
            }}
        }}

        function yazarAlanlariniGuncelle(doc) {
            if (!doc || !doc.body) return;
            const kutular = doc.querySelectorAll(
                "[data-testid='stForm'] input[type='text'], [data-testid='stForm'] textarea"
            );
            kutular.forEach((el) => {
                if (yazarYetkili) {
                    el.setAttribute("data-yazar-kopya-yapistir", "true");
                } else {
                    el.removeAttribute("data-yazar-kopya-yapistir");
                }
            });
        }

        function yazarNotKutusuMu(target) {
            if (!target || !yazarYetkili) return false;
            const el = target.nodeType === 1 ? target : target.parentElement;
            if (!el) return false;
            return Boolean(el.closest("[data-yazar-kopya-yapistir='true']"));
        }

        function korumaUygula(doc) {
            if (!doc) return;
            yazarAlanlariniGuncelle(doc);

            if (!doc.__zikirYazarObserver && doc.body) {
                doc.__zikirYazarObserver = true;
                const observer = new MutationObserver(() => yazarAlanlariniGuncelle(doc));
                observer.observe(doc.body, { childList: true, subtree: true });
            }

            if (doc.__zikirKorumaAktif) return;
            doc.__zikirKorumaAktif = true;

            if (navigator && navigator.share) {
                try {
                    navigator.share = async function() {
                        uyariGoster();
                        throw new Error("Sharing disabled");
                    };
                } catch (e) {}
            }

            doc.addEventListener("contextmenu", function(e) {
                if (yazarNotKutusuMu(e.target)) {
                    return true;
                }
                e.preventDefault();
                uyariGoster();
            }, true);

            ["copy", "cut", "paste", "dragstart", "selectstart"].forEach(function(olay) {
                doc.addEventListener(olay, function(e) {
                    if (yazarNotKutusuMu(e.target) && olay !== "dragstart") {
                        return true;
                    }
                    e.preventDefault();
                    if (olay === "copy" || olay === "cut") {
                        try {
                            if (e.clipboardData) {
                                e.clipboardData.setData("text/plain", "");
                            }
                        } catch (err) {}
                        uyariGoster();
                    }
                }, true);
            });

            doc.addEventListener("keydown", function(e) {
                const key = (e.key || "").toLowerCase();
                if ((e.ctrlKey || e.metaKey) && ["c", "x", "v", "a", "s", "u", "p"].includes(key)) {
                    const izinliKisayol = yazarNotKutusuMu(e.target) && ["c", "x", "v", "a"].includes(key);
                    if (!izinliKisayol) {
                        e.preventDefault();
                        uyariGoster();
                    }
                }
                if (e.key === "F12" || ((e.ctrlKey || e.metaKey) && e.shiftKey && ["i", "j", "c"].includes(key))) {
                    e.preventDefault();
                    uyariGoster();
                }
            }, true);
        }

        korumaUygula(document);
        try {
            if (window.parent && window.parent.document) {
                korumaUygula(window.parent.document);
            }
        } catch (e) {}
    }})();
    </script>
    """,
    height=0,
)
# --- 2. KENAR ÇUBUĞU: KULLANICI & YÖNETİCİ PANELİ ---
st.sidebar.header(t["participant_header"])
kullanici_adi = st.sidebar.text_input(t["name_label"], value=t["default_name"])
misafir_yazar_aktif = st.sidebar.checkbox(
    t["guest_writer_mode"],
    value=(
        st.session_state.yazar_yetkisi
        or (kullanici_adi.strip().lower() == "misafir yazar")
    ),
    help=t["guest_writer_hint"],
)
if not misafir_yazar_aktif and st.session_state.yazar_yetkisi:
    st.session_state.yazar_yetkisi = False

st.sidebar.divider()
st.sidebar.header(t["admin_header"])

aktif_zikir, toplam_zikir, hedef_adet = veri_cek()

if not st.session_state.yonetici_yetkisi:
    girilen_sifre = st.sidebar.text_input(t["admin_pass_label"], type="password")
    if st.sidebar.button(t["login_btn"], use_container_width=True):
        if girilen_sifre == YONETICI_SIFRESI:
            st.session_state.yonetici_yetkisi = True
            st.rerun()
        else:
            st.sidebar.error(t["wrong_pass"])
else:
    st.sidebar.success(t["admin_active"])

    st.sidebar.metric(
        label=t["admin_pool_metric"],
        value=f"{int(toplam_zikir or 0):,}".replace(",", "."),
    )

    mevcut_index = (
        ZIKIR_LISTESI.index(aktif_zikir) if aktif_zikir in ZIKIR_LISTESI else 0
    )
    secim = st.sidebar.selectbox(
        t["select_dhikr_admin"], ZIKIR_LISTESI, index=mevcut_index
    )

    if secim != aktif_zikir:
        veri_guncelle(secim, toplam_zikir, hedef_adet)
        st.rerun()

    with st.sidebar.expander(t["admin_dhikr_catalog_title"], expanded=False):
        st.markdown(f"**{t['short_dhikr_group']}**")
        for zikir in KISA_ZIKIRLER:
            anlam = ZIKIR_ANLAMLARI.get(zikir, "")
            st.markdown(
                f"""
                <div class="quote-box" style="padding: 8px 10px; margin-bottom: 6px; border-left: 3px solid #b8860b; border-radius: 4px; background-color: #fcfcfd;">
                    <strong>{zikir}</strong><br>
                    <span style="font-size: 0.85rem; color: #555555;">{anlam}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(f"**{t['long_dhikr_group']}**")
        for zikir in UZUN_ZIKIRLER:
            anlam = ZIKIR_ANLAMLARI.get(zikir, "")
            st.markdown(
                f"""
                <div class="quote-box" style="padding: 8px 10px; margin-bottom: 6px; border-left: 3px solid #1f77b4; border-radius: 4px; background-color: #fcfcfd;">
                    <strong>{zikir}</strong><br>
                    <span style="font-size: 0.85rem; color: #555555;">{anlam}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    yeni_hedef = st.sidebar.number_input(
        t["target_label"],
        min_value=100,
        max_value=1000000,
        value=hedef_adet,
        step=100,
    )
    if yeni_hedef != hedef_adet:
        st.session_state.baloncuk_goster = False
        veri_guncelle(aktif_zikir, toplam_zikir, yeni_hedef)
        st.rerun()

    st.sidebar.markdown(f"### {t['daily_report_title']} ({datetime.now().strftime('%Y-%m-%d')})")
    bugun_str = datetime.now().strftime("%Y-%m-%d")
    gunluk_kayitlar = gunluk_zikir_ozeti(bugun_str, aktif_zikir)

    if gunluk_kayitlar:
        bugun_toplam = sum(int(adet or 0) for _, adet in gunluk_kayitlar)
        st.sidebar.metric(t["daily_total_label"], f"{bugun_toplam:,}".replace(",", "."))
        df_gunluk = pd.DataFrame(
            [
                {t["col_dhikr"]: z_adi, t["col_count"]: int(z_adet or 0)}
                for z_adi, z_adet in gunluk_kayitlar
            ]
        )
        st.sidebar.dataframe(df_gunluk, use_container_width=True, hide_index=True)
    else:
        st.sidebar.info(t["no_daily_records"])

    if st.sidebar.button(
        t["reset_pool_btn"], type="secondary", use_container_width=True
    ):
        st.session_state.kullanici_sayac = 0
        st.session_state.baloncuk_goster = False
        veri_guncelle(aktif_zikir, 0, hedef_adet)
        cur = conn.cursor()
        cur.execute("DELETE FROM katilimlar")
        conn.commit()
        st.sidebar.success(t["pool_reset_msg"])
        st.rerun()

    if st.sidebar.button(t["logout_btn"], use_container_width=True):
        st.session_state.yonetici_yetkisi = False
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(t["sleep_note"])

# --- 0. SAYFA BAŞI KAYAR YAZI (AYET & BİRLİK MESAJI) ---
st.markdown(
    f"""
    <div style="background-color:#f4f6f8; border:2px solid #111111; border-radius:10px; padding:12px 14px; margin-bottom:16px;">
        <marquee behavior="scroll" direction="left" scrollamount="5" onmouseover="this.stop();" onmouseout="this.start();" style="color:#000000; font-size:22px; font-weight:700; letter-spacing:0.3px;">
            {t["top_marquee"]}
        </marquee>
    </div>
    """,
    unsafe_allow_html=True,
)
# --- 3. ANA SAYFA ARAYÜZÜ ---
st.title(t["main_title"])
st.markdown(t["main_subtitle"])
st.divider()


@st.fragment(run_every=2)
def canli_zikir_havuzu(aktif_kullanici):
    guncel_zikir, guncel_toplam, guncel_hedef = veri_cek()

    hedef_sayi = max(1, int(guncel_hedef or 1))
    havuz_sayi = max(0, int(guncel_toplam or 0))
    kisisel_sayi = int(st.session_state.kullanici_sayac)
    kullanici_toplam_etki = kullanici_toplam_etki_cek(aktif_kullanici)
    etki_yuzdesi = (kullanici_toplam_etki / hedef_sayi) * 100
    havuz_yuzdesi = min(100.0, (havuz_sayi / hedef_sayi) * 100)

    aktif_zikir_anlami = ZIKIR_ANLAMLARI.get(guncel_zikir, "")

    st.markdown(t["active_dhikr_heading"])
    st.markdown(
        f"""
        <div class="quote-box" style="background-color:#fff8e7; border:3px solid #111111; border-radius:12px; padding:18px 20px; text-align:center; margin-top:8px; margin-bottom:16px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
            <div style="color:#000000; font-size:28px; font-weight:900; text-transform:uppercase; letter-spacing:0.6px; line-height:1.35;">
                {guncel_zikir}
            </div>
            <div style="color:#444444; font-size:15px; font-weight:500; margin-top:10px; padding-top:10px; border-top:1px dashed #d4b46a; line-height:1.5;">
                <strong>{t["active_dhikr_meaning_label"]}</strong> {aktif_zikir_anlami}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2 = st.columns(2)
    with m1:
        st.metric(
            label=f"🎯 {t['target_count_label']}",
            value=f"{hedef_sayi:,} {t['unit_count']}".replace(",", "."),
        )
    with m2:
        st.metric(
            label=f"🌐 {t['shared_pool_reached_label']}",
            value=f"{havuz_sayi:,} {t['unit_count']}".replace(",", "."),
            delta=f"%{havuz_yuzdesi:.1f}",
        )

    m3, m4 = st.columns(2)
    with m3:
        st.metric(
            label=f"👤 {t['your_contribution']} ({aktif_kullanici})",
            value=f"{kisisel_sayi:,} {t['unit_count']}".replace(",", "."),
        )
    with m4:
        st.metric(
            label=f"📈 {t['your_goal_impact_label']}",
            value=f"{kullanici_toplam_etki:,} {t['unit_count']}".replace(",", "."),
            delta=f"+%{etki_yuzdesi:.2f}",
        )

    st.progress(min(1.0, havuz_sayi / hedef_sayi))
    st.caption(
        t["goal_progress_caption"]
        .format(
            pct=f"{havuz_yuzdesi:.1f}",
            current=havuz_sayi,
            target=hedef_sayi,
        )
        .replace(",", ".")
    )
    st.write("")

    # --- 4. ZİKİR ÇEKME BUTONU ---
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        if st.button(t["pull_btn"], use_container_width=True, type="primary"):
            st.session_state.kullanici_sayac += 1
            yeni_toplam = havuz_sayi + 1

            if hedef_sayi > 0 and havuz_sayi < hedef_sayi <= yeni_toplam:
                st.session_state.baloncuk_goster = True

            ortak_havuzu_atomik_artir(aktif_kullanici, guncel_zikir)
            st.rerun(scope="fragment")

    with col_btn2:
        if st.button(t["reset_personal_btn"], use_container_width=True):
            st.session_state.kullanici_sayac = 0
            st.toast(t["personal_reset_toast"])
            st.rerun(scope="fragment")

    if st.session_state.baloncuk_goster:
        st.balloons()
        st.session_state.baloncuk_goster = False

    if havuz_sayi >= hedef_sayi:
        st.success(t["goal_reached_msg"].format(hedef=hedef_sayi).replace(",", "."))
        st.markdown(
            f"""
            <div style="background-color:#e8f4f8; padding:14px 16px; border-radius:8px; border-left: 6px solid #1f77b4; margin-top:15px; margin-bottom:15px;">
                <marquee behavior="scroll" direction="left" scrollamount="5" onmouseover="this.stop();" onmouseout="this.start();" style="font-weight: 800; font-size: 20px; color: #1a252f; letter-spacing: 0.4px;">
                    {t["goal_marquee"]}
                </marquee>
            </div>
            """,
            unsafe_allow_html=True,
        )


canli_zikir_havuzu(kullanici_adi)

st.divider()

# --- MİSAFİR YAZAR PAYLAŞIM, GÜNCELLEME VE TARİHÇE ALANI ---
st.subheader(t["writer_section_heading"])
st.markdown(t["writer_section_desc"])

yazar_baslik, yazar_icerik, yazar_guncellenme = yazar_notu_cek()
yazar_gecmisi = yazar_gecmisi_cek()

if yazar_icerik:
    gosterilecek_baslik = yazar_baslik or t["writer_default_title"]
    gosterilecek_icerik = yazar_icerik
    icerik_html = (
        gosterilecek_icerik.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
    st.markdown(
        f"""
        <div style="background-color:#f8fafc; border:2px solid #334155; border-radius:10px; padding:16px 18px; margin-bottom:14px;">
            <div style="font-size:18px; font-weight:800; color:#0f172a; margin-bottom:8px;">
                🖋️ {gosterilecek_baslik}
            </div>
            <div style="font-size:16px; color:#1e293b; line-height:1.65; white-space:normal;">
                {icerik_html}
            </div>
            <div style="font-size:12px; color:#64748b; margin-top:10px;">
                {t["writer_updated_at"]}: {yazar_guncellenme} • {t["writer_char_count"]}: {len(gosterilecek_icerik)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info(t["writer_no_post"])

if misafir_yazar_aktif:
    if not st.session_state.yazar_yetkisi:
        p_col1, p_col2 = st.columns([3, 1])
        with p_col1:
            girilen_yazar_sifre = st.text_input(
                t["writer_pass_label"], type="password", key="yazar_sifre_input"
            )
        with p_col2:
            st.write("")
            st.write("")
            if st.button(t["writer_login_btn"], use_container_width=True):
                if girilen_yazar_sifre == MISAFIR_YAZAR_SIFRESI:
                    st.session_state.yazar_yetkisi = True
                    st.rerun()
                else:
                    st.error(t["writer_wrong_pass"])
    else:
        st.success(t["writer_auth_active"])
        if st.button(t["writer_logout_btn"]):
            st.session_state.yazar_yetkisi = False
            st.rerun()

        with st.form("misafir_yazar_form", clear_on_submit=False):
            yeni_baslik = st.text_input(
                t["writer_title_label"],
                value=yazar_baslik or t["writer_default_title"],
                max_chars=200,
            )
            yeni_icerik = st.text_area(
                t["writer_body_label"],
                value=yazar_icerik,
                height=220,
                max_chars=10000,
                placeholder=t["writer_body_placeholder"],
            )
            f_col1, f_col2 = st.columns([2, 1])
            with f_col1:
                kaydet_basildi = st.form_submit_button(
                    t["writer_save_btn"], use_container_width=True, type="primary"
                )
            with f_col2:
                temizle_basildi = st.form_submit_button(
                    t["writer_clear_btn"], use_container_width=True
                )

            if kaydet_basildi:
                if yeni_icerik.strip():
                    yazar_notu_kaydet(yeni_baslik, yeni_icerik, gecmise_ekle=True)
                    st.success(t["writer_saved_msg"])
                    st.rerun()
                else:
                    st.warning(t["writer_empty_warning"])

            if temizle_basildi:
                yazar_notu_kaydet("", "", gecmise_ekle=False)
                st.success(t["writer_cleared_msg"])
                st.rerun()

        st.markdown(f"#### {t['writer_history_heading']}")
        if yazar_gecmisi:
            if st.button(t["writer_clear_history_btn"]):
                yazar_gecmisi_temizle()
                st.success(t["writer_history_cleared_msg"])
                st.rerun()

            for kayit_id, g_baslik, g_icerik, g_tarih in yazar_gecmisi:
                g_baslik_goster = g_baslik or t["writer_default_title"]
                g_icerik_goster = g_icerik
                baslik_etiketi = f"{g_tarih} — {g_baslik_goster}"
                with st.expander(baslik_etiketi):
                    st.write(g_icerik_goster)
                    if st.button(
                        t["writer_restore_btn"], key=f"restore_yazar_{kayit_id}"
                    ):
                        yazar_notu_kaydet(g_baslik, g_icerik, gecmise_ekle=False)
                        st.success(t["writer_restored_msg"])
                        st.rerun()
        else:
            st.caption(t["writer_no_history"])
else:
    st.caption(t["writer_locked_note"])

st.divider()

# --- 5. SORUMLULUK REDDİ, YASAL KORUMA VE ALT BİLGİ ---
with st.expander(SORUMLULUK_REDDI_BASLIK, expanded=False):
    st.caption(SORUMLULUK_REDDI_METNI)

st.markdown(t["footer_html"], unsafe_allow_html=True)