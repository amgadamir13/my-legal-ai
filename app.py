import streamlit as st
import os, fitz, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image

# 1. تنسيق الواجهة (أنيق ومنظم)
st.set_page_config(page_title="المستشار القانوني الذكي", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { direction: rtl; text-align: right; font-family: 'Cairo', sans-serif; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1e3a8a; color: white; }
    .success-box { padding: 10px; border-radius: 10px; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; margin-bottom: 20px; }
    .legal-box { background-color: #f8f9fa; padding: 25px; border-radius: 15px; border-right: 10px solid #1e3a8a; line-height: 1.8; color: #333; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model_engine = get_model()
DIR = "documents"

# --- الواجهة الجانبية للإعدادات (Sidebar) ---
with st.sidebar:
    st.header("🔐 إعدادات الوصول")
    # استخدام st.form لجعل المتصفح يحفظ المفتاح
    with st.form("api_key_form"):
        api_key_input = st.text_input("أدخل مفتاح Gemini هنا:", type="password", autocomplete="current-password")
        submit_key = st.form_submit_button("تأكيد وحفظ المفتاح")
    
    if submit_key and api_key_input:
        st.session_state['api_key'] = api_key_input
        st.markdown('<div class="success-box">✅ تم تأكيد المفتاح بنجاح!</div>', unsafe_allow_html=True)

# --- الواجهة الرئيسية ---
st.title("⚖️ المستشار القانوني الذكي")
st.write("خبير القانون المصري الاستراتيجي - يحلل المستندات ويقدم حلولاً داهية.")

# التأكد من وجود المفتاح قبل البدء
if 'api_key' not in st.session_state:
    st.warning("الرجاء إدخال المفتاح السري في القائمة الجانبية أولاً لتفعيل النظام.")
else:
    query = st.text_area("اشرح قضيتك أو سؤالك هنا:", height=150, placeholder="مثال: كيف أضمن حقي في هذا العقد؟")

    if st.button("بدء التحليل الاستراتيجي 🚀"):
        if not query:
            st.error("من فضلك اكتب سؤالك أولاً.")
        else:
            try:
                genai.configure(api_key=st.session_state['api_key'])
                
                # اختيار الموديل المتاح تلقائياً
                with st.spinner("جاري فحص الاتصال بالخادم..."):
                    m_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    target = next((m for m in m_list if '1.5-pro' in m), m_list[0])
                    ai = genai.GenerativeModel(target)

                # قراءة الملفات
                context, imgs = "", []
                if os.path.exists(DIR) and os.listdir(DIR):
                    with st.spinner("جاري استخراج الأدلة من مستنداتك..."):
                        # (نفس منطق قراءة الملفات السابق لضمان الدقة)
                        # ... [تم اختصاره هنا للتركيز على الحل] ...
                        pass 

                # تنفيذ التحليل
                prompt = f"أنت محامٍ مصري داهية وخبير. بناءً على السؤال التالي، قدم تحليلاً استراتيجياً وحلولاً ذكية: {query}"
                
                with st.spinner("المستشار يفكر الآن في أفضل مخرج قانوني..."):
                    res = ai.generate_content([prompt] + imgs)
                    st.success("اكتمل التحليل!")
                    st.markdown(f"<div class='legal-box'>{res.text}</div>", unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"عذراً، حدث خطأ: {str(e)}")
                if "API_KEY_INVALID" in str(e):
                    st.error("المفتاح الذي أدخلته غير صحيح. تأكد من نسخه بدقة.")
