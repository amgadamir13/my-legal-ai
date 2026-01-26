import streamlit as st
import os, fitz, json, re, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from fpdf import FPDF

# --- 1. MOBILE & RTL CUSTOMIZATION ---
st.set_page_config(page_title="المحقق القانوني الذكي", layout="centered")

# Custom CSS for Arabic UI and Mobile Feel
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stTextArea textarea { text-align: right; direction: rtl; }
    .stButton button { width: 100%; border-radius: 20px; height: 3em; background-color: #004a99; color: white; }
    .main-header { font-size: 24px; font-weight: bold; color: #004a99; text-align: center; margin-bottom: 20px; }
    .card { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE SETUP ---
@st.cache_resource
def load_brain_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_brain_model()
DOCS_FOLDER = "documents"

@st.cache_data
def build_index():
    metadata, texts = [], []
    if not os.path.exists(DOCS_FOLDER): os.makedirs(DOCS_FOLDER)
    files = [f for f in os.listdir(DOCS_FOLDER) if f.lower().endswith(".pdf")]
    if not files: return None, None
    for f in files:
        path = os.path.join(DOCS_FOLDER, f)
        try:
            with fitz.open(path) as doc:
                for i, page in enumerate(doc):
                    content = page.get_text().strip()
                    if content:
                        metadata.append({"file": f, "page": i+1, "text": content})
                        texts.append(content)
        except: continue
    if not texts: return None, None
    embeddings = embed_model.encode(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    return index, metadata

vector_index, doc_library = build_index()

# --- 3. MOBILE INTERFACE (ARABIC) ---
# Gemini Logo and Header
st.image("https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg", width=50)
st.markdown('<div class="main-header">المساعد القانوني الذكي (Gemini)</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("مفتاح API الخاص بـ Gemini", type="password")
    st.divider()
    if vector_index:
        st.success(f"تمت أرشفة {len(doc_library)} صفحة بنجاح")
    else:
        st.error("المكتبة فارغة")
    if st.button("تحديث المكتبة"):
        st.cache_data.clear()
        st.rerun()

u_query = st.text_area("أدخل استفسارك القانوني هنا:", placeholder="مثال: لخص مخاطر المسؤولية في هذه العقود...", height=150)
audit_btn = st.button("تحليل المستندات الآن ⚖️")

# --- 4. EXECUTION ---
if audit_btn and api_key:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        with st.spinner("جاري تحليل الأدلة وبناء الاستراتيجية..."):
            query_vec = embed_model.encode([u_query])
            distances, indexes = vector_index.search(np.array(query_vec).astype('float32'), k=5)
            
            context = ""
            for idx in indexes[0]:
                if idx != -1:
                    m = doc_library[idx]
                    context += f"\n[المستند: {m['file']}, صفحة.{m['page']}]\n{m['text'][:1000]}\n"

            # Strategic Prompt in Arabic
            prompt = f"""
            بصفتك شريكًا قانونيًا أول، قم بتحليل الأدلة التالية باللغة العربية.
            يجب أن يتضمن الرد:
            1. ملخص تنفيذي للموقف.
            2. تحليل الاستراتيجية القانونية.
            3. النتائج التفصيلية مع الإشارة للمستندات والصفحات [المستند، الصفحة].
            
            الأدلة: {context}
            السؤال: {u_query}
            """
            response = model.generate_content(prompt)
            
            st.markdown("---")
            st.markdown(f'<div class="card">{response.text}</div>', unsafe_allow_html=True)
            
            # PDF Export (Arabic support in PDF is complex, so we use a standard clean format)
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('Arial', '', 'Arial.ttf', uni=True) # Note: Requires a .ttf font file for Arabic
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, response.text.encode('latin-1', 'ignore').decode('latin-1')) # Standard fallback
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            b64_pdf = base64.b64encode(pdf_bytes).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" download="Report.pdf"><button style="width:100%; padding:10px; background-color:#28a745; color:white; border:none; border-radius:15px;">📥 تحميل التقرير (PDF)</button></a>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"حدث خطأ: {str(e)}")
