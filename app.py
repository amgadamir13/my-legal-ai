# =============================================
# 3. الشريط الجانبي (Sidebar) - محدث
# =============================================
with st.sidebar:
    st.header("🛡️ مركز القيادة")
    api_key = st.text_input("Gemini API Key:", type="password", help="أدخل المفتاح واضغط Enter")
    
    # ✅ قائمة محدثة بالموديلات المتاحة حاليًا
    model_choice = st.selectbox("الموديل:", [
        "gemini-2.5-flash",        # موديل فلاش سريع ومستقر (موصى به)
        "gemini-2.5-flash-lite",   # نسخة أخف وأسرع من 2.5 فلاش
        "gemini-2.0-flash",        # مدعوم حتى 31 مارس 2026
        "gemini-1.5-pro"           # موديل "برو" الأقدم (قد تكون حصته منتهية)
    ])
    max_chars = st.slider("🔧 قوة المسح:", 1000, 15000, 5000)
    
    st.divider()
    v_files = st.file_uploader("📂 ملفاتنا (Vault)", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ ملفات الخصم (Opponent)", type=["pdf"], accept_multiple_files=True)
    
    if st.button("🗑️ مسح الذاكرة"):
        st.session_state.chat_history = []
        st.rerun()

# =============================================
# 4. المحرك الرئيسي (Logic) - محدث بإصدار API حديث
# =============================================
st.title("⚖️ Strategic War Room Pro")

# عرض سجل الحوار
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

with st.form("strategic_form", clear_on_submit=True):
    query = st.text_area("اشرح الموقف الاستراتيجي:")
    c1, c2, c3 = st.columns(3)
    btn_L = c1.form_submit_button("⚖️ قانوني")
    btn_P = c2.form_submit_button("🧠 نفسي")
    btn_S = c3.form_submit_button("🧨 استراتيجي")

if (btn_L or btn_P or btn_S):
    if not api_key:
        st.error("⚠️ يرجى إدخال مفتاح API أولاً.")
    elif not query:
        st.warning("⚠️ يرجى كتابة السؤال أو الموقف.")
    else:
        try:
            # ✅ الطريقة الحديثة والبسيطة لتهيئة العميل
            client = genai.Client(api_key=api_key)
            
            with st.spinner("⚔️ جاري التحليل..."):
                v_txt = " ".join([extract_pdf_clean(f) for f in v_files])
                o_txt = " ".join([extract_pdf_clean(f) for f in o_files])

                # ✅ تحديد الدور بشكل صحيح (إصلاح خطأ منطقي)
                if btn_L:
                    label, style, role = ("⚖️ القانوني", "legal", "خبير قانوني متخصص في الثغرات")
                elif btn_P:
                    label, style, role = ("🧠 النفسي", "psych", "محلل نفسي وخبير تفاوض")
                else:  # btn_S is True
                    label, style, role = ("🧨 الاستراتيجي", "strat", "مخطط استراتيجي داهية")

                prompt = f"أنت {role}. مستنداتنا: {v_txt[:max_chars]}. الخصم: {o_txt[:max_chars]}. الموقف: {query}. أجب بالعربية بنقاط."
                
                # ✅ الاستدعاء المبسط باستخدام العميل (Client)
                res = client.models.generate_content(
                    model=model_choice,  # ✅ نمرر اسم الموديل مباشرة
                    contents=prompt
                )
                
                if res.text:
                    st.session_state.chat_history.append({"label": label, "content": res.text, "style": style})
                    st.rerun()

        except gapi_errors.ResourceExhausted:
            st.error("""
            ⚠️ **انتهت الحصة المجانية لهذا الموديل.**
            *جرب تبديل الموديل في الشريط الجانبي إلى **'gemini-2.5-flash'** (الخيار الأول).*
            """)
        except Exception as e:
            st.error(f"⚠️ خطأ: {e}")
