# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
from datetime import datetime

# =============================================
# 1. PAGE SETUP & STYLING
# =============================================
st.set_page_config(page_title="The Classico: Boardroom", layout="centered")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; 
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    .msg-box { 
        padding: 15px; border-radius: 10px; margin-bottom: 10px; 
        border-right: 6px solid; background-color: #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        width: 100%;
        word-wrap: break-word;
    }
    .legal { border-color: #1d4ed8; background-color: #eff6ff; color: #1e3a8a; }
    .strat { border-color: #ea580c; background-color: #fffbeb; color: #451a03; }
    .combo { border-color: #059669; background-color: #ecfdf5; color: #064e3b; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. SESSION STATE & CONFIG
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

CONSTITUTION = """
1. Reverse Engineering: Write the ending first.
2. The Triple Strike: Legal, Financial, Psychological.
3. Controlled Alternatives: Force choices that serve us.
4. Information Embargo: Plan A has no holes. No burning cards early.
5. Identify 'The Mother': Target the root cause driving the conspiracy.
6. Poker Face: Zero unintended words.
7. Shadow Tracking: Flag potential conspiracy links (Witness = Buyer, etc.).
"""

# =============================================
# 3. MAIN INTERFACE (SIDEBAR)
# =============================================
with st.sidebar:
    st.title("⚙️ الإعدادات")
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    
    model_choice = st.selectbox("الموديل:", [
        "gemini-2.0-flash", 
        "gemini-1.5-pro",
        "gemini-1.5-flash"
    ])
    
    if st.button("🗑️ مسح الذاكرة"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ The Classico: Boardroom")

# =============================================
# 4. PROCESSING LOGIC
# =============================================
def run_classico_flow(user_query):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)
        
        with st.status("⚔️ جاري استدعاء الشركات (The Firms)...", expanded=True) as status:
            st.write("⚖️ المحامي يبني الحصن القانوني...")
            st.write("🧨 الفريق الأحمر يهاجم الثغرات...")
            st.write("🧠 الخبير النفسي يحدد 'كبش الفداء'...")
            
            full_prompt = f"""
            أنت نظام 'The Classico' لإدارة الصراعات والعمليات الاستراتيجية.
            الدستور الذي تلتزم به: {CONSTITUTION}
            
            المهمة:
            1. قيام الشركات بتحليل الموقف.
            2. قيام الفريق الأحمر بنقد التحليل.
            3. قيام المدقق بتصفية المخرج النهائي.
            
            الموقف: {user_query}
            
            يجب أن يكون الرد مقسماً كالتالي:
            ZONE_A: (الملف القانوني الرسمي) - لغة قانونية جافة وقوية صالحة للمحامي الخارجي.
            ZONE_B: (خزنة الاستراتيجية) - تحليل النوايا، نقاط الضعف النفسية، وخطوات 'الضربة الثلاثية'.
            GHOST_LIST: (قائمة الظلال) - أي روابط مشبوهة بين الأسماء المذكورة.
            """
            
            res = model.generate_content(full_prompt)
            status.update(label="✅ تم اكتمال التحليل من قبل مجلس الإدارة", state="complete")

        if res and res.text:
            st.session_state.chat_history.append({
                "content": res.text,
                "time": datetime.now().strftime("%H:%M")
            })
            st.rerun()
    except Exception as e:
        st.error(f"⚠️ خطأ: {e}")

# =============================================
# 5. BOARDROOM UI
# =============================================
query = st.text_area("أدخل التقرير أو الموقف الاستراتيجي:", height=150, placeholder="اشرح ما حدث هنا...")

if st.button("🚀 إطلاق عملية الكلاسيكو", use_container_width=True):
    if query and api_key:
        run_classico_flow(query)
    else:
        st.warning("الرجاء إدخال نص التأكد من مفتاح API")

if st.session_state.chat_history:
    latest = st.session_state.chat_history[-1]["content"]
    
    st.divider()
    tab1, tab2 = st.tabs(["📄 Zone A: الملف القانوني", "🔐 Zone B: الخزنة السرية"])
    
    with tab1:
        # Extract Zone A
        if "ZONE_A" in latest:
            content_a = latest.split("ZONE_A:")[1].split("ZONE_B:")[0]
            st.markdown(f'<div class="msg-box legal"><b>🏛️ تقرير المحامي:</b><br>{content_a}</div>', unsafe_allow_html=True)
            st.download_button("📥 تحميل للمحامي", content_a)

    with tab2:
        # Extract Zone B
        if "ZONE_B" in latest:
            content_b = latest.split("ZONE_B:")[1]
            st.markdown(f'<div class="msg-box strat"><b>🧨 التحليل الاستراتيجي:</b><br>{content_b}</div>', unsafe_allow_html=True)
            st.warning("⚠️ محتويات هذه الخزنة سرية للغاية (Chairman Only)")
