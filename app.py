import streamlit as st
import os, fitz, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image

# --- 1. واجهة المستخدم الاحترافية ---
st.set_page_config(page_title="المحقق القانوني", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    .legal-card {
        background: white; padding: 25px; border-radius: 15px;
        border-right: 10px solid #1A73E8;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-top: 20px;
    }
    .error-tag { color: #d32f2f; font-size: 0.8em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك المعالجة "المرن" ---
@st.cache_resource
def load_engine():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_engine()
DOCS_DIR = "documents"

@st.cache_data
def load_and_fix_docs():
    meta, texts = [], []
    if not os.path.exists(DOCS_DIR): os.makedirs(DOCS_PATH)
    
    # جلب كافة الملفات
    all_files = [f for f in os.listdir(DOCS_DIR) if not f.startswith('.')]
    
    for f in all_files:
        path = os.path.join(DOCS_DIR, f)
        try:
            # معالجة الـ PDF
            if f.lower().endswith('.pdf'):
                with fitz.open(path) as doc:
                    for i, page in enumerate(doc):
                        t = page.get_text().strip()
                        if t:
                            meta.append({"file": f, "page": i+1, "text": t, "type": "pdf"})
                            texts.append(t)
            # معالجة الصور بكافة أنواعها
            elif f.lower().endswith(('.png', '.jpg', '.jpeg', '.mpo', '.heic', '.webp')):
                meta.append({"file": f, "page": "صورة", "text": f"مستند مصور: {f}", "type": "image"})
                texts.append(f"مستند مصور: {f}")
            else:
                continue # تجاهل الملفات غير المدعومة دون تعطيل النظام
        except Exception:
            # إذا فشل ملف واحد، نكمل للباقي دون توقف
            st.warning(f"⚠️ تعذر قراءة الملف: {f} - سيتم تخطيه.")
            continue
            
    if not texts: return None, None
    idx = faiss.IndexFlatL2(embed_model.encode(texts).shape[1])
    idx.add(np.array(embed_model.encode(texts)).astype('float32'))
    return idx, meta

vector_index, library = load_and_fix_docs()

# --- 3. الواجهة ---
st.markdown('<center><img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg" width="60"></center>', unsafe_allow_html=True)
st.title("المساعد القانوني الذكي")

api_key = st.text_input("أدخل مفتاح Gemini السري:", type="password")

u_query = st.text_area("ما هو استفسارك القانوني؟", height=150)

if st.button("تحليل المستندات الآن ⚖️", use_container_width=True):
    if not api_key:
        st.error("يرجى إدخال المفتاح أولاً")
    elif not vector_index:
        st.error("لا توجد ملفات صالحة للتحليل في مجلد documents.")
    else:
        genai.configure(api_key=api_key)
        try:
            # اختيار الموديل التلقائي
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            m_id = next((m for m in models if '1.5-pro' in m), models[0])
            model = genai.GenerativeModel(m_id)
            
            with st.spinner("جاري تحليل الملفات المتاحة..."):
                q_vec = embed_model.encode([u_query])
                D, I = vector_index.search(np.array(q_vec).astype('float32'), k=5)
                
                context = ""
                images = []
                for idx in I[0]:
                    if idx != -1:
                        m = library[idx]
                        if m['type'] == "image":
                            try:
                                img = Image.open(os.path.join(DOCS_DIR, m['file'])).convert("RGB")
                                images.append(img)
                            except:
                                st.error(f"❌ مشكلة في الصورة: {m['file']}")
                                continue
                        context += f"\n[{m['file']}, {m['page']}]\n{m['text']}\n"

                prompt = f"حلل كخبير قانوني وبالعربية. السياق: {context}\nالسؤال: {u_query}"
                response = model.generate_content([prompt] + images if images else prompt)
                
                st.markdown("---")
                st.markdown(f'<div class="legal-card">{response.text}</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء التحليل: {str(e)}")
