import streamlit as st
import os, fitz, json, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from fpdf import FPDF

# --- 1. THE "BRUTE FORCE" RTL INJECTION ---
st.set_page_config(page_title="المحقق القانوني", layout="centered")

st.markdown("""
    <style>
    /* Force EVERY element to align Right and use RTL direction */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* Target specifically the text inputs and markdown results */
    textarea, input, .stMarkdown, p, li, h1, h2, h3, label {
        direction: rtl !important;
        text-align: right !important;
    }

    /* Fix bullet points so they appear on the right */
    ul, ol {
        direction: rtl !important;
        text-align: right !important;
        margin-right: 20px !important;
        margin-left: 0px !important;
    }

    /* Mobile-First Action Button */
    .stButton > button {
        width: 100%;
        border-radius: 15px;
        height: 4em;
        background-color: #1A73E8;
        color: white;
        font-size: 18px;
        font-weight: bold;
    }

    /* The Results Card */
    .report-card {
        background: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border-right: 10px solid #1A73E8;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        color: #1a1a1a;
        margin-top: 25px;
        line-height: 1.8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ENGINE ---
@st.cache_resource
def load_engine():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_engine()
CORPUS_DIR = "documents"

@st.cache_data
def index_docs():
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

vector_index, library = index_docs()

# --- 3. THE MOBILE-STYLE INTERFACE ---
st.image("https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg", width=60)
st.title("المحقق القانوني الذكي")

# API and Settings directly on the page (Better for Mobile RTL)
with st.expander("🔑 إعدادات الوصول والأرشفة", expanded=False):
    api_key = st.text_input("مفتاح API الخاص بـ Gemini", type="password")
    if vector_index:
        st.success(f"تمت أرشفة {len(library)} صفحة بنجاح")
    if st.button("تحديث المكتبة"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Main Input
u_query = st.text_area("أدخل سؤالك القانوني أو Directive:", height=150, placeholder="مثال: لخص شروط الفسخ في كافة العقود المرفوعة...")
execute_analysis = st.button("تحليل الأدلة واستخراج الاستراتيجية ⚖️")

# --- 4. EXECUTION ---
if execute_analysis and api_key:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        with st.spinner("جاري فحص المستندات وبناء الرد القانوني..."):
            # Search logic
            q_vec = embed_model.encode([u_query])
            D, I = vector_index.search(np.array(q_vec).astype('float32'), k=5)
            
            context = ""
            for idx in I[0]:
                if idx != -1:
                    match = library[idx]
                    context += f"\n[المستند: {match['file']}, ص.{match['page']}]\n{match['content'][:800]}\n"

            # Strict Arabic Strategy Prompt
            prompt = f"""
            بصفتك مستشارًا قانونيًا أول، حلل الأدلة التالية باللغة العربية حصراً.
            الأدلة: {context}
            السؤال: {u_query}
            
            التنسيق المطلوب:
            1. ملخص تنفيذي.
            2. النظرية القانونية والاستراتيجية.
            3. النتائج المحددة مع ذكر [اسم الملف والصفحة].
            """
            response = model.generate_content(prompt)
            
            # Locked Card for RTL Results
            st.markdown(f'<div class="report-card">{response.text}</div>', unsafe_allow_html=True)
            
            # Simple Export
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            clean_text = response.text.encode('latin-1', 'ignore').decode('latin-1')
            pdf.multi_cell(0, 10, clean_text)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Analysis.pdf"><button style="width:100%; border-radius:15px; background-color: #28a745; color: white; padding: 15px; border: none; font-weight: bold; margin-top: 10px;">📥 تحميل التقرير (PDF)</button></a>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"حدث خطأ في النظام: {str(e)}")
