import streamlit as st
import os, fitz, base64
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from PIL import Image

# 1. إعداد الواجهة لتكون احترافية ومنظمة (سهلة للعين)
st.set_page_config(page_title="المستشار القانوني الذكي", layout="centered")

# تنسيق المتصفح ليدعم اللغة العربية والخطوط المريحة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { direction: rtl; text-align: right; font-family: 'Cairo', sans-serif; }
    .stTextArea textarea { font-size: 1.1em !important; }
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

# --- الواجهة الجديدة ---
st.title("⚖️ المستشار القانوني المصري الذكي")
st.info("مرحباً بك. أنا مستشارك القانوني، أدمج بين نصوص ملفاتك وبين خبرتي العميقة بالقانون المصري لإيجاد أفضل الحلول.")

# ميزة الملء التلقائي للمفتاح (Auto-fill)
# أضفنا وسوم HTML تجعل المتصفح يتعرف عليه ككلمة مرور محفوظة
key = st.text_input("المفتاح السري (Gemini Key):", type="password", help="سيقوم المتصفح باقتراح المفتاح إذا قمت بحفظه مسبقاً", autocomplete="current-password")

query = st.text_area("اشرح قضيتك أو سؤالك هنا:", placeholder="مثلاً: ما هي الثغرات الممكنة في هذا العقد؟", height=150)

if st.button("تحليل قانوني معمق 🚀"):
    if not key:
        st.error("برجاء إدخال مفتاح Gemini للاستمرار.")
    else:
        genai.configure(api_key=key)
        lib, texts = read_docs()
        
        try:
            ai = genai.GenerativeModel('gemini-1.5-pro')
            
            context = ""
            imgs = []
            
            # إذا وجدت ملفات، ابحث فيها لتعزيز الإجابة
            if lib:
                with st.spinner("جاري استحضار الأدلة من ملفاتك..."):
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
                            context += f"\n[من مستنداتك: {item['f']}]\n{item['t']}\n"

            # توجيه Gemini ليكون "محامي مصري داهية"
            system_instruction = f"""
            أنت الآن 'المستشار القانوني'، محامٍ مصري خبير جداً، مطلع على كافة القوانين المصرية (مدني، جنائي، نقض، إلخ) وتاريخها.
            شخصيتك: ذكي، عملي، تبحث عن الحلول غير التقليدية، وتعرف كيف تتفادى المعوقات الإجرائية في مصر.
            المهمة:
            1. حلل السؤال بناءً على خبرتك القانونية العامة أولاً.
            2. استخدم النصوص المرفقة من الملفات (إن وجدت) لتعزيز الإجابة بالدليل.
            3. قدم حلولاً ذكية ومسارات بديلة (استراتيجيات قانونية).
            
            المعطيات من الملفات: {context}
            سؤال المستخدم: {query}
            """
            
            with st.spinner("جاري صياغة الاستراتيجية القانونية..."):
                res = ai.generate_content([system_instruction] + imgs)
                st.success("تم الانتهاء من التحليل!")
                
                # عرض النتيجة بشكل منظم وجميل
                st.markdown(f"""
                <div style='background-color: #ffffff; padding: 25px; border-radius: 15px; border-right: 8px solid #1e3a8a; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); color: #1a1a1a;'>
                    {res.text}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"عذراً، حدث خطأ تقني: {str(e)}")
