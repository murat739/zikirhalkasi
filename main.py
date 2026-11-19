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
    YONETICI_SIFRESI = "tarum1453."

try:
    MISAFIR_YAZAR_SIFRESI = st.secrets["MISAFIR_YAZAR_SIFRESI"]
except Exception:
    MISAFIR_YAZAR_SIFRESI = "tarum1453."

# --- DİL SÖZLÜĞÜ (TÜRKÇE / İNGİLİZCE) ---
METINLER = {
    "tr": {
        "top_marquee": (
            '📖 "BENİ ANIN Kİ, BEN DE SİZİ ANAYIM; BANA ŞÜKREDİN, SAKIN NANKÖRLÜK ETMEYİN." '
            "<strong>[BAKARA SURESİ, 2/152]</strong>"
            " &nbsp;&nbsp;&nbsp;✦&nbsp;&nbsp;&nbsp; "
            "BİRLİKTE GÜÇLENEREK BÜYÜYELİM VE KAİNATA ZİKRİMİZ DAĞILSIN."
        ),
        "lang_label": "🌐 Dil / Language",
        "participant_header": "🌍 Katılımcı Bilgileri",
        "name_label": "Adınız / Rumuzunuz:",
        "default_name": "Misafir",
        "guest_writer_mode": "✍️ Misafir Yazar Modu (Paylaş ve Güncelle)",
        "guest_writer_hint": "Yüksek metin kapasiteli paylaşım, güncelleme ve tarihçe alanını açmak için bu seçeneği işaretleyin.",
        "city_label": "Bulunduğunuz Şehir / Kutsal Merkez / Ülke:",
        "admin_header": "🔐 Yönetici / Kurucu Paneli",
        "admin_pass_label": "Yönetici Şifresi:",
        "login_btn": "Giriş Yap",
        "wrong_pass": "Hatalı yönetici şifresi!",
        "admin_active": "Yönetici yetkisi aktif.",
        "select_dhikr_admin": "Ortak Çekilecek Zikri Belirle:",
        "target_label": "Ortak Hedef Sayısı:",
        "reset_pool_btn": "🗑️ Ortak Havuzu Sıfırla",
        "pool_reset_msg": "Havuz sıfırlandı!",
        "logout_btn": "🚪 Yönetici Çıkışı",
        "daily_report_title": "📊 Günlük Zikir Raporu",
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
            "Mekke ve Medine'den, Türkiye'nin 81 ilinden ve dünyanın dört bir "
            "yanındaki tüm ülkelerden bağlanan müminlerin ortak niyetle buluştuğu manevi dijital halka."
        ),
        "active_dhikr_heading": "### 📌 ÇEKİLECEK ORTAK ZİKİR:",
        "your_contribution": "Sizin Katkınız",
        "unit_count": "Adet",
        "global_pool": "Global Havuz Toplamı",
        "pull_btn": "📿 BİR ZİKİR ÇEK (Tıkla)",
        "reset_personal_btn": "🔄 Kişisel Sayacı Sıfırla",
        "goal_reached_msg": "🎉 ELHAMDÜLİLLAH! BELİRLENEN {hedef:,} ADETLİK GLOBAL ORTAK HEDEF TAMAMLANDI!",
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
        "writer_auto_translated": "İngilizce dile otomatik çevrildi",
        "writer_history_heading": "🗂️ Eski Paylaşımlar Tarihçesi",
        "writer_no_history": "Henüz geçmiş paylaşım kaydı bulunmuyor.",
        "writer_restore_btn": "↩️ Aktif Yap",
        "writer_restored_msg": "Seçilen geçmiş paylaşım aktif alana geri yüklendi!",
        "writer_clear_history_btn": "🗑️ Tarihçeyi Temizle",
        "writer_history_cleared_msg": "Geçmiş paylaşımlar temizlendi.",
        "map_heading": "🗺️ Global Zikir Halkası Haritası",
        "map_desc": (
            "Mekke ve Medine başta olmak üzere katılan şehirlerin ve ülkelerin dünya "
            "üzerindeki konumları canlı olarak işaretlenmektedir:"
        ),
        "no_map_data": (
            "Henüz haritada gösterilecek konum verisi yok. İlk zikri çekerek haritayı "
            "canlandırın!"
        ),
        "city_stats_heading": "📜 Şehir, Merkez ve Ülke Bazlı Zikir Sayıları",
        "city_item": "✨ **{sehir} ({adet} adet)**",
        "no_city_data": "Henüz zikir kaydı bulunmuyor.",
        "footer_html": (
            "<div style='text-align: center; color: gray; font-size: 0.85em; line-height: 1.6;'>"
            "<b>🔒 Hukuki Koruma ve Kullanım Şartları:</b> Bu yazılım ve altyapı münhasıran manevi gelişim, dua ve ibadet amaçlı tasarlanmıştır. "
            "Başka hiçbir ticari, siyasi veya farklı amaç için kullanılamaz, kopyalanamaz ve çoğaltılamaz.<br>"
            '<b>"Birlikten güç doğar."</b> • Global Zikir Halkası Altyapısı • Manevi Gelişim Projesi'
            "</div>"
        ),
    },
    "en": {
        "top_marquee": (
            '📖 "SO REMEMBER ME; I WILL REMEMBER YOU. AND BE GRATEFUL TO ME, AND DO NOT DENY ME." '
            "<strong>[SURAH AL-BAQARAH, 2/152]</strong>"
            " &nbsp;&nbsp;&nbsp;✦&nbsp;&nbsp;&nbsp; "
            "LET US GROW STRONGER TOGETHER AND LET OUR REMEMBRANCE SPREAD ACROSS THE UNIVERSE."
        ),
        "lang_label": "🌐 Language / Dil",
        "participant_header": "🌍 Participant Details",
        "name_label": "Your Name / Nickname:",
        "default_name": "Guest",
        "guest_writer_mode": "✍️ Guest Writer Mode (Share & Update)",
        "guest_writer_hint": "Enable this option to open the high-capacity sharing, updating, and history area.",
        "city_label": "Your City / Sacred Center / Country:",
        "admin_header": "🔐 Admin / Founder Panel",
        "admin_pass_label": "Admin Password:",
        "login_btn": "Log In",
        "wrong_pass": "Incorrect admin password!",
        "admin_active": "Admin access active.",
        "select_dhikr_admin": "Select Shared Dhikr:",
        "target_label": "Shared Target Count:",
        "reset_pool_btn": "🗑️ Reset Shared Pool",
        "pool_reset_msg": "Shared pool has been reset!",
        "logout_btn": "🚪 Admin Logout",
        "daily_report_title": "📊 Daily Dhikr Report",
        "daily_total_label": "Total Dhikr Pulled Today",
        "col_dhikr": "Dhikr",
        "col_count": "Count",
        "no_daily_records": "No dhikr has been pulled today yet.",
        "sleep_note": (
            "💡 *Note:* This web application is hosted on free servers. "
            "If there is no activity for a long time, the app may go to sleep "
            "(a 'Zzzz' icon may appear on screen).\n\n"
            "💤 If you see that screen, click the blue "
            "*'Yes, get this app back up!'* button and wait 15-30 seconds "
            "for the app to wake up."
        ),
        "main_title": "DHIKR CIRCLE",
        "main_subtitle": (
            "A spiritual digital circle where believers from Makkah and Madinah, "
            "all 81 provinces of Türkiye, and countries around the world unite with a shared intention."
        ),
        "active_dhikr_heading": "### 📌 SHARED DHIKR TO RECITE:",
        "your_contribution": "Your Contribution",
        "unit_count": "Count",
        "global_pool": "Global Pool Total",
        "pull_btn": "📿 PULL ONE DHIKR (Click)",
        "reset_personal_btn": "🔄 Reset Personal Counter",
        "goal_reached_msg": "🎉 ALHAMDULILLAH! THE TARGET OF {hedef:,} SHARED DHIKR HAS BEEN COMPLETED!",
        "goal_marquee": (
            '📜 QUR\'AN (VERSE): "SO REMEMBER ME; I WILL REMEMBER YOU." '
            "(AL-BAQARAH, 152) &nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp; 📜 "
            'HADITH: "THE EXAMPLE OF THE ONE WHO REMEMBERS THEIR LORD AND THE ONE WHO DOES NOT '
            'IS LIKE THE LIVING AND THE DEAD." (BUKHARI) &nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp; ✨ '
            'RUMI: "DHIKR IS THE POLISH OF THE HEART AND REMOVER OF ITS RUST; IT IS THE NOURISHMENT OF THE SOUL." '
            "&nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp; 💡 SPIRITUAL MOTTO: "
            '"UNITY BRINGS STRENGTH; HEARTS UNITE THROUGH SHARED INTENTION AND DHIKR."'
        ),
        "writer_section_heading": "✍️ GUEST WRITER CORNER (QUOTES & KNOWLEDGE)",
        "writer_section_desc": "High-capacity sharing space created, updated, and archived exclusively by the Guest Writer:",
        "writer_pass_label": "Guest Writer Password:",
        "writer_login_btn": "🔓 Writer Login",
        "writer_logout_btn": "🔒 Writer Logout",
        "writer_wrong_pass": "Incorrect Guest Writer password!",
        "writer_auth_active": "Guest Writer access active. You can publish, update, and manage history.",
        "writer_title_label": "Title / Topic:",
        "writer_default_title": "Quote & Spiritual Note",
        "writer_body_label": "Quote / Information / Long Text (Up to 10,000 characters):",
        "writer_body_placeholder": "Write a quote, reflection, or detailed note of any length here and update it whenever needed...",
        "writer_save_btn": "💾 Save / Update Post",
        "writer_clear_btn": "🧹 Clear Active Post",
        "writer_saved_msg": "Post saved, updated, and added to history!",
        "writer_cleared_msg": "Active post cleared.",
        "writer_empty_warning": "Please enter text to save.",
        "writer_locked_note": "Enable **Guest Writer Mode** above and sign in with the writer password to open the sharing and update form.",
        "writer_no_post": "No quote or note has been shared by the Guest Writer yet.",
        "writer_updated_at": "Last Updated",
        "writer_char_count": "Characters",
        "writer_auto_translated": "Auto-translated to English",
        "writer_history_heading": "🗂️ Past Posts History",
        "writer_no_history": "No past posts in history yet.",
        "writer_restore_btn": "↩️ Set Active",
        "writer_restored_msg": "Selected past post restored to active area!",
        "writer_clear_history_btn": "🗑️ Clear History",
        "writer_history_cleared_msg": "Past posts history cleared.",
        "map_heading": "🗺️ Global Dhikr Circle Map",
        "map_desc": (
            "Locations of participating cities and countries—starting with Makkah and Madinah—"
            "are marked live on the world map:"
        ),
        "no_map_data": (
            "No location data to display on the map yet. Pull the first dhikr to bring the map to life!"
        ),
        "city_stats_heading": "📜 Dhikr Counts by City, Center & Country",
        "city_item": "✨ **{sehir} ({adet} count)**",
        "no_city_data": "No dhikr records yet.",
        "footer_html": (
            "<div style='text-align: center; color: gray; font-size: 0.85em; line-height: 1.6;'>"
            "<b>🔒 Legal Protection & Terms of Use:</b> This software and infrastructure are designed exclusively for spiritual growth, supplication, and worship. "
            "It may not be used, copied, or reproduced for any commercial, political, or other purpose.<br>"
            '<b>"Unity brings strength."</b> • Global Dhikr Circle Infrastructure • Spiritual Growth Project'
            "</div>"
        ),
    },
}

