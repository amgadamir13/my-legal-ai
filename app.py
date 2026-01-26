import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# 1. تنسيق الواجهة (أنيق وسهل للعين)
st.set_page_config(page_title="المستشار القانوني الذكي", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { direction: rtl; text-align: right; font-family: 'Cairo', sans-serif; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background-color: #1e3a8a; color: white; font-weight: bold; }
    .result-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-right: 10px solid #1e3a8a; box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: #1a1a1a; line-height: 1.8; }
    </style>
    """, unsafe_allow_html=True)

# --- الواجهة الرئيسية ---
st.title("⚖️ المستشار القانوني المصري")
st.write("أهلاً بك؛ أنا مستشارك الذكي. سأدمج خبرتي في القانون المصري مع الملفات التي ستزودني بها الآن.")

# 2. منطقة الدخول (API Key) - مع ميزة الحفظ
with st.expander("🔑 إعدادات الوصول (اضغط هنا لإدخال المفتاح)", expanded=True):
    api_key = st.text_input("أدخل مفتاح Gemini:", type="password", autocomplete="current-password")
    if api_key:
        st.success("✅ تم التعرف على المفتاح")

# 3. رفع الملفات (الحل لمشكلة "المجلد المفقود")
uploaded_files = st.file_uploader("ارفع مستنداتك القانونية (PDF أو صور) هنا:", accept_multiple_files=True)

# 4. السؤال القانوني
query = st.text_area("اشرح مشكلتك القانونية أو اسأل عن تفاصيل في المستندات:", height=150)

if st.button("تحليل استراتيجي شامل 🚀"):
    if not api_key:
        st.error("من فضلك أدخل مفتاح الـ API أولاً في خانة الإعدادات.")
    elif not query:
        st.warning("من فضلك اكتب سؤالك أو اشرح الموقف.")
    else:
        try:
            genai.configure(api_key=api_key)
            
            # اختيار الموديل تلقائياً
            m_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = next((m for m in m_list if '1.5-pro' in m), m_list[0])
            model = genai.GenerativeModel(target)
            
            context = ""
            images_to_send = []

            # معالجة الملفات المرفوعة "فوراً"
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    if uploaded_file.type == "application/pdf":
                        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                        for page in doc:
                            context += page.get_text()
                    else:
                        img = Image.open(uploaded_file)
                        images_to_send.append(img)
            
            # صياغة الاستراتيجية (عقلية المحامي المصري)
            prompt = f"""
            بصفتك مستشاراً قانونياً مصرياً داهية وخبيراً بالتاريخ القانوني:
            1. حلل الموقف بناءً على القانون المصري.
            2. استخدم المعلومات المرفقة من الملفات: {context[:5000]} 
            3. اقترح حلولاً ذكية أو ثغرات أو مسارات بديلة لتفادي المشاكل.
            سؤال المستخدم: {query}
            """
            
            with st.spinner("المستشار يقوم الآن بمراجعة القوانين وتحليل الأوراق..."):
                response = model.generate_content([prompt] + images_to_send)
                st.markdown("### 📜 التقرير القانوني والاستراتيجية المقترحة:")
                st.markdown(f'<div class="result-card">{response.text}</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء التحليل: {str(e)}")
