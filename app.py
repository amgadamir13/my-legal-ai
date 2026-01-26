import streamlit as st
import os, fitz, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image

# --- 1. إعدادات الخصوصية والواجهة (RTL) ---
st.set_page_config(page_title="المحقق القانوني", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], .stApp {
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك قراءة الملفات والصور ---
@st.cache_resource
def load_ai_engine():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_ai_engine()
DOCS_DIR = "documents"

@st.cache_data
def load_all_documents():
    meta, texts = [], []
    if not os.path.exists(DOCS_DIR): os.makedirs(DOCS_DIR)
    valid_files = [f for f in os.listdir(DOCS_DIR) if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))]
    if not valid_files: return None, None

    for f in valid_files:
        path = os.path.join(DOCS_DIR, f)
        if f.lower().endswith('.pdf'):
            try:
                with fitz.open(path) as doc:
                    for i, page in enumerate(doc):
                        t = page.get_text().strip()
                        if t:
                            meta.append({"file": f, "page": i+1, "text": t, "type": "pdf"})
                            texts.append(t)
            except: continue
        else:
            meta.append({"file": f, "page": "صورة التقطت بالأيفون", "text": f"مستند صوري: {f}", "type": "image"})
            texts.append(f"صورة مستند قانوني: {f}")
            
    if not texts: return None, None
    idx = faiss.IndexFlatL2(embed_model.encode(texts).shape[1])
    idx.add(np.array(embed_model.encode(texts)).astype('float32'))
    return idx, meta

vector_index, library = load_all_documents()

# --- 3. الواجهة الأمامية ---
st.markdown('<center><img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg" width="60"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>المساعد القانوني الذكي</h2>", unsafe_allow_html=True)

# خانة المفتاح السرية - اضغط Done في الكيبورد بعد اللصق
api_key = st.text_input("أدخل مفتاحك السري (Secret Key) هنا:", type="password", help="قم بلصق الكود واضغط Done")

if api_key:
    st.success("✅ تم تفعيل المفتاح. النظام جاهز الآن.")
else:
    st.info("💡 الصق المفتاح السري بالأعلى للبدء.")

with st.expander("📂 حالة المستندات"):
    if vector_index:
        st.write(f"تم تحميل {len(library)} ملفات بنجاح.")
    else:
        st.error("لم يتم العثور على ملفات في مجلد documents.")

u_query = st.text_area("ما هو استفسارك القانوني؟", height=150)

# زر التحليل - هذا هو الزر الرئيسي للتنفيذ
if st.button("تحليل الأدلة ⚖️", use_container_width=True):
    if not api_key:
        st.error("يجب إدخال المفتاح السري أولاً.")
    else:
        genai.configure(api_key=api_key)
        try:
            # --- ميزة البحث التلقائي عن الموديل المتاح ---
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # نختار موديل 1.5 pro إذا وجد، وإلا نختار أول موديل متاح
            model_id = next((m for m in available_models if '1.5-pro' in m), 
                           next((m for m in available_models if '1.5' in m), available_models[0]))
            
            model = genai.GenerativeModel(model_id)
            
            with st.spinner("جاري قراءة الملفات وتحليلها..."):
                q_vec = embed_model.encode([u_query])
                D, I = vector_index.search(np.array(q_vec).astype('float32'), k=5)
                
                context_text = ""
                images = []
                for idx in I[0]:
                    if idx != -1:
                        m = library[idx]
                        if m['type'] == "image":
                            img_path = os.path.join(DOCS_DIR, m['file'])
                            images.append(Image.open(img_path))
                        context_text += f"\n[المستند: {m['file']}, {m['page']}]\n{m['text']}\n"

                prompt = f"حلل كخبير قانوني وبالعربية. الأدلة: {context_text}\nالسؤال: {u_query}"
                
                if images:
                    response = model.generate_content([prompt] + images)
                else:
                    response = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(f'<div class="legal-card">{response.text}</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"تنبيه: {str(e)}")
