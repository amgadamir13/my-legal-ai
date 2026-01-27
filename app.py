import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. تصميم الهوية البصرية (High-End Professional) ---
st.set_page_config(page_title="المستشار القانوني Pro", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        background-color: #f8f9fa;
    }
    .msg-box { padding: 22px; border-radius: 20px; margin-bottom: 15px; line-height: 1.8; border: 1px solid #e2e8f0; }
    .user-style { background-color: #ffffff; border-right: 8px solid #1e3a8a; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
    .ai-style { background-color: #f0fdf4; border-right: 8px solid #10b981; }
    .detect-style { background-color: #fff1f2; border-right: 8px solid #e11d48; color: #9f1239; font-weight: 500; }
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { border-radius: 12px; height: 3.8em; background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: white; font-weight: bold; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة ذاكرة الجلسة ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. القائمة الجانبية (The Secure Vault) ---
with st.sidebar:
    st.title("🛡️ المحقق الاستراتيجي")
    api_key = st.text_input("مفتاح Gemini السري:", type="password", placeholder="AIza...")
    st.divider()
    
    st.subheader("📁 قبو حقائقك (Vault)")
    my_docs = st.file_uploader("ارفع أدلتك الموثوقة:", accept_multiple_files=True, key="vault")
    
    st.subheader("🚩 مستندات الخصم (Opponent)")
    opp_docs = st.file_uploader("ارفع أوراق الخصم لكشف التناقض:", accept_multiple_files=True, key="opponent")
    
    if st.button("تفريغ الذاكرة والملفات 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

# --- 4. عرض المحادثة الذكي ---
st.title("⚖️ المحقق القانوني Pro")
st.caption("نظام كشف التناقضات ومطابقة الأدلة الجنائية")

for chat in st.session_state.chat_history:
    # تمييز التناقضات باللون الأحمر فوراً
    content = chat["content"]
    is_alert = any(x in content for x in ["تناقض", "كذب", "مخالفة", "ثغرة", "غير مطابق"])
    style = "user-style" if chat["role"] == "user" else ("detect-style" if is_alert else "ai-style")
    
    label = "👤 أنت" if chat["role"] == "user" else "⚖️ المستشار"
    st.markdown(f'<div class="msg-box {style}"><b>{label}:</b><br>{content}</div>', unsafe_allow_html=True)

# --- 5. محرك الاستجواب المقابل (Forensic Engine) ---
with st.form("pro_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف أو اطلب كشف التناقضات بين الملفات:", height=120)
    analyze_btn = st.form_submit_button("إجراء التحليل الاستراتيجي 🔍")

if analyze_btn:
    if not api_key:
        st.error("⚠️ يرجى إدخال المفتاح في القائمة الجانبية.")
    elif user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        try:
            genai.configure(api_key=api_key)
            # اختيار أسرع وأحدث النماذج تلقائياً
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = next((m for m in ['models/gemini-2.0-flash', 'models/gemini-1.5-pro'] if m in available), 'models/gemini-1.5-flash')
            
            model = genai.GenerativeModel(target)
            
            vault_txt, opp_txt, images = "", "", []

            # معالجة قبو الحقائق (Vault)
            if my_docs:
                for f in my_docs:
                    if f.type == "application/pdf":
                        with fitz.open(stream=f.read(), filetype="pdf") as doc:
                            for p in doc: vault_txt += p.get_text() + "\n"
                    else:
                        img = Image.open(f).convert("RGB")
                        img.thumbnail((1200, 1200)) # دقة عالية للـ OCR
                        images.append(img)

            # معالجة مستندات الخصم (Opponent)
            if opp_docs:
                for f in opp_docs:
                    if f.type == "application/pdf":
                        with fitz.open(stream=f.read(), filetype="pdf") as doc:
                            for p in doc: opp_txt += p.get_text() + "\n"

            # برومبت "المدعي العام" الصارم
            prosecutor_prompt = f"""
            بصفتك 'مدعي عام خبير'، حلل التناقضات بين الحقائق والادعاءات.
            
            حقائقنا (Vault):
            {vault_txt[:15000]}
            
            ادعاءات الخصم (Opponent):
            {opp_txt[:15000]}
            
            المهمة:
            1. قارن بدقة: هل ما قاله الخصم يطابق مستنداتنا؟ ابحث عن تلاعب في التواريخ أو الأرقام.
            2. صحح المصطلحات المشوهة في الصور (مثال: 'احواف' تعني 'أطراف').
            3. حدد ثغرات قانونية يمكن استخدامها ضده.
            4. الرد بالعربية القانونية الفصحى وبشكل نقاط.
            
            سؤال المستخدم: {user_query}
            """
            
            with st.spinner("جاري مطابقة الأدلة وكشف الثغرات..."):
                response = model.generate_content([prosecutor_prompt] + images if images else [prosecutor_prompt])
                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                st.rerun()

        except Exception as e:
            st.error(f"تنبيه تقني: {str(e)}")
