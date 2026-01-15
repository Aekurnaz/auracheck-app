import streamlit as st
import os
import json
import PIL.Image
from google import genai
from PIL import ImageDraw, ImageFont, ImageOps
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st
import os
import json
import PIL.Image
from google import genai
from PIL import ImageDraw, ImageFont, ImageOps
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="AuraCheck", 
    page_icon="💀", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- CSS (Tasarım) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 15px;
    }
    .stButton>button:hover {
        background-color: #FF0000;
        color: white;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS KAYIT (HATA GÖSTEREN VERSİYON) ---
def save_to_sheet(puan, yorum):
    try:
        # 1. Secrets Kontrolü
        if "gcp_service_account" not in st.secrets:
            st.error("🚨 HATA: Streamlit Secrets içinde [gcp_service_account] bölümü bulunamadı!")
            return False

        # 2. Bağlantı Kurma
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 3. Dosyayı Bulma
        # DİKKAT: Senin Google Sheet dosyanın adı tam olarak "AuraDB" olmalı.
        sheet_name = "AuraDB" 
        sheet = client.open(sheet_name).sheet1
        
        # 4. Veriyi Hazırlama
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 5. Kaydetme
        sheet.append_row([zaman, puan, yorum, "gemini-flash-latest"])
        
        # Başarılı olursa yeşil mesaj göster
        st.success(f"✅ Veri '{sheet_name}' tablosuna kaydedildi!")
        return True
        
    except gspread.SpreadsheetNotFound:
        st.error(f"🚨 HATA: Google Drive'ında '{sheet_name}' ad
# --- AYARLAR ---
st.set_page_config(page_title="AuraCheck", page_icon="💀", layout="centered", initial_sidebar_state="collapsed")

# CSS
st.markdown("""
<style>
    .stButton>button {width: 100%; background-color: #FF4B4B; color: white; font-weight: bold; padding: 15px;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS BAĞLANTISI ---
def save_to_sheet(puan, yorum):
    try:
        # Secrets'tan bilgileri al
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # Secrets objesini dict'e çevirip credentials oluşturuyoruz
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Tabloyu aç ("AuraDB" ismini senin sheet isminle aynı yap!)
        sheet = client.open("AuraDB").sheet1
        
        # Tarih ve saat
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Satır ekle
        sheet.append_row([zaman, puan, yorum, "gemini-flash-latest"])
        return True
    except Exception as e:
        print(f"Kayıt Hatası: {e}") # Kullanıcıya göstermeye gerek yok, loga basar
        return False

# --- GEMINI CLIENT ---
def get_gemini_client():
    if "GOOGLE_API_KEY" in st.secrets:
        return genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    return None

# --- ANALİZ MOTORU ---
def analyze_aura(image, client):
    prompt = """
    Sen acımasız bir 'Gen Z Aura Yargıcı'sın.
    1. -5000 ile +5000 arası Aura Puanı ver.
    2. Yorumun "Maksimum 12 kelimelik" TEK BİR VURUCU CÜMLE olsun.
    3. Yanıtı SADECE JSON ver: {"puan": 1200, "yorum": "..."}
    """
    try:
        response = client.models.generate_content(model="gemini-flash-latest", contents=[prompt, image])
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        return {"hata": str(e)}

# --- KART TASARIMI (Aynı Kalıyor) ---
def create_pro_card(user_img, score, roast_text):
    W, H = 1080, 1920
    card = PIL.Image.new('RGB', (W, H), color=(15, 15, 20))
    draw = ImageDraw.Draw(card)
    
    # Font (Varsayılan veya Montserrat)
    try:
        font_name = "Montserrat-ExtraBold.ttf"
        font_score = ImageFont.truetype(font_name, 180)
        font_roast = ImageFont.truetype(font_name, 70)
        font_small = ImageFont.truetype(font_name, 40)
    except:
        font_score = ImageFont.load_default()
        font_roast = ImageFont.load_default()
        font_small = ImageFont.load_default()

    score_val = int(score)
    color = (57, 255, 20) if score_val > 0 else (255, 49, 49)
    
    # Foto İşleme
    img_size = 800
    user_img = ImageOps.fit(user_img, (img_size, img_size), method=PIL.Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    img_with_border = ImageOps.expand(user_img, border=20, fill=color)
    card.paste(img_with_border, ((W - img_with_border.width) // 2, 400))

    # Yazılar
    def center_text(text, font, y, col):
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text(((W - (bbox[2] - bbox[0])) // 2, y), text, fill=col, font=font)

    center_text(f"{score_val:+d} AURA", font_score, 150, color)
    
    import textwrap
    lines = textwrap.wrap(roast_text, width=20)
    y = 1350
    for line in lines:
        center_text(line, font_roast, y, "white")
        y += 90
        
    center_text("auracheck.io | Powered by AI", font_small, H - 100, (150, 150, 150))
    return card

# --- ARAYÜZ ---
st.title("💀 AuraCheck")
st.write("Veri Analitiği Modu Aktif 📊")

tab1, tab2 = st.tabs(["📁 Dosya Yükle", "📸 Selfie Çek"])
img_file = tab1.file_uploader("Galeriden seç", type=["jpg", "png"]) or tab2.camera_input("Fotoğrafını Çek")

if img_file and st.button("🔥 AURAMI HESAPLA"):
    client = get_gemini_client()
    if client:
        img = PIL.Image.open(img_file)
        img = ImageOps.exif_transpose(img)
        st.image(img, width=200)
        
        with st.spinner('Analiz ediliyor ve veritabanına işleniyor...'):
            res = analyze_aura(img, client)
            
            if "hata" in res:
                st.error(res['hata'])
            else:
                puan = res.get("puan", 0)
                yorum = res.get("yorum", "...")
                
                # --- VERİYİ KAYDET ---
                save_to_sheet(puan, yorum)
                # ---------------------
                
                col1, col2 = st.columns(2)
                col1.metric("Aura Puanı", f"{puan:+d}")
                st.info(f"💀 {yorum}")
                
                try:
                    card = create_pro_card(img, puan, yorum)
                    st.image(card, caption="Story Kartın Hazır!", use_column_width=True)
                    
                    buf = io.BytesIO()
                    card.save(buf, format="PNG")
                    st.download_button("📥 KARTI İNDİR", buf.getvalue(), "aura_card.png", "image/png")
                except:
                    pass
    else:
        st.error("API Key Eksik!")