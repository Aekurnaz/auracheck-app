import streamlit as st
import os
import json
import PIL.Image
from google import genai
from PIL import ImageDraw, ImageFont, ImageOps

# API Key'i doğrudan yazmıyoruz! Streamlit Secrets'tan çekecek.
def get_gemini_client():
    try:
        # Streamlit Cloud'da veya localde secrets.toml dosyasından okur
        return genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except:
        st.error("API Key bulunamadı! Lütfen Secrets ayarlarını kontrol et.")
        return None

# Sayfa Ayarları
st.set_page_config(page_title="AuraCheck", page_icon="💀", layout="centered")


def analyze_aura(image, client):
    prompt = """
    Sen acımasız bir 'Gen Z Aura Yargıcı'sın.
    1. -5000 ile +5000 arası Aura Puanı ver.
    2. Yorumun "Maksimum 12 kelimelik" TEK BİR VURUCU CÜMLE olsun.
    3. Asla açıklama yapma. Yanıtı SADECE JSON ver: {"puan": 1200, "yorum": "..."}
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

# --- GELİŞMİŞ KART TASARIMI FONKSİYONU ---
def create_pro_card(user_img, score, roast_text):
    W, H = 1080, 1920
    
    # 1. Arka Plan (Koyu ve Şık)
    bg_color = (15, 15, 20) # Çok koyu lacivert-siyah
    card = PIL.Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(card)
    
    # 2. Fontları Yükle (Dosyanın yanında olmalı!)
    font_name = "Montserrat-ExtraBold.ttf"
    try:
        # Büyük puan için devasa font
        font_score = ImageFont.truetype(font_name, 180)
        # Yorum için orta boy font
        font_roast = ImageFont.truetype(font_name, 70)
        # Alt bilgi için küçük font
        font_small = ImageFont.truetype(font_name, 40)
    except:
        # Font dosyasını bulamazsa uyarı verip default kullanır (kötü görünür)
        print("UYARI: .ttf font dosyası bulunamadı! Varsayılan kullanılıyor.")
        font_score = ImageFont.load_default()
        font_roast = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 3. Puan Rengi Belirle (Neon Efekti)
    score_val = int(score)
    if score_val > 0:
        score_color = (57, 255, 20) # Neon Yeşil
        border_color = (57, 255, 20)
    else:
        score_color = (255, 49, 49) # Neon Kırmızı
        border_color = (255, 49, 49)

    # 4. Kullanıcı Fotosunu İşle (Kare yap, çerçeve ekle, ortala)
    # Fotoyu kare şeklinde kırp (center crop)
    img_size = 800
    user_img = ImageOps.fit(user_img, (img_size, img_size), method=PIL.Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    
    # Çerçeve ekle
    border_width = 20
    img_with_border = ImageOps.expand(user_img, border=border_width, fill=border_color)
    
    # Ortaya yerleştir
    img_x = (W - img_with_border.width) // 2
    img_y = 400
    card.paste(img_with_border, (img_x, img_y))

    # 5. Yazıları Yaz ve Ortala
    
    # --- Puan ---
    score_text = f"{score_val:+d} AURA" # Başına + veya - koyar
    # Yazının kapladığı alanı hesapla (bbox)
    bbox = draw.textbbox((0, 0), score_text, font=font_score)
    text_width = bbox[2] - bbox[0]
    text_x = (W - text_width) // 2
    draw.text((text_x, 150), score_text, fill=score_color, font=font_score)
    
    # --- Roast Yorumu (Satırlara bölme - Text Wrap) ---
    import textwrap
    lines = textwrap.wrap(roast_text, width=20) # Her satıra ~20 karakter
    
    current_y = img_y + img_size + border_width + 100 # Fotonun altından başla
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_roast)
        text_width = bbox[2] - bbox[0]
        text_x = (W - text_width) // 2
        draw.text((text_x, current_y), line, fill="white", font=font_roast)
        current_y += 90 # Satır aralığı

    # --- Footer ---
    footer_text = "auracheck.io | Powered by AI"
    bbox = draw.textbbox((0, 0), footer_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    text_x = (W - text_width) // 2
    draw.text((text_x, H - 100), footer_text, fill=(150, 150, 150), font=font_small)

    return card

# --- ARAYÜZ ---
st.title("💀 AuraCheck")
st.write("Fotoğrafını yükle, gerçekleri yüzüne vuralım.")

uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"])

if uploaded_file and st.button("🔥 ANALİZ ET"):
    with st.spinner('Gen Z Yargı Konseyi toplanıyor...'):
        client = get_gemini_client()
        img = PIL.Image.open(uploaded_file)
        
        # Analiz
        res = analyze_aura(img, client)
        
        if "hata" in res:
            st.error(f"HATA: {res['hata']}")
        else:
            puan = res.get("puan", 0)
            yorum = res.get("yorum", "...")
            
            # Metrikleri göster
            col1, col2 = st.columns(2)
            col1.metric("Aura Puanı", f"{puan:+d}")
            st.info(f"💬 {yorum}")
            
            # --- PRO KARTI OLUŞTUR ---
            try:
                # Eğer font dosyasını koymazsan burada konsolda uyarı verir
                card = create_pro_card(img, puan, yorum)
                
                st.write("---")
                st.header("✨ Instagram Story Kartın Hazır!")
                st.image(card, caption="Bunu indir ve Story'ne at!", width=400)
            except Exception as e:
                st.error(f"Kart oluşturulurken hata: {e}")