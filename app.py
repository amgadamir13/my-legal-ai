import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. الهوية البصرية (تصميم عسكري استراتيجي) ---
st.set_page_config(page_title="Strategic War Room", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        background-color: #0f172a; /* لون داكن للتركيز */
    }
    .msg-box { padding: 20px; border-radius: 15px; margin-bottom: 15px; line-height: 1.8; border-right: 8px solid; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .user-style { background-color: #1e293b; border-color: #3b82f6; color: #f8fafc; }
    .legal-style { background-color: #064e3b; border-color: #10b981; color: #ecfdf5; }
    .psych-style { background-color: #4c1d95; border-color: #a855f7; color: #f5f3ff; }
    .street-style { background-color: #7f1d1d; border-color: #f43f5e; color: #fff1f2; }
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { border-radius: 12px; height: 3.5em; font-weight: bold; border: none; transition: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الذاكرة الاستراتيجية ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. مركز القيادة (القائمة الجانبية) ---
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("مفتاح Gemini السري:", type="password")
    st.divider()
    strategy = st.text_input("القيم الحاكمة:", "الحكمة والهدوء")
    st.divider()
    v_files = st.file_uploader("قبو حقائقي (Vault)", accept_multiple_files=True)
    o_files = st.file_uploader("ملفات الخصم (Opponent)", accept_multiple_files=True)
    if st.button("تصفير الذاكرة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ المحقق الاستراتيجي")
st.caption("نظام العقول الثلاثة: قانوني | نفسي | داهية")

# --- 4. عرض المحادثة ---
for chat in st.session_state.chat_history:
    style = chat.get("style", "user-style")
    label = chat.get("label", "👤 أنت")
    st.markdown(f'<div class="msg-box {style}"><b>{label}:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

# --- 5. محرك العقول المتعددة ---
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي هنا...", height=120)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ القانوني")
    with c2: btn_P = st.form_submit_button("🧠 النفسي")
    with c3: btn_S = st.form_submit_button("🧨 الداهية")

if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # تحويل الشخصية
        if btn_L: role, label, style = "مستشار قانوني خبير بالثغرات والتقادم", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل سلوكي وجنائي يحلل نقاط الضعف النفسية", "🧠 النفسي", "psych-style"
        else: role, label, style = "مفاوض استراتيجي بارع يبحث عن حلول داهية", "🧨 الداهية", "street-style"

        # قراءة ذكية وشاملة للملفات
        v_context, o_context, imgs = "", "", []

        def process_files(files):
            text, images = "", []
            for f in files:
                if f.type == "application/pdf":
                    with fitz.open(stream=f.read(), filetype="pdf") as doc:
                        for page in doc: text += page.get_text() + "\n"
                else:
                    img = Image.open(f).convert("RGB")
                    img.thumbnail((1000, 1000))
                    images.append(img)
            return text, images

        v_context, v_imgs = process_files(v_files if v_files else [])
        o_context, o_imgs = process_files(o_files if o_files else [])

        prompt = f"""
        تقمص دور: {role}.
        قيمنا الحاكمة: {strategy}.
        
        بيانات من 'قبو الحقائق': {v_context[:10000]}
        بيانات من 'ملفات الخصم': {o_context[:10000]}
        
        الموقف المطلوب تحليله: {user_query}
        
        المطلوب: تحليل استراتيجي عميق، كشف التناقضات، واقتراح خطة عمل فورية.
        """
        
        with st.spinner(f"جاري استدعاء {label}..."):
            response = model.generate_content([prompt] + v_imgs + o_imgs)
            st.session_state.chat_history.append({"role": "user", "content": user_query, "label": "👤 أنت", "style": "user-style"})
            st.session_state.chat_history.append({"role": "assistant", "content": response.text, "label": label, "style": style})
            st.rerun()
            
    except Exception as e:
        st.error(f"خطأ في الأنظمة: {e}")
