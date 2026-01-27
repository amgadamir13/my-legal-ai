import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. هندسة واجهة المستخدم (تنسيق Apple-RTL النهائي) ---
st.set_page_config(page_title="المستشار الاستراتيجي Pro", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* إعدادات شاملة لإجبار المتصفح على قراءة النصوص العربية بشكل أفقي ومتصل */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* إصلاح الفقاعات - هذا هو الجزء الأهم للأيفون */
    .msg-box { 
        padding: 15px 20px; 
        border-radius: 18px; 
        margin-bottom: 15px; 
        line-height: 1.6; 
        border-right: 8px solid;
        display: block !important; /* يمنع التراكم العمودي */
        unicode-bidi: isolate !important; /* يحافظ على اتجاه النص */
        white-space: normal !important; /* يسمح بالتفاف النص الطبيعي */
        word-wrap: break-word !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .user-style { background-color: #1e293b; border-color: #3b82f6; color: #f8fafc; }
    .legal-style { background-color: #064e3b; border-color: #10b981; color: #ecfdf5; }
    .psych-style { background-color: #4c1d95; border-color: #a855f7; color: #f5f3ff; }
    .street-style { background-color: #7f1d1d; border-color: #f43f5e; color: #fff1f2; }

    /* تنسيق الحقول */
    .stTextArea textarea {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .stButton button { border-radius: 12px; height: 3.5em; background-color: #1e3a8a; color: white; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الجلسة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. القائمة الجانبية ---
with st.sidebar:
    st.title("🛡️ مركز العمليات")
    api_key = st.text_input("مفتاح Gemini:", type="password")
    
    st.divider()
    strategy = st.text_input("ميثاقنا الاستراتيجي:", "الذكاء والحكمة")
    
    st.divider()
    my_docs = st.file_uploader("📂 الخزنة (Vault)", accept_multiple_files=True)
    opp_docs = st.file_uploader("🚩 ملفات الخصم", accept_multiple_files=True)
    
    if st.button("تفريغ المحادثة 🗑️"):
        st.session_state.messages = []
        st.rerun()

# --- 4. واجهة العرض ---
st.title("⚖️ المحقق الاستراتيجي")

for m in st.session_state.messages:
    style = m.get("style", "user-style")
    label = m.get("label", "👤 أنت")
    # استخدام markdown مع تنسيق HTML لعرض النص بوضوح
    st.markdown(f'<div class="msg-box {style}"><b>{label}:</b><br>{m["content"]}</div>', unsafe_allow_html=True)

# --- 5. محرك العقول الثلاثة ---
with st.form("action_form", clear_on_submit=True):
    user_input = st.text_area("أدخل رسالة الخصم أو سؤالك هنا...", placeholder="اكتب هنا...")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_input:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # اختيار الدور
        if btn_L: role, label, style = "محامي خبير بالثغرات والتقادم", "⚖️ القانوني", "legal-style"
        elif btn_P: role, label, style = "محلل نفسي يكتشف الكذب والغرور من اللغة", "🧠 النفسي", "psych-style"
        else: role, label, style = "مفاوض شوارع داهية يجد حلولاً غير تقليدية", "🧨 الداهية", "street-style"

        # قراءة الملفات
        v_txt = ""
        if my_docs:
            for f in my_docs:
                if f.type == "application/pdf":
                    with fitz.open(stream=f.read(), filetype="pdf") as doc:
                        for p in doc: v_txt += p.get_text() + "\n"
        
        o_txt = ""
        if opp_docs:
            for f in opp_docs:
                if f.type == "application/pdf":
                    with fitz.open(stream=f.read(), filetype="pdf") as doc:
                        for p in doc: o_txt += p.get_text() + "\n"

        prompt = f"""
        أجب كـ {role}. قيمنا هي {strategy}.
        السياق التاريخي في الخزنة: {v_txt[:6000]}
        أوراق الخصم المرفقة: {o_txt[:6000]}
        السؤال/الموقف: {user_input}
        
        * أجب بالعربية الفصحى بشكل مترابط ومنظم جداً.
        """
        
        with st.spinner("جاري التحليل الاستراتيجي..."):
            response = model.generate_content(prompt)
            # إضافة المحادثة للسجل
            st.session_state.messages.append({"role": "user", "content": user_input, "label": "👤 أنت", "style": "user-style"})
            st.session_state.messages.append({"role": "assistant", "content": response.text, "label": label, "style": style})
            st.rerun()
            
    except Exception as e:
        st.error(f"Error: {e}")
