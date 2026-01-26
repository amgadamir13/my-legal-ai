import streamlit as st
import os, fitz, json, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from fpdf import FPDF

# --- 1. GLOBAL RTL & MOBILE STYLING ---
st.set_page_config(page_title="المحقق القانوني", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* Force the entire app to be RTL */
    .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
    }

    /* Fix text alignment for all inputs and text areas */
    input, textarea, .stMarkdown, p, li, h1, h2, h3 {
        direction: rtl !important;
        text-align: right !important;
    }

    /* Mobile-First Button Styling */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #1A73E8;
        color: white;
        font-weight: bold;
        border: none;
    }

    /* Sidebar Fix (Moves to the right for Arabic) */
    [data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }

    /* Report Card Styling */
    .report-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-right: 6px solid #1A73E8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-top: 20px;
        color: #1f1f1f;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE SETUP ---
@st.cache_resource
def load_engine():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_engine()
CORPUS_DIR = "documents"

@st.cache_data
def index_documents():
    meta, texts = [], []
    if not os.path.exists(CORPUS_DIR): os.makedirs(CORPUS_DIR)
    files = [f for f in os.listdir(CORPUS_DIR) if f.lower().endswith(".pdf")]
    if not files: return None, None
    for f in files:
        path = os.path.join(CORPUS_DIR, f)
        try:
            with fitz.open(path) as doc:
                for i, page in enumerate(doc):
                    t = page.get_text().strip()
                    if t:
                        meta.append({"file": f, "page": i+1, "content": t})
                        texts.append(t)
        except: continue
    if not texts: return None, None
    embeddings = embed_model.encode(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    return index, meta

vector_index, library = index_documents()

# --- 3. UI FRONT-END ---
st.image("https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg", width=50)
st.title("المحقق القانوني الذكي")
st.write("نظام تحليل العقود والوثائق بالذكاء الاصطناعي")

with st.sidebar:
    st.header("🔑 الوصول للنظام")
    api_key = st.text_input("مفتاح API الخاص بك", type="password")
    if vector_index:
        st.success(f"تمت أرشفة {len(library)} صفحة")
    else:
        st.warning("المكتبة فارغة - يرجى رفع الملفات")
    if st.button("تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

u_query = st.text_area("ما هو استفسارك القانوني؟", height=120)
execute_analysis = st.button("بدء التحليل الاستراتيجي ⚖️")

# --- 4. EXECUTION ---
if execute_analysis and api_key:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        with st.spinner("جاري فحص المستندات..."):
            q_vec = embed_model.encode([u_query])
            D, I = vector_index.search(np.array(q_vec).astype('float32'), k=5)
            
            context = ""
            for idx in I[0]:
                if idx != -1:
                    match = library[idx]
                    context += f"\n[المستند: {match['file']}, صفحة: {match['page']}]\n{match['content'][:800]}\n"

            prompt = f"Act as a Senior Legal Advisor. Analysis must be in Arabic. Context: {context}\n\nQuery: {u_query}"
            response = model.generate_content(prompt)
            
            # Use the 'report-card' class to keep text clean and aligned
            st.markdown(f'<div class="report-card">{response.text}</div>', unsafe_allow_html=True)
            
            # Standard PDF Download (Latin-1 fallback)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            clean_text = response.text.encode('latin-1', 'ignore').decode('latin-1')
            pdf.multi_cell(0, 10, clean_text)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Legal_Report.pdf"><button style="width:100%; border-radius:12px; background-color: #28a745; color: white; padding: 10px; border: none; font-weight: bold;">📥 تحميل التقرير (PDF)</button></a>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"خطأ: {str(e)}")
