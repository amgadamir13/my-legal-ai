import os
import fitz  # مكتبة PyMuPDF لقراءة الـ PDF
import openai
from verification import verify_citations

# إعدادات المجلد والمفتاح
DOCS_FOLDER = "./documents"
openai.api_key = "ضع_مفتاحك_هنا"

SYSTEM_INSTRUCTION = """
You are a Bilingual Legal Expert (Arabic/English).
1. Analyze as Compliance, Risk, and Drafting Agents.
2. Provide citations for EVERY fact: [Document Name, p. PageNumber].
3. Answer in the same language as the user's question.
4. If the info isn't in the docs, say 'Not found in sources'.
"""

def load_pdf_documents():
    """لقراءة كافة ملفات الـ PDF في المجلد"""
    docs_db = {}
    if not os.path.exists(DOCS_FOLDER):
        return docs_db
        
    for filename in os.listdir(DOCS_FOLDER):
        if filename.endswith(".pdf"):
            path = os.path.join(DOCS_FOLDER, filename)
            doc = fitz.open(path)
            # تخزين كل صفحة كنص مستقل
            docs_db[filename] = [page.get_text() for page in doc]
    return docs_db

def get_ai_response(user_query):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_query}
        ]
    )
    return response.choices[0].message.content

def run_app(user_input):
    # 1. تحميل المستندات
    all_docs = load_pdf_documents()
    
    # 2. الحصول على إجابة الذكاء الاصطناعي
    answer = get_ai_response(user_input)
    
    # 3. التحقق من صحة المراجع (Lie Detector)
    checks = verify_citations(answer, all_docs)
    
    # 4. التنسيق النهائي للشاشة (عربي وإنجليزي)
    report = f"### ⚖️ التحليل القانوني / Legal Analysis\n\n{answer}\n\n---\n"
    report += "### 🛡️ فحص الدقة / Accuracy Check\n"
    
    for c in checks:
        status = "✅ موثق" if c['verified'] else "❌ مخاطرة (هلوسة)"
        report += f"* {c['source']} (p.{c['page']}): {status} ({c['score']}%)\n"
        
    return report
