import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. الإعدادات الأساسية والعلاج الجذري للعرض (The Anti-Vertical Fix) ---
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* فرض التنسيق الأفقي ومنع انكسار الكلمات نهائياً */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p, .msg-box {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: pre-wrap !important; /* يحافظ على الكلمات بجانب بعضها */
        word-break: keep-all !important; /* يمنع تحول الكلمة لحروف عمودية */
        display: block !important;
    }

    /* توسيع الحاويات لضمان عدم ضغط النص */
    .block-container { padding-top: 2rem; max-width: 95%; }

    /* تنسيق فقاعات المحادثة (الذاكرة الاستراتيجية) */
    .msg-box { 
        padding: 20px; border-radius: 15px; margin-bottom: 15px; 
        line-height: 1.8; border-right: 10px solid; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        width: 100% !important;
    }
    .user-style { background-color: #f8fafc; border-color: #1e3a8a; color: #1e3a8a; }
    .legal-style { background-color: #f0fdf4; border-color: #10b981; color: #14532d; }
    .psych-style { background-color: #f5f3ff; border-color: #8b5cf6; color: #4c1d95; }
    .street-style { background-color: #fff1f2; border-color: #f43f5e; color: #9f1239; }

    /* بطاقات النتائج الرسمية */
    .finding-card {
        background: white; padding: 20px; border-radius: 12px;
        margin-bottom: 15px; border-right: 6px solid #cbd5e1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        width: 100%;
    }
    
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; background-color: #1e3a8a; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الذاكرة والجلسة ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. مركز القيادة (Sidebar) ---
with st.sidebar:
    st.title("🛡️ المحقق الاستراتيجي")
    st.caption("نسخة 2026 - مشفرة")
    api_key = st.text_input("مفتاح Gemini السري:", type="password", placeholder="AIza...")
    st.divider()
    
    st.subheader("📁 قبو الحقائق (Vault)")
    v_files = st.file_uploader("ارفع أدلتك الموثوقة:", accept_multiple_files=True, key="vault")
    
    st.subheader("🚩 ملفات الخصم (Opponent)")
    o_files = st.file_uploader("ارفع أوراق الخصم لكشف التناقض:", accept_multiple_files=True, key="opponent")
    
    if st.button("تصفير الجلسة بالكامل 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")
st.info("نظام تحليل الأدلة بالعقول الثلاثة وكاشف التناقضات الجنائية.")

# --- 4. محرك العقول الثلاثة (The Multi-Agent Engine) ---
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي أو اطلب تحليل ملفات معينة:", height=100)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # اختيار الشخصية والأسلوب
        if btn_L: role, label, style = "مستشار قانوني خبير بالثغرات والتقادم", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل نفسي جنائي يقرأ ما وراء السطور", "🧠 النفسي", "psych-style"
        else: role, label, style = "مفاوض استراتيجي داهية يبحث عن حلول غير تقليدية", "🧨 الداهية", "street-style"

        # قراءة الملفات (Vault vs Opponent)
        def read_docs(files):
            text = ""
            for f in files:
                if f.type == "application/pdf":
                    with fitz.open(stream=f.read(), filetype="pdf") as doc:
                        for page in doc: text += page.get_text() + "\n"
            return text

        v_context = read_docs(v_files if v_files else [])
        o_context = read_docs(o_files if o_files else [])

        # بناء البرومبت الاستراتيجي
        prompt = f"""
        دورك: {role}.
        حقائق قبو المستخدم (الصدق): {v_context[:10000]}
        مستندات الخصم (محل الفحص): {o_context[:10000]}
        سؤال المستخدم الحالي: {user_query}
        
        المطلوب:
        1. تحليل دقيق ومنظم في نقاط.
        2. كشف أي تناقضات بين أوراق الخصم وحقائق المستخدم.
        3. اقتراح 'حركة استراتيجية' (Strategic Move) فورية.
        4. اللغة: عربية فصحى قانونية/استراتيجية رصينة.
        """
        
        with st.spinner(f"جاري استحضار {label}..."):
            response = model.generate_content(prompt)
            st.session_state.chat_history.append({"role": "user", "content": user_query, "label": "👤 أنت", "style": "user-style"})
            st.session_state.chat_history.append({"role": "ai", "content": response.text, "label": label, "style": style})
            st.rerun()

    except Exception as e:
        st.error(f"خطأ في الأنظمة: {e}")

# --- 5. عرض المحادثة (أفقي ومستقر) ---
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

# --- 6. قسم النتائج الرسمية (Official Findings) ---
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    st.markdown("""
        <div class="finding-card" style="border-right-color: #1e3a8a;">
            <b style="color: #1e3a8a;">⚖️ الثغرات المستخرجة:</b><br>يتم هنا تلخيص التناقضات المادية والتواريخ المغلوطة المكتشفة في الملفات.
        </div>
        <div class="finding-card" style="border-right-color: #8b5cf6;">
            <b style="color: #8b5cf6;">🧠 نمط الخصم:</b><br>تحليل دوافع الخصم بناءً على نبرة مستنداته ونقاط ضعفه النفسية.
        </div>
        <div class="finding-card" style="border-right-color: #10b981;">
            <b style="color: #10b981;">🎯 الخطوة الاستراتيجية:</b><br>التوصية النهائية للتحرك القادم لضمان السيطرة على الموقف.
        </div>
    """, unsafe_allow_html=True)
