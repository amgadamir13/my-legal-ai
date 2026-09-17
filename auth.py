# -*- coding: utf-8 -*-
"""تسجيل دخول خاص بمالك واحد فقط، مع حفظ كلمة المرور في Streamlit Secrets."""
import hashlib
import hmac

import streamlit as st


def _secret(name, default=""):
    try:
        return str(st.secrets.get(name, default) or default)
    except Exception:
        return default


def configured():
    return bool(_secret("APP_USERNAME") and (_secret("APP_PASSWORD") or _secret("APP_PASSWORD_SHA256")))


def password_matches(password):
    plain = _secret("APP_PASSWORD")
    digest = _secret("APP_PASSWORD_SHA256")
    if digest:
        candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(candidate, digest)
    return bool(plain) and hmac.compare_digest(password, plain)


def require_owner():
    """يعرض نموذج الدخول ويوقف بقية التطبيق حتى ينجح مالك الحساب."""
    if st.session_state.get("authenticated", False):
        return True

    st.markdown("## 🔐 دخول مالك الملف")
    st.info("هذا التطبيق مخصص لمستخدم واحد فقط. لا تشارك بيانات الدخول.")
    if not configured():
        st.error("لم يتم إعداد APP_USERNAME وAPP_PASSWORD في Streamlit Secrets بعد.")
        st.code('APP_USERNAME = "your-name"\nAPP_PASSWORD = "ضع-كلمة-مرور-قوية-هنا"', language="toml")
        st.stop()

    with st.form("owner_login"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول آمن", use_container_width=True)

    if submitted:
        if hmac.compare_digest(username, _secret("APP_USERNAME")) and password_matches(password):
            st.session_state.authenticated = True
            st.rerun()
        st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
    st.stop()


def logout_button():
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