# --- KUTSAL MERKEZLER, TÜRKİYE 81 İL VE TÜM DÜNYA ÜLKELERİ ---
KUTSAL_MERKEZLER = [
    "Mekke (Suudi Arabistan)",
    "Medine (Suudi Arabistan)",
]

DUNYA_ULKELERI = {
    "Afganistan": {"tr": "Afganistan", "en": "Afghanistan", "lat": 34.5553, "lon": 69.2075},
    "Almanya": {"tr": "Almanya", "en": "Germany", "lat": 52.5200, "lon": 13.4050},
    "Amerika Birleşik Devletleri": {"tr": "Amerika Birleşik Devletleri", "en": "United States", "lat": 38.9072, "lon": -77.0369},
    "Andorra": {"tr": "Andorra", "en": "Andorra", "lat": 42.5063, "lon": 1.5218},
    "Angola": {"tr": "Angola", "en": "Angola", "lat": -8.8383, "lon": 13.2344},
    "Antigua ve Barbuda": {"tr": "Antigua ve Barbuda", "en": "Antigua and Barbuda", "lat": 17.1274, "lon": -61.8468},
    "Arjantin": {"tr": "Arjantin", "en": "Argentina", "lat": -34.6037, "lon": -58.3816},
    "Arnavutluk": {"tr": "Arnavutluk", "en": "Albania", "lat": 41.3275, "lon": 19.8187},
    "Avustralya": {"tr": "Avustralya", "en": "Australia", "lat": -35.2809, "lon": 149.1300},
    "Avusturya": {"tr": "Avusturya", "en": "Austria", "lat": 48.2082, "lon": 16.3738},
    "Azerbaycan": {"tr": "Azerbaycan", "en": "Azerbaijan", "lat": 40.4093, "lon": 49.8671},
    "Bahamalar": {"tr": "Bahamalar", "en": "Bahamas", "lat": 25.0343, "lon": -77.3963},
    "Bahreyn": {"tr": "Bahreyn", "en": "Bahrain", "lat": 26.2285, "lon": 50.5860},
    "Bangladeş": {"tr": "Bangladeş", "en": "Bangladesh", "lat": 23.8103, "lon": 90.4125},
    "Barbados": {"tr": "Barbados", "en": "Barbados", "lat": 13.1939, "lon": -59.5432},
    "Belarus": {"tr": "Belarus", "en": "Belarus", "lat": 53.9006, "lon": 27.5590},
    "Belçika": {"tr": "Belçika", "en": "Belgium", "lat": 50.8503, "lon": 4.3517},
    "Belize": {"tr": "Belize", "en": "Belize", "lat": 17.2510, "lon": -88.7590},
    "Benin": {"tr": "Benin", "en": "Benin", "lat": 6.4969, "lon": 2.6289},
    "Bhutan": {"tr": "Bhutan", "en": "Bhutan", "lat": 27.4728, "lon": 89.6390},
    "Birleşik Arap Emirlikleri": {"tr": "Birleşik Arap Emirlikleri", "en": "United Arab Emirates", "lat": 24.4539, "lon": 54.3773},
    "Birleşik Krallık": {"tr": "Birleşik Krallık", "en": "United Kingdom", "lat": 51.5074, "lon": -0.1278},
    "Bolivya": {"tr": "Bolivya", "en": "Bolivia", "lat": -16.4897, "lon": -68.1193},
    "Bosna-Hersek": {"tr": "Bosna-Hersek", "en": "Bosnia and Herzegovina", "lat": 43.8563, "lon": 18.4131},
    "Botsvana": {"tr": "Botsvana", "en": "Botswana", "lat": -24.6282, "lon": 25.9231},
    "Brezilya": {"tr": "Brezilya", "en": "Brazil", "lat": -15.7975, "lon": -47.8919},
    "Brunei": {"tr": "Brunei", "en": "Brunei", "lat": 4.9031, "lon": 114.9398},
    "Bulgaristan": {"tr": "Bulgaristan", "en": "Bulgaria", "lat": 42.6977, "lon": 23.3219},
    "Burkina Faso": {"tr": "Burkina Faso", "en": "Burkina Faso", "lat": 12.3714, "lon": -1.5197},
    "Burundi": {"tr": "Burundi", "en": "Burundi", "lat": -3.3614, "lon": 29.3599},
    "Cezayir": {"tr": "Cezayir", "en": "Algeria", "lat": 36.7538, "lon": 3.0588},
    "Cibuti": {"tr": "Cibuti", "en": "Djibouti", "lat": 11.5886, "lon": 43.1456},
    "Çad": {"tr": "Çad", "en": "Chad", "lat": 12.1348, "lon": 15.0557},
    "Çekya": {"tr": "Çekya", "en": "Czechia", "lat": 50.0755, "lon": 14.4378},
    "Çin": {"tr": "Çin", "en": "China", "lat": 39.9042, "lon": 116.4074},
    "Danimarka": {"tr": "Danimarka", "en": "Denmark", "lat": 55.6761, "lon": 12.5683},
    "Doğu Timor": {"tr": "Doğu Timor", "en": "Timor-Leste", "lat": -8.5569, "lon": 125.5603},
    "Dominik Cumhuriyeti": {"tr": "Dominik Cumhuriyeti", "en": "Dominican Republic", "lat": 18.4861, "lon": -69.9312},
    "Dominika": {"tr": "Dominika", "en": "Dominica", "lat": 15.3092, "lon": -61.3794},
    "Ekvador": {"tr": "Ekvador", "en": "Ecuador", "lat": -0.1807, "lon": -78.4678},
    "Ekvator Ginesi": {"tr": "Ekvator Ginesi", "en": "Equatorial Guinea", "lat": 3.7504, "lon": 8.7371},
    "El Salvador": {"tr": "El Salvador", "en": "El Salvador", "lat": 13.6929, "lon": -89.2182},
    "Endonezya": {"tr": "Endonezya", "en": "Indonesia", "lat": -6.2088, "lon": 106.8456},
    "Eritre": {"tr": "Eritre", "en": "Eritrea", "lat": 15.3229, "lon": 38.9251},
    "Ermenistan": {"tr": "Ermenistan", "en": "Armenia", "lat": 40.1792, "lon": 44.4991},
    "Estonya": {"tr": "Estonya", "en": "Estonia", "lat": 59.4370, "lon": 24.7536},
    "Esvatini": {"tr": "Esvatini", "en": "Eswatini", "lat": -26.3054, "lon": 31.1367},
    "Etiyopya": {"tr": "Etiyopya", "en": "Ethiopia", "lat": 9.0300, "lon": 38.7400},
    "Fas": {"tr": "Fas", "en": "Morocco", "lat": 33.9716, "lon": -6.8498},
    "Fiji": {"tr": "Fiji", "en": "Fiji", "lat": -18.1416, "lon": 178.4419},
    "Fildişi Sahili": {"tr": "Fildişi Sahili", "en": "Côte d'Ivoire", "lat": 6.8276, "lon": -5.2893},
    "Filipinler": {"tr": "Filipinler", "en": "Philippines", "lat": 14.5995, "lon": 120.9842},
    "Filistin": {"tr": "Filistin", "en": "Palestine", "lat": 31.7683, "lon": 35.2137},
    "Finlandiya": {"tr": "Finlandiya", "en": "Finland", "lat": 60.1699, "lon": 24.9384},
    "Fransa": {"tr": "Fransa", "en": "France", "lat": 48.8566, "lon": 2.3522},
    "Gabon": {"tr": "Gabon", "en": "Gabon", "lat": 0.4162, "lon": 9.4673},
    "Gambiya": {"tr": "Gambiya", "en": "Gambia", "lat": 13.4549, "lon": -16.5790},
    "Gana": {"tr": "Gana", "en": "Ghana", "lat": 5.6037, "lon": -0.1870},
    "Gine": {"tr": "Gine", "en": "Guinea", "lat": 9.6412, "lon": -13.5784},
    "Gine-Bissau": {"tr": "Gine-Bissau", "en": "Guinea-Bissau", "lat": 11.8817, "lon": -15.6178},
    "Grenada": {"tr": "Grenada", "en": "Grenada", "lat": 12.0561, "lon": -61.7488},
    "Guatemala": {"tr": "Guatemala", "en": "Guatemala", "lat": 14.6349, "lon": -90.5069},
    "Guyana": {"tr": "Guyana", "en": "Guyana", "lat": 6.8013, "lon": -58.1551},
    "Güney Afrika": {"tr": "Güney Afrika", "en": "South Africa", "lat": -25.7479, "lon": 28.2293},
    "Güney Kore": {"tr": "Güney Kore", "en": "South Korea", "lat": 37.5665, "lon": 126.9780},
    "Güney Sudan": {"tr": "Güney Sudan", "en": "South Sudan", "lat": 4.8517, "lon": 31.5825},
    "Gürcistan": {"tr": "Gürcistan", "en": "Georgia", "lat": 41.7151, "lon": 44.8271},
    "Haiti": {"tr": "Haiti", "en": "Haiti", "lat": 18.5944, "lon": -72.3074},
    "Hırvatistan": {"tr": "Hırvatistan", "en": "Croatia", "lat": 45.8150, "lon": 15.9819},
    "Hindistan": {"tr": "Hindistan", "en": "India", "lat": 28.6139, "lon": 77.2090},
    "Hollanda": {"tr": "Hollanda", "en": "Netherlands", "lat": 52.3676, "lon": 4.9041},
    "Honduras": {"tr": "Honduras", "en": "Honduras", "lat": 14.0723, "lon": -87.1921},
    "Irak": {"tr": "Irak", "en": "Iraq", "lat": 33.3152, "lon": 44.3661},
    "İran": {"tr": "İran", "en": "Iran", "lat": 35.6892, "lon": 51.3890},
    "İrlanda": {"tr": "İrlanda", "en": "Ireland", "lat": 53.3498, "lon": -6.2603},
    "İspanya": {"tr": "İspanya", "en": "Spain", "lat": 40.4168, "lon": -3.7038},
    "İsrail": {"tr": "İsrail", "en": "Israel", "lat": 31.7683, "lon": 35.2137},
    "İsveç": {"tr": "İsveç", "en": "Sweden", "lat": 59.3293, "lon": 18.0686},
    "İsviçre": {"tr": "İsviçre", "en": "Switzerland", "lat": 46.9480, "lon": 7.4474},
    "İtalya": {"tr": "İtalya", "en": "Italy", "lat": 41.9028, "lon": 12.4964},
    "İzlanda": {"tr": "İzlanda", "en": "Iceland", "lat": 64.1466, "lon": -21.9426},
    "Jamaika": {"tr": "Jamaika", "en": "Jamaica", "lat": 18.0179, "lon": -76.8099},
    "Japonya": {"tr": "Japonya", "en": "Japan", "lat": 35.6762, "lon": 139.6503},
    "Kamboçya": {"tr": "Kamboçya", "en": "Cambodia", "lat": 11.5564, "lon": 104.9282},
    "Kamerun": {"tr": "Kamerun", "en": "Cameroon", "lat": 3.8480, "lon": 11.5021},
    "Kanada": {"tr": "Kanada", "en": "Canada", "lat": 45.4215, "lon": -75.6972},
    "Karadağ": {"tr": "Karadağ", "en": "Montenegro", "lat": 42.4304, "lon": 19.2594},
    "Katar": {"tr": "Katar", "en": "Qatar", "lat": 25.2854, "lon": 51.5310},
    "Kazakistan": {"tr": "Kazakistan", "en": "Kazakhstan", "lat": 51.1694, "lon": 71.4491},
    "Kenya": {"tr": "Kenya", "en": "Kenya", "lat": -1.2921, "lon": 36.8219},
    "Kıbrıs": {"tr": "Kıbrıs", "en": "Cyprus", "lat": 35.1856, "lon": 33.3823},
    "Kırgızistan": {"tr": "Kırgızistan", "en": "Kyrgyzstan", "lat": 42.8746, "lon": 74.5698},
    "Kiribati": {"tr": "Kiribati", "en": "Kiribati", "lat": 1.4518, "lon": 172.9717},
    "Kolombiya": {"tr": "Kolombiya", "en": "Colombia", "lat": 4.7110, "lon": -74.0721},
    "Komorlar": {"tr": "Komorlar", "en": "Comoros", "lat": -11.7172, "lon": 43.2473},
    "Kongo Cumhuriyeti": {"tr": "Kongo Cumhuriyeti", "en": "Republic of the Congo", "lat": -4.2634, "lon": 15.2429},
    "Kongo Demokratik Cumhuriyeti": {"tr": "Kongo Demokratik Cumhuriyeti", "en": "Democratic Republic of the Congo", "lat": -4.4419, "lon": 15.2663},
    "Kosta Rika": {"tr": "Kosta Rika", "en": "Costa Rica", "lat": 9.9281, "lon": -84.0907},
    "Kuveyt": {"tr": "Kuveyt", "en": "Kuwait", "lat": 29.3759, "lon": 47.9774},
    "Kuzey Kıbrıs Türk Cumhuriyeti": {"tr": "Kuzey Kıbrıs Türk Cumhuriyeti", "en": "Northern Cyprus", "lat": 35.1856, "lon": 33.3823},
    "Kuzey Kore": {"tr": "Kuzey Kore", "en": "North Korea", "lat": 39.0392, "lon": 125.7625},
    "Kuzey Makedonya": {"tr": "Kuzey Makedonya", "en": "North Macedonia", "lat": 41.9973, "lon": 21.4280},
    "Küba": {"tr": "Küba", "en": "Cuba", "lat": 23.1136, "lon": -82.3666},
    "Laos": {"tr": "Laos", "en": "Laos", "lat": 17.9757, "lon": 102.6331},
    "Lesotho": {"tr": "Lesotho", "en": "Lesotho", "lat": -29.3100, "lon": 27.4782},
    "Letonya": {"tr": "Letonya", "en": "Latvia", "lat": 56.9496, "lon": 24.1052},
    "Liberya": {"tr": "Liberya", "en": "Liberia", "lat": 6.2907, "lon": -10.7605},
    "Libya": {"tr": "Libya", "en": "Libya", "lat": 32.8872, "lon": 13.1913},
    "Lihtenştayn": {"tr": "Lihtenştayn", "en": "Liechtenstein", "lat": 47.1410, "lon": 9.5209},
    "Litvanya": {"tr": "Litvanya", "en": "Lithuania", "lat": 54.6872, "lon": 25.2797},
    "Lübnan": {"tr": "Lübnan", "en": "Lebanon", "lat": 33.8938, "lon": 35.5018},
    "Lüksemburg": {"tr": "Lüksemburg", "en": "Luxembourg", "lat": 49.6116, "lon": 6.1319},
    "Macaristan": {"tr": "Macaristan", "en": "Hungary", "lat": 47.4979, "lon": 19.0402},
    "Madagaskar": {"tr": "Madagaskar", "en": "Madagascar", "lat": -18.8792, "lon": 47.5079},
    "Malavi": {"tr": "Malavi", "en": "Malawi", "lat": -13.9626, "lon": 33.7741},
    "Maldivler": {"tr": "Maldivler", "en": "Maldives", "lat": 4.1755, "lon": 73.5093},
    "Malezya": {"tr": "Malezya", "en": "Malaysia", "lat": 3.1390, "lon": 101.6869},
    "Mali": {"tr": "Mali", "en": "Mali", "lat": 12.6392, "lon": -8.0029},
    "Malta": {"tr": "Malta", "en": "Malta", "lat": 35.8989, "lon": 14.5146},
    "Marshall Adaları": {"tr": "Marshall Adaları", "en": "Marshall Islands", "lat": 7.1130, "lon": 171.1850},
    "Mauritius": {"tr": "Mauritius", "en": "Mauritius", "lat": -20.1609, "lon": 57.5012},
    "Meksika": {"tr": "Meksika", "en": "Mexico", "lat": 19.4326, "lon": -99.1332},
    "Mısır": {"tr": "Mısır", "en": "Egypt", "lat": 30.0444, "lon": 31.2357},
    "Mikronezya": {"tr": "Mikronezya", "en": "Micronesia", "lat": 6.9147, "lon": 158.1610},
    "Moğolistan": {"tr": "Moğolistan", "en": "Mongolia", "lat": 47.8864, "lon": 106.9057},
    "Moldova": {"tr": "Moldova", "en": "Moldova", "lat": 47.0105, "lon": 28.8638},
    "Monako": {"tr": "Monako", "en": "Monaco", "lat": 43.7384, "lon": 7.4246},
    "Moritanya": {"tr": "Moritanya", "en": "Mauritania", "lat": 18.0735, "lon": -15.9582},
    "Mozambik": {"tr": "Mozambik", "en": "Mozambique", "lat": -25.9692, "lon": 32.5732},
    "Myanmar": {"tr": "Myanmar", "en": "Myanmar", "lat": 19.7633, "lon": 96.0785},
    "Namibya": {"tr": "Namibya", "en": "Namibia", "lat": -22.5609, "lon": 17.0658},
    "Nauru": {"tr": "Nauru", "en": "Nauru", "lat": -0.5477, "lon": 166.9209},
    "Nepal": {"tr": "Nepal", "en": "Nepal", "lat": 27.7172, "lon": 85.3240},
    "Nijer": {"tr": "Nijer", "en": "Niger", "lat": 13.5116, "lon": 2.1254},
    "Nijerya": {"tr": "Nijerya", "en": "Nigeria", "lat": 9.0765, "lon": 7.3986},
    "Nikaragua": {"tr": "Nikaragua", "en": "Nicaragua", "lat": 12.1150, "lon": -86.2362},
    "Norveç": {"tr": "Norveç", "en": "Norway", "lat": 59.9139, "lon": 10.7522},
    "Orta Afrika Cumhuriyeti": {"tr": "Orta Afrika Cumhuriyeti", "en": "Central African Republic", "lat": 4.3947, "lon": 18.5582},
    "Özbekistan": {"tr": "Özbekistan", "en": "Uzbekistan", "lat": 41.2995, "lon": 69.2401},
    "Pakistan": {"tr": "Pakistan", "en": "Pakistan", "lat": 33.6844, "lon": 73.0479},
    "Palau": {"tr": "Palau", "en": "Palau", "lat": 7.5006, "lon": 134.6243},
    "Panama": {"tr": "Panama", "en": "Panama", "lat": 8.9824, "lon": -79.5199},
    "Papua Yeni Gine": {"tr": "Papua Yeni Gine", "en": "Papua New Guinea", "lat": -9.4438, "lon": 147.1803},
    "Paraguay": {"tr": "Paraguay", "en": "Paraguay", "lat": -25.2637, "lon": -57.5759},
    "Peru": {"tr": "Peru", "en": "Peru", "lat": -12.0464, "lon": -77.0428},
    "Polonya": {"tr": "Polonya", "en": "Poland", "lat": 52.2297, "lon": 21.0122},
    "Portekiz": {"tr": "Portekiz", "en": "Portugal", "lat": 38.7223, "lon": -9.1393},
    "Romanya": {"tr": "Romanya", "en": "Romania", "lat": 44.4268, "lon": 26.1025},
    "Ruanda": {"tr": "Ruanda", "en": "Rwanda", "lat": -1.9441, "lon": 30.0619},
    "Rusya": {"tr": "Rusya", "en": "Russia", "lat": 55.7558, "lon": 37.6173},
    "Saint Kitts ve Nevis": {"tr": "Saint Kitts ve Nevis", "en": "Saint Kitts and Nevis", "lat": 17.3026, "lon": -62.7177},
    "Saint Lucia": {"tr": "Saint Lucia", "en": "Saint Lucia", "lat": 14.0101, "lon": -60.9875},
    "Saint Vincent ve Grenadinler": {"tr": "Saint Vincent ve Grenadinler", "en": "Saint Vincent and the Grenadines", "lat": 13.1600, "lon": -61.2248},
    "Samoa": {"tr": "Samoa", "en": "Samoa", "lat": -13.8507, "lon": -171.7514},
    "San Marino": {"tr": "San Marino", "en": "San Marino", "lat": 43.9424, "lon": 12.4578},
    "São Tomé ve Príncipe": {"tr": "São Tomé ve Príncipe", "en": "São Tomé and Príncipe", "lat": 0.3365, "lon": 6.7273},
    "Senegal": {"tr": "Senegal", "en": "Senegal", "lat": 14.7167, "lon": -17.4677},
    "Seyşeller": {"tr": "Seyşeller", "en": "Seychelles", "lat": -4.6191, "lon": 55.4513},
    "Sırbistan": {"tr": "Sırbistan", "en": "Serbia", "lat": 44.7866, "lon": 20.4489},
    "Sierra Leone": {"tr": "Sierra Leone", "en": "Sierra Leone", "lat": 8.4657, "lon": -13.2317},
    "Singapur": {"tr": "Singapur", "en": "Singapore", "lat": 1.3521, "lon": 103.8198},
    "Slovakya": {"tr": "Slovakya", "en": "Slovakia", "lat": 48.1486, "lon": 17.1077},
    "Slovenya": {"tr": "Slovenya", "en": "Slovenia", "lat": 46.0569, "lon": 14.5058},
    "Solomon Adaları": {"tr": "Solomon Adaları", "en": "Solomon Islands", "lat": -9.4456, "lon": 159.9729},
    "Somali": {"tr": "Somali", "en": "Somalia", "lat": 2.0469, "lon": 45.3182},
    "Sri Lanka": {"tr": "Sri Lanka", "en": "Sri Lanka", "lat": 6.9271, "lon": 79.8612},
    "Sudan": {"tr": "Sudan", "en": "Sudan", "lat": 15.5007, "lon": 32.5599},
    "Surinam": {"tr": "Surinam", "en": "Suriname", "lat": 5.8520, "lon": -55.2038},
    "Suriye": {"tr": "Suriye", "en": "Syria", "lat": 33.5138, "lon": 36.2765},
    "Suudi Arabistan": {"tr": "Suudi Arabistan", "en": "Saudi Arabia", "lat": 24.7136, "lon": 46.6753},
    "Şili": {"tr": "Şili", "en": "Chile", "lat": -33.4489, "lon": -70.6693},
    "Tacikistan": {"tr": "Tacikistan", "en": "Tajikistan", "lat": 38.5598, "lon": 68.7870},
    "Tanzanya": {"tr": "Tanzanya", "en": "Tanzania", "lat": -6.7924, "lon": 39.2083},
    "Tayland": {"tr": "Tayland", "en": "Thailand", "lat": 13.7563, "lon": 100.5018},
    "Togo": {"tr": "Togo", "en": "Togo", "lat": 6.1319, "lon": 1.2228},
    "Tonga": {"tr": "Tonga", "en": "Tonga", "lat": -21.2114, "lon": -175.1398},
    "Trinidad ve Tobago": {"tr": "Trinidad ve Tobago", "en": "Trinidad and Tobago", "lat": 10.6549, "lon": -61.5019},
    "Tunus": {"tr": "Tunus", "en": "Tunisia", "lat": 36.8065, "lon": 10.1815},
    "Tuvalu": {"tr": "Tuvalu", "en": "Tuvalu", "lat": -8.5211, "lon": 179.1962},
    "Türkiye": {"tr": "Türkiye", "en": "Türkiye", "lat": 39.9334, "lon": 32.8597},
    "Türkmenistan": {"tr": "Türkmenistan", "en": "Turkmenistan", "lat": 37.9601, "lon": 58.3261},
    "Uganda": {"tr": "Uganda", "en": "Uganda", "lat": 0.3476, "lon": 32.5825},
    "Ukrayna": {"tr": "Ukrayna", "en": "Ukraine", "lat": 50.4501, "lon": 30.5234},
    "Umman": {"tr": "Umman", "en": "Oman", "lat": 23.5880, "lon": 58.3829},
    "Uruguay": {"tr": "Uruguay", "en": "Uruguay", "lat": -34.9011, "lon": -56.1645},
    "Ürdün": {"tr": "Ürdün", "en": "Jordan", "lat": 31.9454, "lon": 35.9284},
    "Vanuatu": {"tr": "Vanuatu", "en": "Vanuatu", "lat": -17.7333, "lon": 168.3273},
    "Vatikan": {"tr": "Vatikan", "en": "Vatican City", "lat": 41.9029, "lon": 12.4534},
    "Venezuela": {"tr": "Venezuela", "en": "Venezuela", "lat": 10.4806, "lon": -66.9036},
    "Vietnam": {"tr": "Vietnam", "en": "Vietnam", "lat": 21.0285, "lon": 105.8542},
    "Yemen": {"tr": "Yemen", "en": "Yemen", "lat": 15.3694, "lon": 44.1910},
    "Yeni Zelanda": {"tr": "Yeni Zelanda", "en": "New Zealand", "lat": -41.2865, "lon": 174.7762},
    "Yeşil Burun": {"tr": "Yeşil Burun", "en": "Cabo Verde", "lat": 14.9330, "lon": -23.5133},
    "Zambiya": {"tr": "Zambiya", "en": "Zambia", "lat": -15.3875, "lon": 28.3228},
    "Zimbabve": {"tr": "Zimbabve", "en": "Zimbabwe", "lat": -17.8252, "lon": 31.0335},
}

