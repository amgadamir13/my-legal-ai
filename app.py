# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
from datetime import datetime

# =============================================
# 1. PAGE SETUP & STYLING (iOS Optimized)
# =============================================
st.set_page_config(page_title="The Classico: War Room", layout="centered")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important; 
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    .zone-a { border-right: 6px solid #1d4ed8; background-color: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .zone-b { border-right: 6px solid #b91c1c; background-color: #fef2f2; padding: 15px; border-radius: 8px; color: #7f1d1d; }
    .ghost-tag { background-color: #000; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. SESSION STATE
# =============================================
if "vault" not in st.session_state:
    st.session_state.vault = []

# =============================================
# 3. CORE LOGIC: THE ORCHESTRATOR
# =============================================
def run_classico_orchestration(query, model_choice, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_choice)
    
    # --- STEP 1: THE SILENT FIGHT (Internal Debate) ---
    with st.status("⚔️ جاري تفعيل غرف العمليات (The Silent Fight)...", expanded=False) as status:
        st.write("🕵️ جاري تعقب الخيوط (Detective Unit)...")
        # Internal Logic for Red Team & Detective
        internal_prompt = f"تحليل استخباراتي للموقف: {query}. ابحث عن 'اللاعبين الخفيين' والثغرات."
        internal_analysis = model.generate_content(internal_prompt).text
        
        st.write("🔴 جاري هجوم الفريق الأحمر (Red Team)...")
        status.update(label="✅ اكتمل التحليل الداخلي", state="complete")

    # --- STEP 2: DUAL-ZONE GENERATION ---
    final_prompt = f"""
    أنت نظام 'The Classico' لإدارة الصراعات. بناءً على الموقف التالي: {query}
    
    عليك تطبيق (القواعد الـ 18 الذهبية) وتوليد تقرير في منطقتين:
    
    [ZONE_A]: ملف قانوني رصين (محامي شرعي وعقاري). ركز على المواريث، عقود الإيجار، والأدلة. (للقضاء).
    [ZONE_B]: قبو الاستراتيجية. ملف لـ 'Chairman' فقط. شفرة 'الخال/الأم'، تحليل الجشع، التلاعب النفسي، وخطوات الضغط (Psy-Ops).
    
    التزم بالتنسيق التالي بدقة:
    ZONE_A_START
    (المحتوى)
    ZONE_A_END
    ZONE_B_START
    (المحتوى)
    ZONE_B_END
    """
    
    response = model.generate_content(final_prompt).text
    
    # Parsing zones
    try:
        zone_a = response.split("ZONE_A_START")[1].split("ZONE_A_END")[0].strip()
        zone_b = response.split("ZONE_B_START")[1].split("ZONE_B_END")[0].strip()
        return zone_a, zone_b
    except:
        return response, "لم يتم توليد القبو الاستراتيجي بشكل منفصل."

# =============================================
# 4. MAIN INTERFACE
# =============================================
st.title("🏛️ Project: The Classico")
st.caption("نظام أوركسترا إدارة الصراعات - الإصدار الاستراتيجي")

api_key = st.secrets.get("GEMINI_API_KEY", None)
model_choice = st.selectbox("الموديل الاستراتيجي:", ["gemini-1.5-pro", "gemini-1.5-flash"])

query = st.text_area("أدخل معطيات الصراع (Raw Data):", height=150, placeholder="مثال: نزاع على تركة عقارية، تدخل أطراف خارجية...")

if st.button("🚀 بدء تفعيل البروتوكول (The Triple Strike)"):
    if query and api_key:
        za, zb = run_classico_orchestration(query, model_choice, api_key)
        st.session_state.vault.append({"date": datetime.now(), "legal": za, "secret": zb})
        st.rerun()

# =============================================
# 5. DUAL-ZONE DISPLAY
# =============================================
for entry in reversed(st.session_state.vault):
    st.divider()
    st.info(f"📅 جلسة بتاريخ: {entry['date'].strftime('%Y-%m-%d %H:%M')}")
    
    # Zone A: The Legal File
    with st.expander("⚖️ Zone A: الملف القانوني (Court-Ready)", expanded=True):
        st.markdown(f'<div class="zone-a">{entry["legal"]}</div>', unsafe_allow_html=True)
    
    # Zone B: The Strategic Vault
    with st.expander("🕵️ Zone B: قبو الاستراتيجية (Chairman Only)", expanded=False):
        st.markdown(f'<div class="zone-b">{entry["secret"]}</div>', unsafe_allow_html=True)
        st.warning("⚠️ تحذير: هذه المعلومات للاطلاع الشخصي فقط ولا تظهر في ملف القضية.")

if st.button("🗑️ إتلاف السجلات (Clear All)"):
    st.session_state.vault = []
    st.rerun()
