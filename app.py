import streamlit as st
import os, fitz, json, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from fpdf import FPDF

# --- 1. MOBILE-FIRST & ARABIC RTL STYLING ---
st.set_page_config(page_title="المحقق القانوني الذكي", layout="centered")

# Enterprise CSS for Arabic Mobile UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    /* Mobile-friendly buttons */
    .stButton > button {
        width: 100%;
        border-radius: 25px;
        height: 3.5em;
        background-color: #1A73E8;
        color: white;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    /* Card style for results */
    .report-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-right: 5px solid #1A73E8;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        color: #333;
    }
    .gemini-logo { display: block; margin: 0 auto 10px auto; width: 60px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE INTELLIGENCE ENGINE ---
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

# --- 3. MOBILE UI FRONT-END ---
# Gemini Branding
st.markdown('<img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg" class="gemini-logo">', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #1A73E8;'>المحقق القانوني الذكي</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 0.9em; color: #666;'>نظام تحليل الأدلة واستخراج الاستراتيجيات القانونية</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("مفتاح API (Gemini)", type="password")
    if vector_index:
        st.success(f"تمت أرشفة {len(library)} صفحة قانونية")
    else:
        st.warning("يرجى رفع ملفات PDF في مجلد documents")
    if st.button("تحديث قاعدة البيانات"):
        st.cache_data.clear()
        st.rerun()

# User Input - Mobile Friendly
u_query = st.text_area("ما هو استفسارك القانوني؟", placeholder="اكتب سؤالك هنا ليقوم المحقق الذكي بالبحث في الملفات...", height=120)
execute_analysis = st.button("بدء التحليل الاستراتيجي ⚖️")

# --- 4. THE ANALYSIS & PDF EXPORT ---
if execute_analysis and api_key:
    genai.configure(api_key=api_key)
    try:
        # Selection of best available model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        with st.spinner("جاري فحص المستندات وبناء التقرير..."):
            # Semantic Search
            q_vec = embed_model.encode([u_query])
            D, I = vector_index.search(np.array(q_vec).astype('float32'), k=5)
            
            context = ""
            for idx in I[0]:
                if idx != -1:
                    match = library[idx]
                    context += f"\n[المستند: {match['file']}, صفحة: {match['page']}]\n{match['content'][:800]}\n"

            # Arabic-First Strategic Prompt
            prompt = f"""
            بصفتك مستشارًا قانونيًا خبيرًا، قم بتحليل الأدلة التالية باللغة العربية.
            يجب أن يكون الرد احترافيًا ومنظمًا كالتالي:
            1. الملخص التنفيذي: (رؤية سريعة للموقف).
            2. النظرية القانونية: (الاستراتيجية المقترحة بناءً على النصوص).
            3. تفاصيل الأدلة: (قائمة بالنتائج مع ذكر اسم الملف ورقم الصفحة [ملف، صفحة]).
            
            الأدلة المستخرجة: {context}
            السؤال: {u_query}
            """
            
            response = model.generate_content(prompt)
            
            # Displaying as a professional "Card"
            st.markdown("---")
            st.markdown(f'<div class="report-card">{response.text}</div>', unsafe_allow_html=True)
            
            # Easy Download Button
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            # Standard PDF cleanup
            clean_text = response.text.encode('latin-1', 'ignore').decode('latin-1')
            pdf.multi_cell(0, 10, clean_text)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_bytes).decode()
            
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Legal_Report.pdf"><button style="background-color: #28a745;">📥 تحميل التقرير المعتمد (PDF)</button></a>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"خطأ في النظام: {str(e)}")