SEHIR_ADLARI = {
    "Mekke (Suudi Arabistan)": {"tr": "Mekke (Suudi Arabistan)", "en": "Makkah (Saudi Arabia)"},
    "Medine (Suudi Arabistan)": {"tr": "Medine (Suudi Arabistan)", "en": "Madinah (Saudi Arabia)"},
    **{k: {"tr": v["tr"], "en": v["en"]} for k, v in DUNYA_ULKELERI.items()},
}

SEHIR_KOORDINATLARI = {
    "Mekke (Suudi Arabistan)": {"lat": 21.3891, "lon": 39.8579},
    "Medine (Suudi Arabistan)": {"lat": 24.5247, "lon": 39.5692},
    # Türkiye 81 İl
    "Adana": {"lat": 37.0, "lon": 35.3213},
    "Adıyaman": {"lat": 37.7648, "lon": 38.2786},
    "Afyonkarahisar": {"lat": 38.7507, "lon": 30.5567},
    "Ağrı": {"lat": 39.7191, "lon": 43.0503},
    "Aksaray": {"lat": 38.3687, "lon": 34.037},
    "Amasya": {"lat": 40.654, "lon": 35.8359},
    "Ankara": {"lat": 39.9334, "lon": 32.8597},
    "Antalya": {"lat": 36.8969, "lon": 30.7133},
    "Ardahan": {"lat": 41.1105, "lon": 42.7022},
    "Artvin": {"lat": 41.1828, "lon": 41.8183},
    "Aydın": {"lat": 37.8444, "lon": 27.8458},
    "Balıkesir": {"lat": 39.6484, "lon": 27.8826},
    "Bartın": {"lat": 41.6344, "lon": 32.3375},
    "Batman": {"lat": 37.8812, "lon": 41.1351},
    "Bayburt": {"lat": 40.2552, "lon": 40.2249},
    "Bilecik": {"lat": 40.0567, "lon": 29.9797},
    "Bingöl": {"lat": 38.8854, "lon": 40.498},
    "Bitlis": {"lat": 38.4006, "lon": 42.1095},
    "Bolu": {"lat": 40.735, "lon": 31.6061},
    "Burdur": {"lat": 37.7246, "lon": 30.2887},
    "Bursa": {"lat": 40.1828, "lon": 29.0665},
    "Çanakkale": {"lat": 40.1553, "lon": 26.4142},
    "Çankırı": {"lat": 40.6013, "lon": 33.6134},
    "Çorum": {"lat": 40.5506, "lon": 34.9556},
    "Denizli": {"lat": 37.7765, "lon": 29.0864},
    "Diyarbakır": {"lat": 37.9144, "lon": 40.2306},
    "Düzce": {"lat": 40.8438, "lon": 31.1565},
    "Edirne": {"lat": 41.6771, "lon": 26.5557},
    "Elazığ": {"lat": 38.681, "lon": 39.2264},
    "Erzincan": {"lat": 39.75, "lon": 39.5},
    "Erzurum": {"lat": 39.9, "lon": 41.27},
    "Eskişehir": {"lat": 39.7767, "lon": 30.5206},
    "Gaziantep": {"lat": 37.0662, "lon": 37.3833},
    "Giresun": {"lat": 40.9128, "lon": 38.3895},
    "Gümüşhane": {"lat": 40.46, "lon": 39.48},
    "Hakkari": {"lat": 37.5833, "lon": 43.7333},
    "Hatay": {"lat": 36.2, "lon": 36.16},
    "Iğdır": {"lat": 39.9167, "lon": 44.0333},
    "Isparta": {"lat": 37.7648, "lon": 30.5566},
    "İstanbul": {"lat": 41.0082, "lon": 28.9784},
    "İzmir": {"lat": 38.4192, "lon": 27.1287},
    "Kahramanmaraş": {"lat": 37.5858, "lon": 36.9371},
    "Karabük": {"lat": 41.2, "lon": 32.62},
    "Karaman": {"lat": 37.1759, "lon": 33.2287},
    "Kars": {"lat": 40.6, "lon": 43.1},
    "Kastamonu": {"lat": 41.3887, "lon": 33.7827},
    "Kayseri": {"lat": 38.7312, "lon": 35.4787},
    "Kilis": {"lat": 36.7184, "lon": 37.1212},
    "Kırıkkale": {"lat": 39.8468, "lon": 33.5153},
    "Kırklareli": {"lat": 41.7333, "lon": 27.2167},
    "Kırşehir": {"lat": 39.1425, "lon": 34.1709},
    "Kocaeli": {"lat": 40.7654, "lon": 29.9408},
    "Konya": {"lat": 37.8667, "lon": 32.4833},
    "Kütahya": {"lat": 39.4167, "lon": 29.9833},
    "Malatya": {"lat": 38.3552, "lon": 38.3095},
    "Manisa": {"lat": 38.6191, "lon": 27.4289},
    "Mardin": {"lat": 37.3211, "lon": 40.7245},
    "Mersin": {"lat": 36.8, "lon": 34.6333},
    "Muğla": {"lat": 37.2153, "lon": 28.3636},
    "Muş": {"lat": 38.9462, "lon": 41.4913},
    "Nevşehir": {"lat": 38.6939, "lon": 34.7145},
    "Niğde": {"lat": 37.9667, "lon": 34.6833},
    "Ordu": {"lat": 40.9839, "lon": 37.8764},
    "Osmaniye": {"lat": 37.0742, "lon": 36.2478},
    "Rize": {"lat": 41.0201, "lon": 40.5234},
    "Sakarya": {"lat": 40.7569, "lon": 30.3783},
    "Samsun": {"lat": 41.2867, "lon": 36.33},
    "Siirt": {"lat": 37.9333, "lon": 41.95},
    "Sinop": {"lat": 42.0231, "lon": 35.1531},
    "Sivas": {"lat": 39.7477, "lon": 37.0179},
    "Şanlıurfa": {"lat": 37.1591, "lon": 38.7969},
    "Şırnak": {"lat": 37.5192, "lon": 42.4589},
    "Tekirdağ": {"lat": 40.9833, "lon": 27.5167},
    "Tokat": {"lat": 40.3167, "lon": 36.55},
    "Trabzon": {"lat": 41.0015, "lon": 39.7178},
    "Tunceli": {"lat": 39.3074, "lon": 39.5467},
    "Uşak": {"lat": 38.6823, "lon": 29.4082},
    "Van": {"lat": 38.4891, "lon": 43.4089},
    "Yalova": {"lat": 40.65, "lon": 29.2667},
    "Yozgat": {"lat": 39.8181, "lon": 34.8147},
    "Zonguldak": {"lat": 41.4564, "lon": 31.7987},
    # Tüm Dünya Ülkeleri
    **{
        k: {"lat": v["lat"], "lon": v["lon"]}
        for k, v in DUNYA_ULKELERI.items()
    },
}

