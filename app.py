# -*- coding: utf-8 -*-
import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF
import io
import os
import time
import re
from typing import List
from datetime import datetime

# =============================================
# 1. PAGE CONFIGURATION & STYLING
# =============================================
st.set_page_config(
    page_title="Strategic War Room Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Arabic styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
    
    /* Base RTL Styling */
    html, body, [data-testid="stAppViewContainer"], 
    [data-testid="stMarkdownContainer"], 
    [data-testid="stVerticalBlock"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }
    
    /* Fix vertical text issue */
    * {
        word-break: normal !important;
        white-space: normal !important;
        line-height: 1.8 !important;
    }
    
    /* Message Boxes */
    .msg-box { 
        padding: 25px; 
        border-radius: 18px; 
        margin-bottom: 25px; 
        line-height: 1.8; 
        border-right: 12px solid; 
        box-shadow: 0 6px 20px rgba(0,0,0,0.1); 
        width: 100% !important;
        transition: transform 0.3s ease;
    }
    
    .msg-box:hover {
        transform: translateX(-5px);
    }
    
    .user-style { 
        border-color: #1e3a8a; 
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        color: #1e3a8a; 
    }
    
    .ai-style { 
        border-color: #10b981; 
        background: linear-gradient(135deg, #f0fdf4 0%, #d1fae5 100%);
        color: #064e3b; 
    }
    
    .legal { border-color: #3b82f6; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); }
    .psych { border-color: #8b5cf6; background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%); }
    .strat { border-color: #f59e0b; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); }
    
    /* Finding Cards */
    .finding-card {
        background: #ffffff; 
        padding: 30px; 
        border-radius: 18px;
        margin-bottom: 25px; 
        border-right: 10px solid #cbd5e1; 
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        width: 100% !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Button Styling */
    .stButton > button {
        width: 100%;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 16px;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    /* File Uploader Styling */
    .stFileUploader > div {
        border: 2px dashed #4f46e5;
        border-radius: 12px;
        padding: 20px;
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# =============================================
# 2. ENHANCED FUNCTIONS
# =============================================

@st.cache_data(show_spinner=False)
def normalize_arabic_text(text: str) -> str:
    """Enhanced Arabic text normalization"""
    if not text:
        return ""
    
    # Remove special characters
    text = re.sub(r'[\u200b-\u200f\u202a-\u202e]', '', text)
    
    # Normalize Arabic letters
    replacements = {
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
        'ة': 'ه',
        '\u064b': '', '\u064c': '', '\u064d': '',  # Remove diacritics
        '\u064e': '', '\u064f': '', '\u0650': '',
        '\u0651': '', '\u0652': ''
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Fix spacing issues
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(?<=[\u0600-\u06FF])\s*\n\s*(?=[\u0600-\u06FF])', ' ', text)
    
    return text.strip()

def validate_pdf_file(file):
    """Validate uploaded PDF files"""
    if file.type != "application/pdf":
        return False, "الملف ليس بصيغة PDF"
    
    if file.size == 0:
        return False, "الملف فارغ"
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        return False, "حجم الملف كبير جداً (الحد الأقصى 10MB)"
    
    return True, ""

@st.cache_data(show_spinner=False)
def extract_text_from_pdf(file_bytes, max_pages=50):
    """Extract text from PDF with caching"""
    try:
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for i, page in enumerate(doc):
                if i >= max_pages:  # Limit pages for performance
                    text += "\n[تم اقتصار التحليل على أول 50 صفحة للملف الكبير]"
                    break
                text += page.get_text() + "\n"
        return normalize_arabic_text(text)
    except Exception as e:
        return f"خطأ في قراءة الملف: {str(e)}"

def get_text_from_files(files):
    """Process multiple files and extract text"""
    if not files:
        return ""
    
    all_text = []
    progress_bar = st.progress(0)
    
    for i, file in enumerate(files):
        is_valid, error_msg = validate_pdf_file(file)
        
        if not is_valid:
            st.warning(f"تم تخطي الملف {file.name}: {error_msg}")
            continue
            
        try:
            with st.spinner(f"جاري معالجة {file.name}..."):
                file.seek(0)
                text = extract_text_from_pdf(file.read())
                if text:
                    all_text.append(f"--- ملف: {file.name} ---\n{text}\n")
        except Exception as e:
            st.error(f"خطأ في معالجة {file.name}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(files))
    
    progress_bar.empty()
    return "\n".join(all_text)

def validate_api_key(api_key):
    """Basic API key validation"""
    if not api_key or len(api_key.strip()) < 20:
        return False, "مفتاح API غير صالح (يجب أن يكون 20 حرفاً على الأقل)"
    return True, ""

# =============================================
# 3. PROMPT TEMPLATES
# =============================================

PROMPT_TEMPLATES = {
    "legal": """
    أنت خبير قانوني محترف. قم بتحليل الوضع التالي بدقة واحترافية:
    
    📁 **الملفات والحقائق المتوفرة:**
    {vault_text}
    
    ⚔️ **ادعاءات الطرف الآخر:**
    {opponent_text}
    
    ❓ **السؤال أو الموقف المطلوب تحليله:**
    {user_query}
    
    **🎯 المطلوب منك:**
    1. **التقييم القانوني**: حدد الجوانب القانونية الرئيسية
    2. **نقاط القوة والضعف**: بين نقاط القوة في موقفنا ونقاط الضعف في موقف الخصم
    3. **السوابق القضائية**: اقترح سوابق قانونية مشابهة (إن أمكن)
    4. **التوصيات العملية**: قدم خطوات عملية يمكن اتخاذها
    
    **🔍 ملاحظة**: كن دقيقاً وواقعياً في التحليل. تجنب التفاؤل غير المبرط.
    """,
    
    "psychological": """
    أنت خبير في علم النفس القانوني والتفاوض. قم بتحليل الجوانب النفسية التالية:
    
    📁 **المعلومات المتوفرة:**
    {vault_text}
    
    ⚔️ **موقف الخصم:**
    {opponent_text}
    
    ❓ **المشكلة المطروحة:**
    {user_query}
    
    **🧠 جوانب التحليل النفسي:**
    1. **الدوافع والنيّات**: ما الذي يدفع الطرفين؟
    2. **نقاط الضغط النفسي**: أين توجد نقاط الضعف العاطفية؟
    3. **استراتيجيات الإقناع**: كيف يمكن التأثير على الطرف الآخر؟
    4. **لغة الجسد واللفظ**: ما الرسائل غير المعلنة؟
    5. **نصائح للتفاوض**: تقنيات فعالة للتواصل
    
    **💡 تذكر**: التركيز على الجوانب العملية القابلة للتطبيق.
    """,
    
    "strategic": """
    أنت استراتيجي قانوني محترف. قم بتطوير خطة تكتيكية شاملة:
    
    📁 **مواردنا:**
    {vault_text}
    
    ⚔️ **تهديدات الخصم:**
    {opponent_text}
    
    🎯 **الهدف الاستراتيجي:**
    {user_query}
    
    **⚔️ مكونات الخطة الاستراتيجية:**
    1. **المفاجآت التكتيكية**: خطوات غير متوقعة يمكن اتخاذها
    2. **نقاط التحكم**: أين تتمحور السيطرة في الموقف؟
    3. **التحركات المضادة**: كيف نرد على تحركات الخصم؟
    4. **الجدول الزمني**: تسلسل زمني مقترح للتحركات
    5. **سيناريوهات الطوارئ**: ماذا لو فشلت الخطة أ؟
    
    **🚀 كن مبتكراً وجريئاً**: لا تخف من اقتراح حلول غير تقليدية.
    """
}

# =============================================
# 4. SESSION STATE INITIALIZATION
# =============================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "analysis_count" not in st.session_state:
    st.session_state.analysis_count = 0

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0

# =============================================
# 5. SIDEBAR CONFIGURATION
# =============================================

with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🛡️ مركز القيادة الاستراتيجي</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    # API Configuration
    st.subheader("🔑 الإعدادات الفنية")
    
    # Try to get API key from secrets first
    try:
        default_api_key = st.secrets["GEMINI_API_KEY"]
        api_key = st.text_input("مفتاح Gemini API:", value=default_api_key, type="password")
    except:
        api_key = st.text_input("مفتاح Gemini API:", type="password")
    
    model_name = st.selectbox(
        "اختر نموذج الذكاء الاصطناعي:",
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    )
    
    # File Upload Sections
    st.markdown("---")
    st.subheader("📁 إدارة الوثائق")
    
    with st.expander("📂 قبو الحقائق (Vault)", expanded=True):
        v_files = st.file_uploader(
            "رفع وثائقنا الداعمة:",
            type=["pdf"],
            accept_multiple_files=True,
            key="vault_files",
            help="يمكنك رفع عدة ملفات PDF تحتوي على الأدلة والوثائق الداعمة"
        )
    
    with st.expander("⚔️ ملفات الخصم (Opponent)", expanded=True):
        o_files = st.file_uploader(
            "رفع وثائق الخصم:",
            type=["pdf"],
            accept_multiple_files=True,
            key="opponent_files",
            help="رفع وثائق وادعاءات الطرف الآخر"
        )
    
    # Analysis Settings
    st.markdown("---")
    st.subheader("⚙️ إعدادات التحليل")
    
    max_context_length = st.slider(
        "الحد الأقصى للنص المعالج (كلمة):",
        min_value=1000,
        max_value=10000,
        value=5000,
        step=500
    )
    
    # Management Tools
    st.markdown("---")
    st.subheader("🛠️ أدوات الإدارة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ تفريغ الذاكرة", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.analysis_count = 0
            st.rerun()
    
    with col2:
        if st.button("📊 عرض الإحصائيات", use_container_width=True):
            st.info(f"عدد التحليلات المنفذة: {st.session_state.analysis_count}")
    
    # App Info
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 10px;'>
    <small>Strategic War Room Pro v2.0</small><br>
    <small>Powered by Gemini AI</small>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# 6. MAIN INTERFACE
# =============================================

st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>⚖️ Strategic War Room Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-size: 18px;'>منصة التحليل القانوني والنفسي والاستراتيجي المتكاملة</p>", unsafe_allow_html=True)

# Quick Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("عدد التحليلات", st.session_state.analysis_count)
with col2:
    st.metric("الملفات المرفوعة", len(v_files or []) + len(o_files or []))
with col3:
    st.metric("آخر تحديث", datetime.now().strftime("%H:%M"))

# Main Analysis Form
with st.form("war_room_form", clear_on_submit=False):
    st.subheader("🎯 ابدأ التحليل")
    
    user_query = st.text_area(
        "**وصف الموقف الحالي:**",
        height=150,
        placeholder="صِف الموقف القانوني أو المشكلة المطروحة بتفصيل دقيق...",
        help="كلما كان الوصف أكثر تفصيلاً، كان التحليل أدق وأكثر فائدة"
    )
    
    st.markdown("**اختر نوع التحليل:**")
    cols = st.columns(3)
    
    with cols[0]:
        btn_L = st.form_submit_button(
            "⚖️ التحليل القانوني",
            help="تحليل الجوانب القانونية والنقاط القانونية",
            use_container_width=True
        )
        if btn_L:
            analysis_type = "legal"
            label = "⚖️ القانوني"
            style_class = "legal"
    
    with cols[1]:
        btn_P = st.form_submit_button(
            "🧠 التحليل النفسي",
            help="تحليل الجوانب النفسية والدوافع والسلوك",
            use_container_width=True
        )
        if btn_P:
            analysis_type = "psychological"
            label = "🧠 النفسي"
            style_class = "psych"
    
    with cols[2]:
        btn_S = st.form_submit_button(
            "🧨 التحليل الاستراتيجي",
            help="تطوير خطط تكتيكية واستراتيجيات متقدمة",
            use_container_width=True
        )
        if btn_S:
            analysis_type = "strategic"
            label = "🧨 الداهية"
            style_class = "strat"

# =============================================
# 7. EXECUTION LOGIC
# =============================================

if (btn_L or btn_P or btn_S) and user_query:
    # Rate limiting check
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 2:
        st.warning("⏳ الرجاء الانتظار ثانيتين بين كل طلب")
        st.stop()
    
    st.session_state.last_request_time = current_time
    
    # API Key Validation
    is_valid_key, key_error = validate_api_key(api_key)
    if not is_valid_key:
        st.error(f"⚠️ {key_error}")
        st.stop()
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4000,
            }
        )
        
        # Process files with progress
        with st.spinner("📂 جاري معالجة الوثائق المرفوعة..."):
            vault_text = get_text_from_files(v_files)[:max_context_length]
            opponent_text = get_text_from_files(o_files)[:max_context_length]
        
        # Prepare prompt
        prompt_template = PROMPT_TEMPLATES[analysis_type]
        prompt = prompt_template.format(
            vault_text=vault_text[:3000] if vault_text else "لا توجد وثائق مرفوعة",
            opponent_text=opponent_text[:3000] if opponent_text else "لا توجد وثائق للخصم",
            user_query=user_query
        )
        
        # Generate response
        with st.spinner(f"🤖 جاري تحليل الموقف باستخدام {label}..."):
            response = model.generate_content(prompt)
            
            # Store in chat history
            st.session_state.chat_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": analysis_type,
                "query": user_query,
                "response": response.text,
                "label": label,
                "style": style_class,
                "files_count": len(v_files or []) + len(o_files or [])
            })
            
            st.session_state.analysis_count += 1
        
        st.success("✅ تم الانتهاء من التحليل بنجاح!")
        time.sleep(0.5)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء التحليل: {str(e)}")
        st.code(traceback.format_exc(), language="python")

# =============================================
# 8. DISPLAY CHAT HISTORY
# =============================================

if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("📜 سجل التحليلات")
    
    for idx, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10
        # User Query
        st.markdown(f'''
        <div class="msg-box user-style">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b>👤 سؤالك:</b>
                <small style="color: #64748b;">{chat['timestamp']}</small>
            </div>
            <div style="margin-top: 10px;">{chat['query']}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # AI Response
        st.markdown(f'''
        <div class="msg-box {chat['style']}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b>{chat['label']}:</b>
                <small style="color: #64748b;">{chat['files_count']} ملف مرفوع</small>
            </div>
            <div style="margin-top: 10px;">{chat['response']}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        with st.expander(f"🔍 نسخ النص الكامل {idx+1}"):
            st.code(chat['response'], language="markdown")

# =============================================
# 9. OFFICIAL FINDINGS SECTION
# =============================================

if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("📋 التقرير الاستراتيجي النهائي")
    st.markdown("#### (#Official-Findings)")
    
    # Create report columns
    report_col1, report_col2 = st.columns([3, 1])
    
    with report_col1:
        st.markdown("""
        <div class="finding-card">
            <h3 style="color: #1e3a8a; margin-top: 0;">🎯 التوصيات المركزة</h3>
            <p>بناءً على التحليلات السابقة، إليك النقاط الرئيسية:</p>
            <ol>
                <li><strong>راجع كل تحليل</strong> للاطلاع على التفاصيل الكاملة</li>
                <li><strong>حدد الثغرات</strong> التي ذكرت في التحليل القانوني</li>
                <li><strong>استفد من النقاط النفسية</strong> في التفاوض</li>
                <li><strong>طبق الاستراتيجيات</strong> المقترحة خطوة بخطوة</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with report_col2:
        if st.button("📄 إنشاء تقرير كامل", use_container_width=True):
            # Generate comprehensive report
            all_analyses = []
            for chat in st.session_state.chat_history:
                all_analyses.append(f"""
                {'='*60}
                التحليل: {chat['label']}
                الوقت: {chat['timestamp']}
                {'='*60}
                
                السؤال: {chat['query'][:200]}...
                
                النقاط الرئيسية:
                {chat['response'][:1000]}...
                """)
            
            report_text = f"""
            التقرير الاستراتيجي النهائي
            تاريخ الإنشاء: {datetime.now().strftime("%Y-%m-%d %H:%M")}
            عدد التحليلات: {len(st.session_state.chat_history)}
            {'='*80}
            
            {''.join(all_analyses)}
            
            {'='*80}
            الخلاصة:
            1. راجع كل تحليل للتفاصيل الكاملة
            2. استخدم النقاط القانونية كأساس للمرافعة
            3. طبق الاستراتيجيات النفسية في التفاوض
            4. تبنى الخطط التكتيكية المقترحة
            
            تم إنشاء هذا التقرير تلقائياً بواسطة Strategic War Room Pro
            """
            
            # Display and offer download
            st.download_button(
                label="📥 تنزيل التقرير",
                data=report_text,
                file_name=f"التقرير_الاستراتيجي_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Summary Statistics
    st.markdown("#### 📊 إحصائيات التحليل")
    
    summary_cols = st.columns(4)
    analysis_types = [chat['type'] for chat in st.session_state.chat_history]
    
    with summary_cols[0]:
        st.metric("التحليلات القانونية", analysis_types.count("legal"))
    with summary_cols[1]:
        st.metric("التحليلات النفسية", analysis_types.count("psychological"))
    with summary_cols[2]:
        st.metric("التحليلات الاستراتيجية", analysis_types.count("strategic"))
    with summary_cols[3]:
        total_files = sum(chat['files_count'] for chat in st.session_state.chat_history)
        st.metric("إجمالي الملفات المعالجة", total_files)

# =============================================
# 10. EMPTY STATE
# =============================================

else:
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 20px;">
        <h2 style="color: #1e3a8a;">🚀 مرحباً بكم في War Room Pro</h2>
        <p style="font-size: 18px; color: #64748b; margin-bottom: 30px;">
        ابدأ برفع الوثائق في الشريط الجانبي، ثم اكتب سؤالك واختر نوع التحليل
        </p>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 40px;">
            <div style="padding: 20px; background: white; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                <h3>⚖️ قانوني</h3>
                <p>تحليل الجوانب القانونية والسوابق</p>
            </div>
            <div style="padding: 20px; background: white; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                <h3>🧠 نفسي</h3>
                <p>فهم الدوافع والتأثير النفسي</p>
            </div>
            <div style="padding: 20px; background: white; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
                <h3>🧨 استراتيجي</h3>
                <p>تطوير خطط تكتيكية متقدمة</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# 11. FOOTER
# =============================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 20px;">
    <small>Strategic War Room Pro v2.0 | تم التطوير للاستخدام القانوني الاستراتيجي</small><br>
    <small>⚠️ هذا التطبيق مساعد فقط ولا يعد رأياً قانونياً ملزماً</small>
</div>
""", unsafe_allow_html=True)
