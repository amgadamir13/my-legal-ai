import streamlit as st
import os, fitz, json, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image # لدعم صور الأيفون

# --- 1. هندسة الواجهة المتطورة (Mobile-First) ---
st.set_page_config(page_title="المحقق القانوني الشامل", layout="centered")

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

# --- 2. محرك قراءة الصور والـ PDF (OCR Engine) ---
@st.cache_resource
def load_rag_engine():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_rag_engine()
DOCS_PATH = "documents"

@st.cache_data
def process_all_files():
    meta, texts = [], []
    if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)
    
    # قراءة كافة أنواع الملفات (PDF + صور)
    supported_extensions = ('.pdf', '.png', '.jpg', '.jpeg', '.heic')
    files = [f for f in os.listdir(DOCS_PATH) if f.lower().endswith(supported_extensions)]
    
    if not files: return None, None

    for f in files:
        path = os.path.join(DOCS_PATH, f)
        # إذا كان ملف PDF
        if f.lower().endswith('.pdf'):
            try:
                with fitz.open(path) as doc:
                    for i, page in enumerate(doc):
                        content = page.get_text().strip()
                        if content:
                            meta.append({"file": f, "page": i+1, "text": content})
                            texts.append(content)
            except: continue
        # إذا كان صورة (JPG/PNG) - نحتاج لـ Gemini لقراءتها لاحقاً أو استخراج نصها
        else:
            meta.append({"file": f, "page": "صورة", "text": f"مرفق صورة باسم {f}"})
            texts.append(f"هذا الملف صورة لمستند قانوني باسم {f}")
            
    if not texts: return None, None
    idx = faiss.IndexFlatL2(embed_model.encode(texts).shape[1])
    idx.add(np.array(embed_model.encode(texts)).astype('float32'))
    return idx, meta

vector_index, doc_library = process_all_files()

# --- 3. الواجهة الرئيسية ---
st.markdown('<center><img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg" width="50"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>نظام التدقيق القانوني (PDF + صور)</h2>", unsafe_allow_html=True)

api_key = st.text_input("Gemini API Key (Secret)", type="password")

with st.expander("📂 حالة المستندات والصور"):
    if vector_index:
        st.success(f"تم التعرف على {len(doc_library)} عنصر (PDF وصور)")
    else:
        st.error("لم يتم العثور على ملفات. تأكد من وضع الصور والـ PDF في مجلد documents")

u_query = st.text_area("أدخل استفسارك:", height=150)
analyze = st.button("تحليل المستندات والصور الآن ⚖️")

# --- 4. التحليل الذكي المزدوج (Multi-Modal) ---
if analyze and api_key:
    genai.configure(api_key=api_key)
    try:
        # اختيار الموديل (Pro يدعم الصور)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        with st.spinner("جاري قراءة الصور والنصوص وتحليلها..."):
            # البحث عن السياق
            q_vec = embed_model.encode([u_query])
            D, I = vector_index.search(np.array(q_vec).astype('float32'), k=5)
            
            # تجميع النصوص والصور للتحليل
            context_text = ""
            images_to_process = []
            
            for idx in I[0]:
                if idx != -1:
                    m = doc_library[idx]
                    if "صورة" in str(m['page']):
                        img_path = os.path.join(DOCS_PATH, m['file'])
                        images_to_process.append(Image.open(img_path))
                    context_text += f"\n[المصدر: {m['file']}, {m['page']}]\n{m['text']}\n"

            # إرسال البيانات لـ Gemini (نص + صور)
            prompt = f"""
            بصفتك خبيراً قانونياً، قم بتحليل الصور والنصوص المرفقة.
            مهمتك:
            1. قراءة النصوص المشوهة في الصور وترميمها قانونياً.
            2. تقديم تحليل استراتيجي بناءً على كل الأدلة المتاحة.
            3. تحديد أرقام الصفحات وأسماء ملفات الصور بدقة.
            
            السياق المستخرج: {context_text}
            السؤال: {u_query}
            """
            
            # إذا وجدت صور، نرسلها مع النص
            if images_to_process:
                response = model.generate_content([prompt] + images_to_process)
            else:
                response = model.generate_content(prompt)
            
            st.markdown(f'<div class="legal-card">{response.text}</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"خطأ: {str(e)}")
