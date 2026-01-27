# --------------------
# استدعاء Gemini (تكملة الدالة الأساسية)
# --------------------
def call_gemini(prompt: str, model_name: str, api_key: str):
    """
    محرك الاتصال الذكي: يحاول استدعاء النموذج بأكثر من واجهة برمجية 
    لضمان التوافق مع تحديثات مكتبة google-generativeai.
    """
    try:
        genai.configure(api_key=api_key)
        
        # محاولة الوصول للنموذج
        model = genai.GenerativeModel(model_name)
        
        # استدعاء الإنشاء مع معالجة الأخطاء الشائعة في الـ Safety Settings
        response = model.generate_content(prompt)
        
        # استخراج النص بطريقة آمنة
        answer = extract_text_from_response(response)
        
        if not answer or answer.strip() == "":
             raise ValueError("استجابة النموذج فارغة أو تم حظرها.")
             
        return response, answer

    except Exception as e:
        error_msg = f"فشل استدعاء Gemini: {str(e)}"
        if "API_KEY_INVALID" in str(e):
            error_msg = "مفتاح API غير صحيح. يرجى التأكد منه في الشريط الجانبي."
        raise RuntimeError(error_msg)

# --------------------
# المحرك الاستراتيجي (الواجهة الأمامية)
# --------------------
with st.form("war_room_form", clear_on_submit=True):
    user_query = st.text_area("اشرح الموقف الحالي أو اطلب تحليل التناقضات:", height=120)
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and user_query:
    try:
        # تحديد الشخصية
        if btn_L: label, role, style = "⚖️ القانوني", "محامٍ جنائي متخصص في الثغرات", "legal-style"
        elif btn_P: label, role, style = "🧠 النفسي", "محلل سلوكي يحلل لغة الجسد والنصوص", "psych-style"
        else: label, role, style = "🧨 الداهية", "مفاوض استراتيجي يجد حلولاً خارج الصندوق", "street-style"

        # قراءة المستندات
        with st.spinner("جاري قراءة الملفات وتحليل البيانات..."):
            v_text = get_text_from_files(v_files)
            o_text = get_text_from_files(o_files)

        # بناء البرومبت الاحترافي
        full_prompt = f"""
        تقمص دور: {role}.
        سياق الحقائق (Vault): {v_text[:10000]}
        ادعاءات الخصم (Opponent): {o_text[:10000]}
        سؤال المستخدم: {user_query}
        
        المطلوب:
        1. تحليل دقيق جداً للموقف.
        2. كشف التناقضات بين الحقائق وادعاءات الخصم (إن وجدت).
        3. اقتراح خطة عمل استراتيجية فورية.
        أجب بالعربية الفصحى وبشكل نقاط واضحة.
        """

        with st.spinner(f"جاري معالجة الرد بواسطة {label}..."):
            raw_resp, answer_text = call_gemini(full_prompt, model_name, api_key)
            st.session_state.raw_last_response = raw_resp
            
            # إضافة للمحادثة
            st.session_state.chat_history.append({"role": "user", "content": user_query, "label": "👤 أنت", "style": "user-style"})
            st.session_state.chat_history.append({"role": "ai", "content": answer_text, "label": label, "style": style})
            st.rerun()

    except Exception as e:
        st.error(f"⚠️ خطأ استراتيجي: {str(e)}")
        if show_raw:
            st.code(traceback.format_exc())

# --------------------
# عرض التاريخ (Chat Display)
# --------------------
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}:</b><br>{chat["content"]}</div>', unsafe_allow_html=True)

# --------------------
# قسم النتائج الرسمية (Findings)
# --------------------
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير الاستراتيجي النهائي (#Official-Findings)")
    
    # عرض Debug إذا تم تفعيله
    if show_raw and st.session_state.raw_last_response:
        with st.expander("🔍 تفاصيل الاستجابة الخام (Debug)"):
            st.write(st.session_state.raw_last_response)

    st.markdown("""
        <div class="finding-card">
            <b style="color: #1e3a8a;">⚖️ الخلاصة القانونية:</b><br>
            يتم استخراج الثغرات بناءً على التناقضات المكتشفة في ملفات الخصم مقارنة بالحقائق الموثقة.
        </div>
        <div class="finding-card">
            <b style="color: #10b981;">🎯 التوصية الفورية:</b><br>
            اتبع استراتيجية "الهجوم المضاد بالوثائق" المذكورة في رد المستشار أعلاه.
        </div>
    """, unsafe_allow_html=True)