# --- EN ÖNEMLİ ZİKİRLER LİSTESİ (DOĞRU YAZILIŞLARIYLA) ---
ZIKIR_LISTESI = [
    "Allah",
    "Allahümme salli ala seyyidina Muhammedin ve ala ali seyyidina Muhammed (Salavat-ı Şerife)",
    "La ilahe illallah",
    "Sübhanallahi ve bihamdihi, Sübhanallahil azim",
    "Estağfirullah el-azim ve etübü ileyh",
    "La havle vela kuvvete illa billahil aliyyil azim",
    "Hasbiyallahu ve ni'mel vekil",
    "Sübhanallahi vel hamdülillahi ve la ilahe illallahu vallahu ekber",
    "La ilahe illa ente sübhaneke inni kuntu minez zalimin (Hz. Yunus Duası)",
    "Seyyidü'l-İstiğfar (Allahümme ente rabbi la ilahe illa ente...)",
    "Elhamdülillah",
    "Allahu Ekber",
]


def sehir_etiketi(sehir_key, dil):
    if sehir_key in SEHIR_ADLARI:
        return SEHIR_ADLARI[sehir_key].get(dil, sehir_key)
    return sehir_key


def _tek_parcayi_ingilizceye_cevir(parca):
    if not parca.strip():
        return parca
    try:
        query = urlencode({"q": parca, "langpair": "tr|en"})
        url = f"https://api.mymemory.translated.net/get?{query}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=6) as resp:
            veri = json.loads(resp.read().decode("utf-8"))
        ceviri = veri.get("responseData", {}).get("translatedText")
        if ceviri and ceviri.strip() and "MYMEMORY WARNING" not in ceviri.upper():
            return ceviri.strip()
    except Exception:
        pass
    return parca


