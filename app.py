# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions as gapi_errors
from datetime import datetime

# =============================================
# 4. THE CLASSICO ENGINE (ORCHESTRATOR)
# =============================================

CONSTITUTION = """
1. Reverse Engineering: Write the ending first.
2. The Triple Strike: Legal, Financial, Psychological.
3. Controlled Alternatives: Force choices that serve us.
4. Information Embargo: No Plan B—Plan A is perfect.
5. Identify 'The Mother': Target the root cause.
6. Poker Face: Zero unintended words.
7. Shadow Tracking: Flag potential conspiracy links.
"""

def run_classico_flow(query):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)
        
        # The Silent Fight (Background Processing)
        with st.status("⚔️ جاري استدعاء الشركات (The Firms)...", expanded=False) as status:
            st.write("⚖️ المحامي يبني الحصن القانوني...")
            st.write("🧨 الفريق الأحمر يهاجم الثغرات...")
            st.write("🧠 الخبير النفسي يحلل مستويات الطمع...")
            
            full_prompt = f"""
            أنت نظام 'The Classico' لإدارة الصراعات.
            الدستور: {CONSTITUTION}
            المهمة: تحليل الموقف التالي عبر 3 شركات (قانوني، نفسي، استراتيجي) ثم تدقيقهم بواسطة 'المدقق'.
            الموقف: {query}
            
            المطلوب مخرج نهائي مقسم حصراً إلى:
            ZONE_A: (الملف الرسمي) - حقائق وقوانين جافة للمحامي الخارجي.
            ZONE_B: (الخزنة السرية) - تحليل الخصم، كبش الفداء، التحركات النفسية، ونقاط الضعف.
            GHOST_LIST: قائمة بأي أسماء تكررت أو روابط مشبوهة.
            """
            
            res = model.generate_content(full_prompt)
            status.update(label="✅ تم الانتهاء من التحليل الاستراتيجي", state="complete")

        if res and res.text:
            # Parsing the logic into the UI
            content = res.text
            st.session_state.chat_history.append({
                "label": "🏛️ قرار مجلس الإدارة",
                "content": content,
                "style": "combo"
            })
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ خطأ في النظام: {e}")

# Main Trigger for The Classico
if query and api_key:
    if st.button("🚀 إطلاق عملية الكلاسيكو (The Classico Flow)", use_container_width=True):
        run_classico_flow(query)

# =============================================
# 5. THE BOARDROOM UI (ZONE A / ZONE B)
# =============================================
if st.session_state.chat_history:
    st.divider()
    latest_response = st.session_state.chat_history[-1]["content"]
    
    tab1, tab2 = st.tabs(["📄 Zone A: الملف القانوني", "🔐 Zone B: خزنة الاستراتيجية"])
    
    with tab1:
        if "ZONE_A" in latest_response:
            zone_a = latest_response.split("ZONE_A:")[1].split("ZONE_B:")[0]
            st.markdown(f'<div class="msg-box legal">{zone_a}</div>', unsafe_allow_html=True)
            st.download_button("📥 تحميل الملف الرسمي", zone_a, file_name="Legal_File.txt")
            
    with tab2:
        if "ZONE_B" in latest_response:
            zone_b = latest_response.split("ZONE_B:")[1]
            st.markdown(f'<div class="msg-box strat">{zone_b}</div>', unsafe_allow_html=True)
            st.warning("⚠️ تحذير: هذه المنطقة لرئيس مجلس الإدارة فقط.")

    if st.button("🔄 تحليل جديد"):
        st.session_state.chat_history = []
        st.rerun()
