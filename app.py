# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
import fitz  # PyMuPDF
import re
from datetime import datetime

# =============================================
# 1. PAGE SETUP & STYLING (With vertical text fix)
# =============================================
st.set_page_config(page_title="Strategic War Room Pro 2026", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; 
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    
    .msg-box { 
        padding: 25px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 12px solid; background-color: #ffffff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        width: 100%;
        /* Prevent text from breaking vertically */
        word-wrap: break-word;
        white-space: normal;
    }
    
    .legal { border-color: #1d4ed8; background-color: #eff6ff; color: #1e3a8a; }
    .psych { border-color: #7c3aed; background-color: #f5f3ff; color: #2e1065; }
    .strat { border-color: #ea580c; background-color: #fffbeb; color: #451a03; }
    
    .stButton > button { width: 100%; font-weight: 700; height: 3.5em; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. HELPER FUNCTIONS
# =============================================
def extract_pdf_clean(file_obj):
    """Extract and clean text from a PDF file object."""
    try:
        file_obj.seek(0)
        pdf_data = file_obj.read()
        text = ""
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return re.sub(r'\s+', ' ', text).strip()
    except: return ""

def safe_display_text(text):
    """Escape dollar signs to prevent vertical LaTeX rendering[citation:8]."""
    if text:
        # This stops Streamlit from misinterpreting $ as a LaTeX command
        return text.replace("$", "\$")
    return text

# =============================================
# 3. SESSION STATE
# =============================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =============================================
# 4. SIDEBAR CONTROLS
# =============================================
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("Gemini API Key:", type="password", help="أدخل المفتاح واضغط Enter")
    
    # Updated list of current, working models (as of Jan 2026)
    model_choice = st.selectbox("الموديل:", [
        "gemini-2.0-flash",        # Stable and widely available
        "gemini-1.5-pro",          # Alternative Pro model
    ])
    max_chars = st.slider("🔧 قوة المسح (حروف):", 1000, 15000, 5000)
    
    st.divider()
    v_files = st.file_uploader("📂 ملفاتنا (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الذاكرة"):
        st.session_state.chat_history = []
        st.rerun()

# =============================================
# 5. MAIN APP INTERFACE
# =============================================
st.title("⚖️ Strategic War Room Pro")

# Display previous chat using the safe_display function
for chat in st.session_state.chat_history:
    safe_content = safe_display_text(chat["content"])
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{safe_content}</div>', unsafe_allow_html=True)

# Input Form
with st.form("strategic_form"):
    query = st.text_area("اشرح الموقف الاستراتيجي:")
    c1, c2, c3 = st.columns(3)
    # Using form_submit_button ensures logic runs on "Enter" press within the text area[citation:1][citation:6]
    btn_L = c1.form_submit_button("⚖️ قانوني")
    btn_P = c2.form_submit_button("🧠 نفسي")
    btn_S = c3.form_submit_button("🧨 استراتيجي")

# =============================================
# 6. PROCESSING LOGIC (With clear 'working' feedback)
# =============================================
if (btn_L or btn_P or btn_S):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح API أولاً.")
    elif not query:
        st.warning("⚠️ يرجى كتابة السؤال أو الموقف.")
    else:
        # --- IMMEDIATE FEEDBACK THAT CODE IS WORKING ---
        processing_placeholder = st.empty()
        with processing_placeholder.container():
            st.info("🔄 **تم استلام طلبك.** جاري تهيئة المحرك وتحليل المستندات...")
        
        try:
            # Modern Gemini API client setup[citation:2][citation:7]
            client = genai.Client(api_key=api_key)
            
            # Update status message
            with processing_placeholder.container():
                st.info("⚙️ **التجهيز مكتمل.** جاري الآن استشارة الذكاء الاصطناعي لتوليد الاستراتيجية...")
            
            with st.spinner("⚔️ جاري التحليل النهائي مع Gemini. قد يستغرق بضع ثوانٍ..."):
                # Extract text
                v_txt = " ".join([extract_pdf_clean(f) for f in v_files])[:max_chars]
                o_txt = " ".join([extract_pdf_clean(f) for f in o_files])[:max_chars]

                # Determine role
                if btn_L:
                    label, style, role = ("⚖️ القانوني", "legal", "خبير قانوني متخصص في الثغرات")
                elif btn_P:
                    label, style, role = ("🧠 النفسي", "psych", "محلل نفسي وخبير تفاوض")
                else:  # btn_S
                    label, style, role = ("🧨 الاستراتيجي", "strat", "مخطط استراتيجي داهية")

                prompt = f"أنت {role}. مستنداتنا: {v_txt}. الخصم: {o_txt}. الموقف: {query}. أجب بالعربية بنقاط واضحة ومباشرة."
                
                # Call the Gemini API[citation:2]
                res = client.models.generate_content(
                    model=model_choice,
                    contents=prompt
                )
                
                if res.text:
                    # Store the response (saving the original text)
                    st.session_state.chat_history.append({
                        "label": label,
                        "content": res.text,  # Original saved for download
                        "style": style
                    })
                    processing_placeholder.empty()  # Clear status messages
                    st.rerun()  # Refresh to show the new message
                else:
                    st.error("لم يتم توليد رد من النموذج.")

        except gapi_errors.ResourceExhausted:
            processing_placeholder.empty()
            st.error("""
            ⚠️ **انتهت الحصة المجانية لهذا الموديل.**
            *جرب تبديل الموديل في الشريط الجانبي أو انتظر دقيقة.*
            """)
        except Exception as e:
            processing_placeholder.empty()
            st.error(f"⚠️ خطأ في النظام: {e}")

# =============================================
# 7. OFFICIAL REPORT (#Official-Findings)
# =============================================
if st.session_state.chat_history:
    st.divider()
    st.markdown('<div id="official-findings"></div>', unsafe_allow_html=True)
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    # Prepare report with original text (dollar signs are fine in a .txt file)
    full_report = f"--- تقرير Strategic War Room ---\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for c in st.session_state.chat_history:
        full_report += f"[{c['label']}]:\n{c['content']}\n{'-'*30}\n"

    st.download_button(
        label="📥 تحميل التقرير الرسمي الكامل",
        data=full_report.encode('utf-8'),
        file_name=f"Strategic_Report_{datetime.now().strftime('%y%m%d_%H%M')}.txt",
        mime="text/plain"
    )
