import streamlit as st
import os, fitz, json, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image

# --- 1. إعدادات الأمان والمظهر (RTL كامل) ---
st.set_page_config(page_title="المحقق القانوني", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], .stApp {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    /* جعل خانة المفتاح مخفية وآمنة */
    input[type="password"] { direction: ltr !important; text-align: left !important; }
    
    .report-card {
        background: white; padding: 20px; border-radius: 15px;
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
    
    # دعم الصور والـ PDF
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
            # تمييز الصور ليقوم Gemini بقراءتها لاحقاً
            meta.append({"file": f, "page": "صورة التقطت بالأيفون", "text": f"مستند صوري: {f}", "type": "image"})
            texts.append(f"صورة مستند قانوني: {f}")
            
    if not texts: return None, None
    idx = faiss.IndexFlatL2(embed_model.encode(texts).shape[1])
    idx.add(np.array(embed_model.encode(texts)).astype('float32'))
    return idx, meta

vector_index, library = load_all_documents()

# --- 3. الواجهة (بسيطة جداً لمستخدمي الأيفون) ---
st.markdown('<center><img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002.svg" width="60"></center>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>المساعد القانوني الذكي</h2>", unsafe_allow_html=True)

# خانة المفتاح السرية - لن يظهر ما تكتبه
api_key = st.text_input("أدخل مفتاحك السري هنا (Gemini API Key):", type="password")

if not api_key:
    st.info("💡 يرجى وضع المفتاح السري في الخانة أعلاه للبدء.")
else:
    st.success("✅ المفتاح متصل. يمكنك الآن البدء بالتحليل.")

with st.expander("📂 حالة الملفات المرفوعة"):
    if vector_index:
        st.write(f"تم فحص {len(library)} ملفات وصور بنجاح.")
    else:
        st.error("لم يتم العثور على أي صور أو ملفات في مجلد documents.")

u_query = st.text_area("ماذا تريد أن تعرف من هذه المستندات؟", height=150, placeholder="اكتب سؤالك هنا...")

# الزر الكبير للتحليل
if st.button("بدء التحليل الاستراتيجي ⚖️", use_container_width=True):
    if not api_key:
        st.error("يرجى إدخال المفتاح السري أولاً.")
    else:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            with st.spinner("جاري قراءة الصور والنصوص..."):
                # البحث عن المعلومات ذات الصلة
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

                # نطلب من الذكاء الاصطناعي "فهم" الصور والترميم
                prompt = f"حلل الصور والنصوص التالية كخبير قانوني وبالعربية. السياق: {context_text}\nالسؤال: {u_query}"
                
                if images:
                    response = model.generate_content([prompt] + images)
                else:
                    response = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(f'<div class="report-card">{response.text}</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"حدث خطأ: تأكد من صحة المفتاح السري أو اتصال الإنترنت. (التفاصيل: {str(e)})")
