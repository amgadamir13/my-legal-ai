import streamlit as st
import os, fitz, json, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- 1. هندسة الواجهة (RTL للعربي و LTR للكود) ---
st.set_page_config(page_title="المحقق القانوني", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* تنسيق الصفحة العام - عربي */
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* استثناء خاص لمربعات إدخال الرموز أو المفاتيح التقنية لتظل LTR */
    input[type="password"], input[type="text"] {
        direction: ltr !important;
        text-align: left !important;
    }

    /* حاوية النتائج القانونية */
    .legal-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-right: 8px solid #1A73E8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        color: #1a1a1a;
        margin-top: 20px;
    }

    /* زر التشغيل - متوافق مع إبهام اليد في الموبايل */
    .stButton > button {
        width: 100%;
        border-radius: 50px;
        height: 3.5em;
        background: #1A73E8;
        color: white;
        font-weight: bold;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. المحرك التقني ---
@st.cache_resource
def setup_ai():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = setup_ai()
DOCS_PATH = "documents"

@st.cache_data
def process_docs():
    meta, texts = [], []
    if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)
    files = [f for f in os.listdir(DOCS_PATH) if f.lower().endswith(".pdf")]
    if not files: return None, None
    for f in files:
        path = os.path.join(DOCS_PATH, f)
        try:
            with fitz.open(path) as doc:
                for i, page in enumerate(doc):
                    content = page.get_text().strip()
                    if content:
                        meta.append({"file": f, "page": i+1, "text": content})
                        texts.append(content)
        except: continue
    if not texts: return None, None
    embeddings = embed_model.encode(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    return index, meta

vector_index, doc_library = process_docs()

# --- 3. الواجهة الأمامية ---
st.markdown('<center><img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg" width="50"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>المساعد القانوني الذكي</h2>", unsafe_allow_html=True)

# خانة المفتاح (ستظهر LTR تلقائياً لمنع الانعكاس)
api_key = st.text_input("Gemini API Key (Secret)", type="password", help="أدخل الكود السري الخاص بك هنا")

with st.expander("📂 حالة المكتبة القانونية"):
    if vector_index:
        st.success(f"تمت أرشفة {len(doc_library)} صفحة")
    else:
        st.error("لم يتم العثور على ملفات PDF")
    if st.button("تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

u_query = st.text_area("ما هو استفسارك القانوني؟", height=120)
analyze = st.button("تحليل المستندات الآن ⚖️")

# --- 4. التنفيذ الذكي ---
if analyze and api_key:
    genai.configure(api_key=api_key)
    try:
        # البحث التلقائي عن الموديل المتاح لتجنب خطأ 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-pro' if 'models/gemini-1.5-pro' in available_models else available_models[0]
        
        model = genai.GenerativeModel(target)
        
        with st.spinner("جاري استخراج الأدلة..."):
            # بحث سيمانتك (بالأبعاد)
            q_vec = embed_model.encode([u_query])
            D, I = vector_index.search(np.array(q_vec).astype('float32'), k=5)
            
            context = ""
            for idx in I[0]:
                if idx != -1:
                    m = doc_library[idx]
                    context += f"\n[المصدر: {m['file']}, ص.{m['page']}]\n{m['text'][:800]}\n"

            prompt = f"حلل كخبير قانوني وباللغة العربية. السياق: {context}\n\nالسؤال: {u_query}"
            response = model.generate_content(prompt)
            
            st.markdown(f'<div class="legal-card">{response.text}</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"تنبيه: {str(e)}")
