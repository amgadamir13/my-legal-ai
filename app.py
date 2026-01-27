import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io

# --- 1. UI ARCHITECTURE (Arabic RTL Fixed) ---
st.set_page_config(page_title="Strategic War Room", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; 
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        background-color: #0f172a; color: #f8fafc;
    }
    /* Fixed Arabic Text Areas */
    textarea, input { 
        direction: rtl !important; 
        text-align: right !important; 
        font-family: 'Cairo', sans-serif !important;
    }
    /* Password/API field stays LTR for accuracy */
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    
    .msg-box { padding: 22px; border-radius: 20px; margin-bottom: 15px; line-height: 1.8; }
    .user-style { background-color: #1e293b; border-right: 8px solid #38bdf8; }
    .ai-style { background-color: #1e293b; border-right: 8px solid #10b981; }
    .psych-style { background-color: #2e1065; border-right: 8px solid #a855f7; }
    .street-style { background-color: #450a0a; border-right: 8px solid #ef4444; }
    
    .stButton button { border-radius: 12px; height: 3.5em; background: linear-gradient(90deg, #0ea5e9, #2563eb); color: white; border: none; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMORY MANAGEMENT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 3. COMMAND CENTER (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ مركز القيادة")
    api_key = st.text_input("مفتاح Gemini (AIza...):", type="password")
    
    st.divider()
    st.subheader("🎯 ميثاق الاستراتيجية")
    user_strategy = st.text_input("قيمنا (مثلاً: الصبر، الصدق، الهجوم):", placeholder="أدخل قيمك هنا...")
    
    st.divider()
    st.subheader("📁 ملفات القضية")
    my_docs = st.file_uploader("حقائبي (Vault):", accept_multiple_files=True, key="v")
    opp_docs = st.file_uploader("ملفات الخصم:", accept_multiple_files=True, key="o")
    
    if st.button("تصفير الذاكرة 🗑️"):
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ War Room: المحقق الاستراتيجي")

# --- 4. CHAT DISPLAY ---
for chat in st.session_state.chat_history:
    style = "user-style" if chat["role"] == "user" else chat.get("style", "ai-style")
    label = "👤 أنت" if chat["role"] == "user" else chat.get("label", "⚖️ المستشار")
    st.markdown(f'<div class="msg-box {style}"><b>{label}:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

# --- 5. THE TRIPLE-BRAIN ENGINE ---
with st.form("war_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف أو التطور الجديد:", height=100)
    col1, col2, col3 = st.columns(3)
    with col1: legal_btn = st.form_submit_button("⚖️ قانوني")
    with col2: psych_btn = st.form_submit_button("🧠 نفسي")
    with col3: street_btn = st.form_submit_button("🧨 داهية")

if legal_btn or psych_btn or street_btn:
    if not api_key:
        st.error("يرجى إدخال المفتاح أولاً.")
    elif user_query:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Logic to switch personalities
            if legal_btn:
                instr, label, style = "أنت محامي داهية، استخرج الثغرات.", "⚖️ القانوني", "ai-style"
            elif psych_btn:
                instr, label, style = "أنت طبيب نفسي جنائي، حلل شخصية الخصم من لغته.", "🧠 النفسي", "psych-style"
            else:
                instr, label, style = "أنت مفاوض شوارع خبير، ابحث عن حلول غير تقليدية وضغوط.", "🧨 الداهية", "street-style"

            # Context extraction
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

            # The Secret History Prompt
            full_prompt = f"""
            {instr}
            استراتيجيتنا وقيمنا الملتزمين بها: {user_strategy}
            
            اقرأ ما بين السطور في تاريخنا (Vault): {v_txt[:10000]}
            وقارنه بما يقوله الخصم الآن: {o_txt[:10000]}
            
            السؤال الحالي: {user_query}
            
            * ملاحظة: تعرف على الأنماط المتكررة في تاريخهم دون ذكرها صراحة إلا إذا لزم الأمر.
            """
            
            response = model.generate_content(full_prompt)
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.chat_history.append({"role": "assistant", "content": response.text, "label": label, "style": style})
            st.rerun()

        except Exception as e:
            st.error(f"خطأ: {str(e)}")
