import streamlit as st
import os, fitz, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image

# 1. إعدادات الواجهة (احترافية ومنظمة)
st.set_page_config(page_title="المستشار القانوني الذكي", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { direction: rtl; text-align: right; font-family: 'Cairo', sans-serif; }
    .stTextArea textarea { font-size: 1.1em !important; border-radius: 10px !important; }
    .legal-box { background-color: #ffffff; padding: 20px; border-radius: 15px; border-right: 8px solid #1e3a8a; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #1a1a1a; line-height: 1.8; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model_engine = get_model()
DIR = "documents"

def read_docs():
    data, raw_texts = [], []
    if not os.path.exists(DIR): os.makedirs(DIR)
    for f in os.listdir(DIR):
        if f.startswith('.'): continue
        path = os.path.join(DIR, f)
        try:
            if f.lower().endswith('.pdf'):
                with fitz.open(path) as doc:
                    for i, p in enumerate(doc):
                        t = p.get_text().strip()
                        if t:
                            data.append({"f": f, "p": i+1, "t": t, "type": "pdf"})
                            raw_texts.append(t)
            elif f.lower().endswith(('.jpg', '.jpeg', '.png')):
                data.append({"f": f, "p": "صورة", "t": f"مستند صوري {f}", "type": "image"})
                raw_texts.append(f"صورة مستند {f}")
        except: continue
    return data, raw_texts

# --- الواجهة ---
st.title("⚖️ المستشار القانوني (نسخة الحلول الذكية)")
st.write("خبير في القانون المصري، يدمج بين مستنداتك وذكاء 'محامي الشارع' المتمرس.")

# ميزة الملء التلقائي للمفتاح
key = st.text_input("المفتاح السري (Gemini Key):", type="password", autocomplete="current-password")

query = st.text_area("اشرح الموقف القانوني أو السؤال:", placeholder="اكتب سؤالك هنا بوضوح...", height=150)

if st.button("تحليل الاستراتيجية القانونية 🚀"):
    if not key:
        st.error("برجاء إدخال مفتاح الـ API أولاً.")
    else:
        try:
            genai.configure(api_key=key)
            
            # --- حل مشكلة الـ 404 تلقائياً ---
            # البحث عن أفضل موديل متاح يدعم توليد المحتوى
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # نفضل Pro، إذا لم يوجد نأخذ Flash، إذا لم يوجد نأخذ أول واحد متاح
            selected_model = next((m for m in available_models if "1.5-pro" in m), 
                                 next((m for m in available_models if "1.5-flash" in m), available_models[0]))
            
            ai = genai.GenerativeModel(selected_model)
            
            lib, texts = read_docs()
            context = ""
            imgs = []
            
            if lib:
                with st.spinner("جاري فحص المستندات الملحقة..."):
                    vecs = model_engine.encode(texts)
                    index = faiss.IndexFlatL2(vecs.shape[1])
                    index.add(np.array(vecs).astype('float32'))
                    _, I = index.search(np.array(model_engine.encode([query])).astype('float32'), k=3)
                    
                    for idx in I[0]:
                        if idx < len(lib):
                            item = lib[idx]
                            if item['type'] == "image":
                                img = Image.open(os.path.join(DIR, item['f'])).convert("RGB")
                                imgs.append(img)
                            context += f"\n[دليل من ملف: {item['f']} - صفحة {item['p']}]\n{item['t']}\n"

            # توجيه العقل الذكي (System Instruction)
            prompt = f"""
            بصفتك مستشاراً قانونياً مصرياً داهية، حلل الآتي بذكاء وخبرة عملية:
            
            1. ابدأ برؤية قانونية عامة طبقاً للقوانين المصرية المعمول بها.
            2. ادمج المعلومات من المستندات التالية (إن وجدت): {context}
            3. فكر في 'مخارج' أو 'ثغرات' أو 'تحذيرات' قد لا ينتبه لها المبتدئ.
            4. اجعل الإجابة مرتبة في نقاط واضحة.
            
            سؤال المستخدم: {query}
            """
            
            with st.spinner(f"جاري التحليل باستخدام {selected_model}..."):
                res = ai.generate_content([prompt] + imgs)
                st.success("تم تحليل الموقف بنجاح!")
                st.markdown(f"<div class='legal-box'>{res.text}</div>", unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")
            st.info("نصيحة: تأكد أن مفتاح الـ API صحيح وأن لديك صلاحية الوصول لموديلات Gemini.")
