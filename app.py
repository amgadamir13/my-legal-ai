# -*- coding: utf-8 -*-
"""ملف العائلة القانونية — نسخة عربية خاصة بمالك واحد."""
import json
from datetime import datetime

import streamlit as st
import google.api_core.exceptions as gapi_errors
import google.generativeai as genai

from auth import require_owner, logout_button
from storage import append_audit, init_db, load_case, save_case

st.set_page_config(page_title="ملف العائلة القانونية", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { direction:rtl!important; text-align:right!important; }
.block-container { max-width:1200px; }
textarea, input, select { direction:rtl!important; text-align:right!important; }
.stChatMessage { direction:rtl; }
.panel { background:#f8fafc; border:1px solid #dbe3ee; border-radius:14px; padding:16px; margin-bottom:12px; }
.notice { background:#fff8e1; border-right:5px solid #f59e0b; padding:12px; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

require_owner()
init_db()

DOMAINS = ["عقارات", "إيجارات", "تركات ومواريث", "جنائي", "متعدد المجالات"]
STATUSES = ["قيد التجميع", "تحت المراجعة", "توجد مواعيد عاجلة", "بانتظار مستندات", "مغلق مؤقتاً"]
RECORD_TYPES = ["محضر شرطة", "محضر نيابة", "قضية جنائية", "دعوى مدنية", "دعوى كلية", "دعوى جزئية", "إنذار رسمي", "إعلان", "حكم", "قرار ندب خبير", "تقرير خبير", "عقد قسمة", "عقد إيجار", "مذكرة", "مستند ملكية", "أخرى"]


def new_case():
    return {"id": 1, "title": "", "owner": "", "summary": "", "status": "قيد التجميع", "domains": [], "records": [], "chat": [], "tasks": [], "audit": [], "reports": []}


if "case" not in st.session_state:
    st.session_state.case = load_case(1) or new_case()
case = st.session_state.case


def persist(action=None, detail=""):
    case["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_case(case)
    if action:
        case.setdefault("audit", []).append({"time": datetime.now().isoformat(timespec="minutes"), "action": action, "detail": detail})
        save_case(case)
        append_audit(case.get("id", 1), action, detail)


def ask_ai(question):
    key = st.secrets.get("GEMINI_API_KEY", None)
    if not key:
        return "تم تسجيل سؤالك. لإجراء تحليل آلي، أضف GEMINI_API_KEY إلى Secrets. لا تعتمد على أي نتيجة قبل مراجعة محامٍ مصري."
    prompt = f"""
أنت مساعد لتنظيم ملف قانوني مصري، ولست محامياً أو جهة تحقيق. أجب بالعربية وباختصار.
لا تعتبر الفساد أو المؤامرة أو التلفيق حقيقة دون دليل، ولا تخترع قانوناً أو حكماً.
افصل بين الوقائع المسجلة والادعاءات والأسئلة الناقصة. لا تقدم إرشادات لإخفاء دليل أو التأثير على شاهد.
السؤال: {question}
بيانات الملف: {json.dumps(case, ensure_ascii=False, indent=2)}
"""
    try:
        genai.configure(api_key=key)
        result = genai.GenerativeModel(st.session_state.get("model", "gemini-2.5-flash")).generate_content(prompt)
        return getattr(result, "text", "لم يصل رد قابل للاستخدام.") or "لم يصل رد قابل للاستخدام."
    except gapi_errors.GoogleAPIError as exc:
        return f"تعذر الاتصال بخدمة التحليل: {exc}"
    except Exception as exc:
        return f"حدث خطأ أثناء التحليل: {exc}"


st.title("⚖️ ملف العائلة القانونية")
st.caption("مصر فقط · العربية · حساب مالك واحد")
st.markdown("<div class='notice'><b>تنبيه:</b> سجّل الوقائع ومصادرها. الادعاءات ليست حقائق تلقائية، ولا يصدر التطبيق رأياً قانونياً نهائياً.</div>", unsafe_allow_html=True)
with st.sidebar:
    st.header("ملفي الخاص")
    st.write(f"الحالة: **{case.get('status', 'قيد التجميع')}**")
    st.metric("السجلات", len(case.get("records", [])))
    st.metric("الأسئلة", len(case.get("chat", [])) // 2)
    logout_button()
    if st.button("حفظ الآن", use_container_width=True):
        persist("حفظ يدوي")
        st.success("تم الحفظ.")
    st.download_button("نسخة احتياطية JSON", json.dumps(case, ensure_ascii=False, indent=2), "family_case_backup.json", "application/json", use_container_width=True)

left, right = st.columns([2, 1])
with left:
    st.subheader("💬 تحدث معي عن الملف")
    for message in case.get("chat", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])
    question = st.chat_input("اكتب سؤالك أو أضف واقعة للملف...")
    if question:
        case.setdefault("chat", []).append({"role": "user", "content": question, "time": datetime.now().isoformat(timespec="minutes")})
        answer = ask_ai(question)
        case["chat"].append({"role": "assistant", "content": answer, "time": datetime.now().isoformat(timespec="minutes")})
        persist("إضافة محادثة")
        st.rerun()
with right:
    st.subheader("ملخص سريع")
    st.markdown(f"<div class='panel'><b>اسم الملف</b><br>{case.get('title') or 'لم يُحدد بعد'}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel'><b>صاحب الملف</b><br>{case.get('owner') or 'لم يُحدد بعد'}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel'><b>الملخص</b><br>{case.get('summary') or 'اكتب ملخصاً من إعداد الملف أدناه.'}</div>", unsafe_allow_html=True)

st.divider()
with st.expander("⚙️ إعداد الملف", expanded=not bool(case.get("title"))):
    with st.form("case_setup"):
        title = st.text_input("اسم الملف", case.get("title", ""), placeholder="مثال: ملف تركة وعقارات الأسرة")
        owner = st.text_input("الوارث / صاحب الأصول", case.get("owner", ""))
        domains = st.multiselect("مجالات الملف", DOMAINS, default=case.get("domains", []))
        status = st.selectbox("حالة الملف", STATUSES, index=STATUSES.index(case.get("status", "قيد التجميع")))
        summary = st.text_area("ملخص الملف", case.get("summary", ""), height=120)
        if st.form_submit_button("حفظ بيانات الملف", use_container_width=True):
            case.update({"title": title, "owner": owner, "domains": domains, "status": status, "summary": summary})
            persist("تحديث بيانات الملف")
            st.success("تم حفظ الملف بنجاح.")

st.subheader("🗂️ تنظيم الملف")
tab_records, tab_tasks, tab_reports = st.tabs(["المحررات والمحاضر", "المهام والمواعيد", "التقارير"])
with tab_records:
    with st.form("record_form"):
        a, b = st.columns(2)
        with a:
            rtype = st.selectbox("نوع السجل", RECORD_TYPES)
            number = st.text_input("الرقم / رقم القضية / رقم المحضر")
            authority = st.text_input("الجهة")
        with b:
            record_date = st.date_input("تاريخ السجل")
            received = st.date_input("تاريخ الاستلام")
            verified = st.selectbox("حالة التحقق", ["غير مراجع", "مراجع من المستخدم", "يحتاج مراجعة محامٍ", "تمت مراجعته مع محامٍ"])
        content = st.text_area("المحتوى أو الملخص المنقول", height=160)
        allegation = st.checkbox("يتضمن ادعاءً يحتاج إلى إثبات مستقل")
        if st.form_submit_button("إضافة إلى الملف", use_container_width=True):
            case.setdefault("records", []).append({"id": len(case["records"]) + 1, "type": rtype, "number": number, "authority": authority, "date": str(record_date), "received": str(received), "verified": verified, "content": content, "allegation": allegation})
            persist("إضافة سجل", rtype)
            st.success("تمت الإضافة والحفظ.")
    for item in reversed(case.get("records", [])):
        with st.expander(f"{item['type']} — {item['number'] or 'بلا رقم'} — {item['date']}"):
            st.write(f"الجهة: {item.get('authority') or 'غير محددة'} · التحقق: {item.get('verified')}")
            if item.get("allegation"):
                st.warning("هذا ادعاء يحتاج دليلاً، وليس إثباتاً تلقائياً.")
            st.write(item.get("content") or "لا يوجد محتوى.")
with tab_tasks:
    with st.form("task_form"):
        task = st.text_input("المهمة")
        due = st.date_input("الموعد")
        if st.form_submit_button("إضافة مهمة", use_container_width=True) and task.strip():
            case.setdefault("tasks", []).append({"id": len(case["tasks"]) + 1, "task": task, "due": str(due), "done": False})
            persist("إضافة مهمة", task)
            st.success("تمت إضافة المهمة.")
    for item in case.get("tasks", []):
        item["done"] = st.checkbox(f"{item['task']} — {item['due']}", item.get("done", False), key=f"task_{item['id']}")
    persist()
with tab_reports:
    st.session_state.model = st.selectbox("نموذج التحليل", ["gemini-2.5-flash", "gemini-2.5-pro"])
    st.info("التقارير الآلية مسودات فقط وتحتاج مراجعة محامٍ مصري.")
    if st.button("إنشاء مراجعة أولية"):
        text = ask_ai("أنشئ مراجعة منظمة للملف: الوقائع، الادعاءات، الفجوات، الأسئلة، والخطوات التالية.")
        case.setdefault("reports", []).append({"time": datetime.now().isoformat(timespec="minutes"), "text": text})
        persist("إنشاء تقرير")
    for report in reversed(case.get("reports", [])):
        with st.expander(f"تقرير {report['time']}"):
            st.write(report["text"])

st.caption("الحفظ الحالي يتم في SQLite على بيئة التطبيق. يلزم تخزين سحابي دائم ومشفّر قبل الاعتماد على بيانات حساسة.")
