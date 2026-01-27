# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
import os
import re
from datetime import datetime

# =============================================
# 1. PAGE CONFIG & RADICAL ARABIC FIX
# =============================================
st.set_page_config(page_title="Strategic War Room Pro", layout="wide")

# التنسيق الذي يقتل مشكلة النص الرأسي نهائياً
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* منع انكماش الحاوية الرئيسية */
    .main .block-container {
        max-width: 95% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* إصلاح الفقاعات ومنع انكسار الكلمات */
    [data-testid="stMarkdownContainer"] p, .msg-box {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        white-space: normal !important; /* السماح بالتفاف السطور لا الحروف */
        word-break: keep-all !important; /* منع كسر الكلمة الواحدة */
        overflow-wrap: break-word !important;
        line-height: 1.8 !important;
        display: block !important;
        min-width: 250px !important; /* ضمان مساحة عرض دنيا */
    }
    
    .msg-box { 
        padding: 20px; border-radius: 15px; margin-bottom: 20px; 
        border-right: 10px solid; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .user-style { border-color: #1e3a8a; background-color: #f8fafc; color: #1e3a8a; }
    .legal { border-color: #3b82f6; background-color: #eff6ff; }
    .psych { border-color: #8b5cf6; background-color: #f5f3ff; }
    .strat { border-color: #f59e0b; background-color: #fffbeb; }

    /* تحسين المدخلات للأيفون */
    .stTextArea textarea { direction: rtl !important; text-align: right !important; font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. CORE FUNCTIONS
# =============================================
def normalize_arabic_text(text):
    if not text: return ""
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    text = re.sub(r'\s+', ' ', text) # دمج المسافات الزائدة التي تسبب تقطعاً
    return text.strip()

def extract_text_from_pdf(file_bytes):
    try:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc: text += page.get_text() + " "
        return normalize_arabic_text(text)
    except Exception as e: return f"خطأ: {e}"

# =============================================
# 3. INTERFACE & LOGIC
# =============================================
if "chat_history" not in st.session_state: st.session_state.chat_history = []

with st.sidebar:
    st.header("🛡️ الإعدادات")
    api_key = st.text_input("Gemini API Key:", type="password")
    model_choice = st.selectbox("الموديل:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    v_files = st.file_uploader("📂 الخزنة", type=["pdf"], accept_multiple_files=True)
    o_files = st.file_uploader("⚔️ الخصم", type=["pdf"], accept_multiple_files=True)
    if st.button("🗑️ مسح"): 
        st.session_state.chat_history = []
        st.rerun()

st.title("⚖️ Strategic War Room Pro")

# عرض الرسائل
for chat in st.session_state.chat_history:
    st.markdown(f'<div class="msg-box {chat["style"]}"><b>{chat["label"]}</b>:<br>{chat["content"]}</div>', unsafe_allow_html=True)

# نموذج الإدخال
with st.form("main_form", clear_on_submit=True):
    u_query = st.text_area("اشرح الموقف:")
    c1, c2, c3 = st.columns(3)
    with c1: btn_L = st.form_submit_button("⚖️ قانوني")
    with c2: btn_P = st.form_submit_button("🧠 نفسي")
    with c3: btn_S = st.form_submit_button("🧨 داهية")

if (btn_L or btn_P or btn_S) and api_key and u_query:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_choice)
        
        v_txt = "".join([extract_text_from_pdf(f.read()) for f in v_files]) if v_files else ""
        o_txt = "".join([extract_text_from_pdf(f.read()) for f in o_files]) if o_files else ""

        label, style, role = ("⚖️ القانوني", "legal", "محامي") if btn_L else \
                             ("🧠 النفسي", "psych", "خبير نفسي") if btn_P else \
                             ("🧨 الداهية", "strat", "استراتيجي")
        
        prompt = f"أنت {role}. حلل: {u_query}. سياقنا: {v_txt[:4000]}. سياق الخصم: {o_txt[:4000]}. أجب بالعربية الفصحى وبشكل عرضي منظم."
        
        with st.spinner("جاري التحليل..."):
            res = model.generate_content(prompt)
            st.session_state.chat_history.append({"label": label, "content": res.text, "style": style})
            st.rerun()
    except Exception as e: st.error(f"Error: {e}")

# قسم النتائج النهائية
if st.session_state.chat_history:
    st.divider()
    st.subheader("📋 التقرير النهائي (#Official-Findings)")
    report = "\n".join([f"{c['label']}: {c['content']}" for c in st.session_state.chat_history])
    st.download_button("📥 تحميل التقرير", report, file_name="report.txt")