@st.cache_data(show_spinner=False)
def metni_ingilizceye_cevir(metin):
    if not metin or not metin.strip():
        return metin

    satirlar = metin.split("\n")
    cevrilen_satirlar = []
    blok = []
    blok_uzunluk = 0

    def blok_bosalt():
        nonlocal blok, blok_uzunluk
        if not blok:
            return
        birlesik = "\n".join(blok)
        if len(birlesik) <= 450:
            cevrilen_satirlar.append(_tek_parcayi_ingilizceye_cevir(birlesik))
        else:
            for s in blok:
                cevrilen_satirlar.append(_tek_parcayi_ingilizceye_cevir(s))
        blok = []
        blok_uzunluk = 0

    for satir in satirlar:
        ek_uzunluk = len(satir) + (1 if blok else 0)
        if blok and blok_uzunluk + ek_uzunluk > 450:
            blok_bosalt()
        blok.append(satir)
        blok_uzunluk += ek_uzunluk

    blok_bosalt()
    return "\n".join(cevrilen_satirlar)


# --- 1. VERİTABANI BAĞLANTISI VE KURULUMU ---
def init_db():
    conn = sqlite3.connect("global_zikir.db", check_same_thread=False)
    c = conn.cursor()

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
    c.execute(
        "SELECT secilen_zikir, toplam_zikir, hedef_adet FROM zikir_portal WHERE id = 1"
    )
    return c.fetchone()


