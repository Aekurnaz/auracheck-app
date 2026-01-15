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

# --- GOOGLE SHEETS KAYIT (DÜZELTİLMİŞ VERSİYON) ---
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
        # HATA BURADAYDI: Satır çok uzun olduğu için böldük
        st.error(f"🚨 HATA: '{sheet_name}' adında dosya bulunamadı! "
                 "Lütfen Google Sheet adının 'AuraDB' olduğundan ve robotun 'Editör' olarak eklendiğinden emin ol.")
        return False
    except Exception as e:
        st.error(f"🚨 BEKLENMEYEN HATA: {e}")
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
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[prompt, image]
        )
        clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        return {"hata": str(e)}

# --- KART TASARIMI ---
def create_pro_card(user_img, score, roast_text):
    W, H = 1080, 1920
    bg_color = (15, 15, 20)
    card = PIL.Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(card)
    
    font_name = "Montserrat-ExtraBold.ttf"
    try:
        font_score = ImageFont.truetype(font_name, 180)
        font_roast = ImageFont.truetype(font_name, 70)
        font_small = ImageFont.truetype(font_name, 40)
    except:
        font_score = ImageFont.load_default()
        font_roast = ImageFont.load_default()
        font_small = ImageFont.load_default()

    score_val = int(score)
    if score_val > 0:
        score_color = (57, 255, 20)
        border_color = (57, 255, 20)
    else:
        score_color = (255, 49, 49)
        border_color = (255, 49, 49)

    img_size = 800
    user_img = ImageOps.fit(user_img, (img_size, img_size), method=PIL.Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    img_with_border = ImageOps.expand(user_img, border=20, fill=border_color)
    
    img_x = (W - img_with_border.width) // 2
    img_y = 400
    card.paste(img_with_border, (img_x, img_y))

    score_text = f"{score_val:+d} AURA"
    bbox = draw.textbbox((0, 0), score_text, font=font_score)
    text_width = bbox[2] - bbox[0]
    text_x = (W - text_width) // 2
    draw.text((text_x, 150), score_text, fill=score_color, font=font_score)
    
    import textwrap
    lines = textwrap.wrap(roast_text, width=20)
    current_y = img_y + img_size + 120
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_roast)
        text_width = bbox[2] - bbox[0]
        text_x = (W - text_width) // 2
        draw.text((text_x, current_y), line, fill="white", font=font_roast)
        current_y += 90

    footer_text = "auracheck.io | Powered by AI"
    bbox = draw.textbbox((0, 0), footer_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    text_x = (W - text_width) // 2
    draw.text((text_x, H - 100), footer_text, fill=(150, 150, 150), font=font_small)

    return card

# --- ARAYÜZ ---
st.title("💀 AuraCheck")
st.write("Veri Analitiği Modu Aktif 📊")

tab1, tab2 = st.tabs(["📁 Dosya Yükle", "📸 Selfie Çek"])
img_file = None

with tab1:
    uploaded_file = st.file_uploader("Galeriden seç", type=["jpg", "png", "jpeg"])
    if uploaded_file: img_file = uploaded_file
with tab2:
    camera_file = st.camera_input("Fotoğrafını Çek")
    if camera_file: img_file = camera_file

if img_file and st.button("🔥 AURAMI HESAPLA"):
    client = get_gemini_client()
    
    if not client:
        st.error("API Key bulunamadı! Secrets ayarlarını kontrol et.")
    else:
        img = PIL.Image.open(img_file)
        img = ImageOps.exif_transpose(img)
        st.image(img, width=200)
        
        with st.spinner('Analiz ediliyor...'):
            res = analyze_aura(img, client)
            
            if "hata" in res:
                st.error(res['hata'])
            else:
                puan = res.get("puan", 0)
                yorum = res.get("yorum", "...")
                
                # --- VERİYİ KAYDET ---
                save_to_sheet(puan, yorum)
                # ---------------------
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                col1.metric("Aura Puanı", f"{puan:+d}")
                st.info(f"💀 {yorum}")
                
                try:
                    card = create_pro_card(img, puan, yorum)
                    st.image(card, caption="Story Kartın Hazır!", use_column_width=True)
                    
                    buf = io.BytesIO()
                    card.save(buf, format="PNG")
                    st.download_button("📥 KARTI İNDİR", buf.getvalue(), "aura_card.png", "image/png")
                except Exception as e:
                    st.warning(f"Kart oluşturulamadı: {e}")