def veri_guncelle(secilen_zikir, toplam_zikir, hedef_adet):
    c.execute(
        """
        UPDATE zikir_portal
        SET secilen_zikir = ?, toplam_zikir = ?, hedef_adet = ?
        WHERE id = 1
        """,
        (secilen_zikir, toplam_zikir, hedef_adet),
    )
    conn.commit()


def katilim_ekle(kullanici_adi, sehir, adet, zikir_adi):
    simdi = datetime.now()
    zaman = simdi.strftime("%H:%M:%S")
    gun = simdi.strftime("%Y-%m-%d")
    c.execute(
        """
        INSERT INTO katilimlar (kullanici_adi, sehir, adet, tarih, zikir_adi, gun)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (kullanici_adi or "Misafir", sehir, adet, zaman, zikir_adi, gun),
    )
    conn.commit()


def gunluk_zikir_ozeti(gun_str, varsayilan_zikir):
    c.execute(
        """
        SELECT COALESCE(NULLIF(zikir_adi, ''), ?), COALESCE(SUM(adet), 0) AS adet
        FROM katilimlar
        WHERE COALESCE(gun, ?) = ?
        GROUP BY COALESCE(NULLIF(zikir_adi, ''), ?)
        ORDER BY adet DESC, 1 ASC
        """,
        (varsayilan_zikir, gun_str, gun_str, varsayilan_zikir),
    )
    return c.fetchall()


def yazar_notu_cek():
    c.execute(
        "SELECT baslik, icerik, guncellenme FROM misafir_yazar_notu WHERE id = 1"
    )
    row = c.fetchone()
    return row if row else ("", "", "")


def yazar_notu_kaydet(baslik, icerik, gecmise_ekle=True):
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temiz_baslik = baslik.strip()
    temiz_icerik = icerik.strip()
    c.execute(
        """
        UPDATE misafir_yazar_notu
        SET baslik = ?, icerik = ?, guncellenme = ?
        WHERE id = 1
        """,
        (temiz_baslik, temiz_icerik, zaman),
    )
    if gecmise_ekle and temiz_icerik:
        c.execute(
            """
            INSERT INTO misafir_yazar_gecmisi (baslik, icerik, tarih)
            VALUES (?, ?, ?)
            """,
            (temiz_baslik, temiz_icerik, zaman),
        )
    conn.commit()


def yazar_gecmisi_cek(limit=20):
    c.execute(
        """
        SELECT id, baslik, icerik, tarih
        FROM misafir_yazar_gecmisi
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return c.fetchall()


def yazar_gecmisi_temizle():
    c.execute("DELETE FROM misafir_yazar_gecmisi")
    conn.commit()


# Güncel veriyi veritabanından al
aktif_zikir, toplam_zikir, hedef_adet = veri_cek()
yazar_baslik, yazar_icerik, yazar_guncellenme = yazar_notu_cek()
yazar_gecmisi = yazar_gecmisi_cek()

if "dil" not in st.session_state:
    st.session_state.dil = "tr"
if "kullanici_sayac" not in st.session_state:
    st.session_state.kullanici_sayac = 0
if "yonetici_yetkisi" not in st.session_state:
    st.session_state.yonetici_yetkisi = False
if "yazar_yetkisi" not in st.session_state:
    st.session_state.yazar_yetkisi = False
if "baloncuk_goster" not in st.session_state:
    st.session_state.baloncuk_goster = False

# --- 2. KENAR ÇUBUĞU: DİL, KULLANICI & YÖNETİCİ PANELİ ---
dil_secimi = st.sidebar.selectbox(
    METINLER[st.session_state.dil]["lang_label"],
    options=["tr", "en"],
    index=0 if st.session_state.dil == "tr" else 1,
    format_func=lambda x: "Türkçe" if x == "tr" else "English",
)
if dil_secimi != st.session_state.dil:
    st.session_state.dil = dil_secimi
    st.rerun()

t = METINLER[st.session_state.dil]
dil = st.session_state.dil

st.sidebar.header(t["participant_header"])
kullanici_adi = st.sidebar.text_input(t["name_label"], value=t["default_name"])
misafir_yazar_aktif = st.sidebar.checkbox(
    t["guest_writer_mode"],
    value=(
        st.session_state.yazar_yetkisi
        or (kullanici_adi.strip().lower() in ["misafir yazar", "guest writer"])
    ),
    help=t["guest_writer_hint"],
)
if not misafir_yazar_aktif and st.session_state.yazar_yetkisi:
    st.session_state.yazar_yetkisi = False

diger_sehirler = sorted(
    [s for s in SEHIR_KOORDINATLARI.keys() if s not in KUTSAL_MERKEZLER],
    key=lambda s: sehir_etiketi(s, dil),
)
sehir_listesi = KUTSAL_MERKEZLER + diger_sehirler

secilen_sehir = st.sidebar.selectbox(
    t["city_label"],
    sehir_listesi,
    index=sehir_listesi.index("Mekke (Suudi Arabistan)"),
    format_func=lambda s: sehir_etiketi(s, dil),
)

st.sidebar.divider()
st.sidebar.header(t["admin_header"])

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

    mevcut_index = (
        ZIKIR_LISTESI.index(aktif_zikir) if aktif_zikir in ZIKIR_LISTESI else 0
    )
    secim = st.sidebar.selectbox(
        t["select_dhikr_admin"], ZIKIR_LISTESI, index=mevcut_index
    )

    if secim != aktif_zikir:
        veri_guncelle(secim, toplam_zikir, hedef_adet)
        st.rerun()

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
        c.execute("DELETE FROM katilimlar")
        conn.commit()
        st.sidebar.success(t["pool_reset_msg"])
        st.rerun()

    if st.sidebar.button(t["logout_btn"], use_container_width=True):
        st.session_state.yonetici_yetkisi = False
        st.rerun()

# Kenar çubuğuna bilgi notu ve uyku modu yönlendirmesi
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

st.markdown(t["active_dhikr_heading"])
st.markdown(
    f"""
    <div style="background-color:#fff8e7; border:3px solid #111111; border-radius:12px; padding:18px 20px; text-align:center; margin-top:8px; margin-bottom:16px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
        <div style="color:#000000; font-size:28px; font-weight:900; text-transform:uppercase; letter-spacing:0.6px; line-height:1.35;">
            {aktif_zikir}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

ilerleme_orani = min(1.0, toplam_zikir / hedef_adet) if hedef_adet > 0 else 0

col1, col2 = st.columns(2)
with col1:
    st.metric(
        label=f"{t['your_contribution']} ({kullanici_adi})",
        value=f"{st.session_state.kullanici_sayac} {t['unit_count']}",
    )
with col2:
    st.metric(
        label=t["global_pool"], value=f"{toplam_zikir:,} / {hedef_adet:,}"
    )

st.progress(ilerleme_orani)
st.write("")

# --- 4. ZİKİR ÇEKME BUTONU ---
col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    if st.button(
        t["pull_btn"], use_container_width=True, type="primary"
    ):
        st.session_state.kullanici_sayac += 1
        yeni_toplam = toplam_zikir + 1

        if hedef_adet > 0 and toplam_zikir < hedef_adet <= yeni_toplam:
            st.session_state.baloncuk_goster = True

        veri_guncelle(aktif_zikir, yeni_toplam, hedef_adet)
        katilim_ekle(kullanici_adi, secilen_sehir, 1, aktif_zikir)
        st.rerun()

with col_btn2:
    if st.button(t["reset_personal_btn"], use_container_width=True):
        st.session_state.kullanici_sayac = 0
        st.rerun()

# Hedefe Tam Ulaşıldığında Baloncuklar, Tamamlandığında Mesaj ve Kayar Yazı
if st.session_state.baloncuk_goster:
    st.balloons()
    st.session_state.baloncuk_goster = False

if toplam_zikir >= hedef_adet:
    st.success(t["goal_reached_msg"].format(hedef=hedef_adet))

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

st.divider()

# --- MİSAFİR YAZAR PAYLAŞIM, GÜNCELLEME VE TARİHÇE ALANI ---
st.subheader(t["writer_section_heading"])
st.markdown(t["writer_section_desc"])

if yazar_icerik:
    ham_baslik = yazar_baslik or t["writer_default_title"]
    if dil == "en":
        gosterilecek_baslik = metni_ingilizceye_cevir(ham_baslik)
        gosterilecek_icerik = metni_ingilizceye_cevir(yazar_icerik)
        ceviri_notu = f" • {t['writer_auto_translated']}"
    else:
        gosterilecek_baslik = ham_baslik
        gosterilecek_icerik = yazar_icerik
        ceviri_notu = ""

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
                {t["writer_updated_at"]}: {yazar_guncellenme} • {t["writer_char_count"]}: {len(gosterilecek_icerik)}{ceviri_notu}
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
                g_baslik_goster = (
                    metni_ingilizceye_cevir(g_baslik)
                    if (dil == "en" and g_baslik)
                    else (g_baslik or t["writer_default_title"])
                )
                g_icerik_goster = (
                    metni_ingilizceye_cevir(g_icerik) if dil == "en" else g_icerik
                )
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

# --- 5. GLOBAL HARİTA VE İL / ÜLKE BAZLI ZİKİR SAYILARI ---
st.subheader(t["map_heading"])
st.markdown(t["map_desc"])

c.execute("SELECT sehir, SUM(adet) FROM katilimlar GROUP BY sehir")
aktif_sehirler = c.fetchall()

if aktif_sehirler:
    harita_verisi = [
        {
            "lat": SEHIR_KOORDINATLARI[sehir]["lat"],
            "lon": SEHIR_KOORDINATLARI[sehir]["lon"],
            "adet": max(int(toplam_adet or 1), 1),
        }
        for sehir, toplam_adet in aktif_sehirler
        if sehir in SEHIR_KOORDINATLARI
    ]

    if harita_verisi:
        df_harita = pd.DataFrame(harita_verisi)
        st.map(df_harita, size="adet", zoom=1)
else:
    st.info(t["no_map_data"])

st.divider()

st.subheader(t["city_stats_heading"])
c.execute(
    "SELECT sehir, COALESCE(SUM(adet), 0) AS toplam_adet "
    "FROM katilimlar "
    "GROUP BY sehir "
    "ORDER BY toplam_adet DESC, sehir ASC"
)
sehir_kayitlari = c.fetchall()

if sehir_kayitlari:
    for sehir, sehir_adet in sehir_kayitlari:
        adet_formatli = f"{int(sehir_adet):,}".replace(",", ".")
        st.markdown(
            t["city_item"].format(
                sehir=sehir_etiketi(sehir, dil), adet=adet_formatli
            )
        )
else:
    st.write(t["no_city_data"])

st.divider()

# --- 6. YASAL KORUMA VE ALT BİLGİ ---
st.markdown(t["footer_html"], unsafe_allow_html=True)