# -*- coding: utf-8 -*-
"""منصة ملف العائلة القانونية - الإصدار التنفيذي الأول."""
import html
import json
from datetime import date, datetime

import streamlit as st
import google.api_core.exceptions as gapi_errors
import google.generativeai as genai

st.set_page_config(page_title="منصة ملف العائلة القانونية", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { direction: rtl; text-align: right; }
.block-container { max-width: 1500px; }
.notice { background:#fff8e1; border-right:5px solid #d97706; padding:12px; border-radius:8px; margin-bottom:12px; }
.card { background:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:8px; margin-bottom:8px; }
.danger { background:#fff1f2; border-right:5px solid #be123c; padding:10px; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

DOMAINS = ["عقارات", "إيجارات", "تركات ومواريث", "جنائي", "متعدد المجالات"]
STATUSES = ["قيد التجميع", "تحت المراجعة", "توجد مواعيد عاجلة", "بانتظار مستندات", "مغلق مؤقتاً"]
RECORD_TYPES = [
    "محضر شرطة", "محضر نيابة", "قضية جنائية", "دعوى مدنية", "دعوى كلية", "دعوى جزئية",
    "إنذار رسمي", "إعلان", "حكم", "قرار ندب خبير", "تقرير خبير", "عقد قسمة", "عقد إيجار",
    "مذكرة", "خطاب", "إيصال", "مستند ملكية", "توكيل", "أخرى"
]
ROLES = ["وارث", "مؤجر", "مستأجر", "مقاول", "متهم", "مجني عليه / مدعٍ", "شاهد", "خبير", "محامٍ", "جهة", "غير محددة"]


def new_case():
    return {
        "id": 1, "title": "", "owner": "", "summary": "", "status": STATUSES[0],
        "domains": [], "records": [], "parties": [], "assets": [], "timeline": [],
        "tasks": [], "questions": [], "reports": [], "audit": [], "branches": []
    }


if "case" not in st.session_state:
    st.session_state.case = new_case()
if "model_choice" not in st.session_state:
    st.session_state.model_choice = "gemini-2.5-flash"

case = st.session_state.case


def esc(value):
    return html.escape(str(value or "")).replace("\n", "<br>")


def audit(action, detail=""):
    case["audit"].append({"time": datetime.now().isoformat(timespec="minutes"), "action": action, "detail": detail})


def add_item(collection, item, label):
    item["id"] = len(collection) + 1
    collection.append(item)
    audit(f"إضافة {label}", str(item.get("title") or item.get("name") or item.get("type") or item.get("event") or item.get("task") or ""))


def context_for_ai():
    return json.dumps(case, ensure_ascii=False, indent=2)


def generate_review():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        st.error("لم يتم إعداد GEMINI_API_KEY. التسجيل اليدوي والتصدير يعملان دون التحليل الآلي.")
        return
    prompt = f"""
أنت مساعد لتنظيم ملف قانوني مصري، ولست محامياً أو جهة تحقيق.
أجب بالعربية فقط وبقوائم مختصرة. لا تعتبر اتهام الفساد أو التلفيق أو المؤامرة حقيقة؛ صنفه كادعاء يحتاج دليلاً.
لا تخترع مادة أو حكماً أو واقعة أو موعداً. لا تقدم تعليمات لإخفاء دليل أو التأثير على شاهد أو تعطيل تحقيق.
رتب الإجابة تحت العناوين:
1. الوقائع المسجلة كما وردت
2. الادعاءات غير المثبتة
3. خريطة القضايا والمحاضر والفروع
4. التناقضات والفجوات
5. المستندات المطلوبة
6. المواعيد التي تحتاج تحققاً من محامٍ
7. المخاطر الإجرائية
8. أسئلة يجب الإجابة عنها قبل أي رأي
9. خطوات تنظيمية تالية

بيانات الملف:
{context_for_ai()}
"""
    try:
        genai.configure(api_key=api_key)
        result = genai.GenerativeModel(st.session_state.model_choice).generate_content(prompt)
        text = getattr(result, "text", "")
        if not text:
            st.warning("لم يصل نص قابل للاستخدام من النموذج.")
            return
        case["reports"].append({"time": datetime.now().isoformat(timespec="minutes"), "text": text})
        audit("إنشاء مسودة مراجعة آلية")
        st.success("تم إنشاء مسودة مراجعة. راجعها مع محامٍ مصري مختص قبل الاعتماد.")
    except gapi_errors.GoogleAPIError as exc:
        st.error(f"خطأ في خدمة التحليل: {exc}")
    except Exception as exc:
        st.error(f"خطأ غير متوقع: {exc}")


st.title("⚖️ منصة ملف العائلة القانونية")
st.caption("مصر فقط | العربية | عقارات وإيجارات وتركات ومحاضر وقضايا جنائية")
st.markdown("<div class='notice'><b>حدود الاستخدام:</b> هذه أداة تنظيم وتحليل أولي. تسجيل كلمة «مؤامرة» أو «فساد» أو «تلفيق» لا يثبتها. لا يصدر النظام رأياً نهائياً، ولا يستبدل المحامي أو النيابة أو المحكمة. لا تدخل بيانات حساسة في هذه النسخة قبل إضافة الدخول والتشفير والتخزين الآمن.</div>", unsafe_allow_html=True)

with st.expander("إعداد الملف الرئيسي", expanded=not bool(case["title"])):
    with st.form("main_case"):
        title = st.text_input("اسم الملف", case["title"], placeholder="مثال: ملف تركة وعقارات الأسرة")
        owner = st.text_input("الوارث / صاحب الأصول", case["owner"])
        domains = st.multiselect("مجالات الملف", DOMAINS, default=case["domains"])
        status = st.selectbox("الحالة", STATUSES, index=STATUSES.index(case["status"]))
        summary = st.text_area("الملخص الأولي كما يرويه المستخدم", case["summary"], height=110)
        if st.form_submit_button("حفظ بيانات الملف"):
            case.update({"title": title, "owner": owner, "domains": domains, "status": status, "summary": summary})
            audit("تحديث بيانات الملف")
            st.success("تم الحفظ في جلسة التطبيق الحالية.")

if not case["title"]:
    st.info("ابدأ باسم الملف، ثم أضف الفروع والأطراف والمحررات.")

# Sidebar: quick actions
with st.sidebar:
    st.header("إدارة الملف")
    st.write(f"**الملف:** {case['title'] or 'غير مسمى'}")
    st.write(f"**الحالة:** {case['status']}")
    st.metric("الفروع", len(case["branches"]))
    st.metric("السجلات", len(case["records"]))
    st.metric("المهام المفتوحة", sum(not t.get("done") for t in case["tasks"]))
    st.divider()
    if st.button("تنزيل نسخة JSON", use_container_width=True):
        st.download_button("اضغط للتنزيل", json.dumps(case, ensure_ascii=False, indent=2), "family_legal_case.json", "application/json", use_container_width=True)
    if st.button("بدء ملف جديد", use_container_width=True):
        st.session_state.case = new_case()
        st.rerun()

# Dashboard
summary_tabs = st.tabs(["لوحة الملف", "فروع القضية", "المحررات والمحاضر", "الأطراف", "الأصول", "الخط الزمني", "المهام والمواعيد", "المراجعة والتدقيق"])

with summary_tabs[0]:
    cols = st.columns(6)
    metrics = [("الفروع", len(case["branches"])), ("السجلات", len(case["records"])), ("الأطراف", len(case["parties"])), ("الأصول", len(case["assets"])), ("المهام المفتوحة", sum(not t.get("done") for t in case["tasks"])), ("التقارير", len(case["reports"]))]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
    st.subheader("ملخص الملف")
    st.write(case["summary"] or "لا يوجد ملخص بعد.")
    if case["status"] == "توجد مواعيد عاجلة":
        st.markdown("<div class='danger'><b>تنبيه:</b> توجد مواعيد مصنفة عاجلة. تحقق منها مع المحامي والجهة المختصة.</div>", unsafe_allow_html=True)
    st.subheader("آخر نشاط")
    for item in reversed(case["audit"][-8:]):
        st.caption(f"{item['time']} — {item['action']} {item['detail']}")

with summary_tabs[1]:
    st.subheader("فروع القضية")
    st.write("استخدم الفروع لتفكيك الملف الرئيسي إلى مسارات مستقلة وربط كل فرع بمحررات وأطراف ومواعيد.")
    with st.form("branch_form"):
        branch_title = st.text_input("اسم الفرع", placeholder="مثال: الطعن على عقد القسمة")
        branch_type = st.selectbox("نوع الفرع", ["تركة / قسمة", "عقار", "إيجار", "جنائي", "مقاول / تعاقد", "خبير", "أخرى"])
        branch_number = st.text_input("رقم القضية أو المحضر إن وجد")
        branch_status = st.selectbox("حالة الفرع", STATUSES)
        branch_notes = st.text_area("وصف مختصر وحدود الفرع")
        if st.form_submit_button("إضافة فرع") and branch_title.strip():
            add_item(case["branches"], {"title": branch_title, "type": branch_type, "number": branch_number, "status": branch_status, "notes": branch_notes}, "فرع")
            st.success("تمت إضافة الفرع.")
    for branch in case["branches"]:
        st.markdown(f"<div class='card'><b>#{branch['id']} — {esc(branch['title'])}</b><br>النوع: {esc(branch['type'])} | الرقم: {esc(branch['number']) or 'غير محدد'} | الحالة: {esc(branch['status'])}<br>{esc(branch['notes'])}</div>", unsafe_allow_html=True)

with summary_tabs[2]:
    st.subheader("المحررات والمحاضر والقضايا")
    with st.form("record_form"):
        rtype = st.selectbox("النوع", RECORD_TYPES)
        number = st.text_input("الرقم / رقم القضية / رقم المحضر")
        record_date = st.date_input("تاريخ المحرر")
        authority = st.text_input("الجهة")
        received = st.date_input("تاريخ الاستلام")
        branch_id = st.selectbox("الفرع المرتبط", ["غير مرتبط"] + [f"#{b['id']} — {b['title']}" for b in case["branches"]])
        verification = st.selectbox("حالة التحقق", ["غير مراجع", "مراجع من المستخدم", "يحتاج مراجعة محامٍ", "تمت مراجعته مع محامٍ"])
        allegation = st.checkbox("يتضمن ادعاء فساد أو تلفيق أو مؤامرة — سيبقى ادعاءً يحتاج دليلاً")
        content = st.text_area("محتوى المحرر أو ملخصه المنقول يدوياً", height=170)
        notes = st.text_area("ملاحظات وروابط مع محررات أخرى", height=90)
        if st.form_submit_button("إضافة سجل"):
            add_item(case["records"], {"type": rtype, "number": number, "date": str(record_date), "authority": authority, "received": str(received), "branch": branch_id, "verification": verification, "allegation": allegation, "content": content, "notes": notes}, "محرر أو محضر")
            st.success("تمت إضافة السجل.")
    for item in reversed(case["records"]):
        with st.expander(f"#{item['id']} — {item['type']} — {item['number'] or 'بلا رقم'} — {item['date']}"):
            st.write(f"الجهة: {item['authority'] or 'غير محددة'} | الفرع: {item['branch']} | التحقق: {item['verification']}")
            if item["allegation"]:
                st.warning("هذا السجل يحتوي ادعاءً، وليس إثباتاً مستقلاً.")
            st.markdown(esc(item["content"]), unsafe_allow_html=True)
            if item["notes"]:
                st.caption(item["notes"])

with summary_tabs[3]:
    st.subheader("الأطراف والأشخاص")
    with st.form("party_form"):
        name = st.text_input("الاسم")
        role = st.selectbox("الصفة", ROLES)
        relation = st.text_input("العلاقة بالقضية أو الأصل")
        evidence = st.text_input("مصدر إثبات الاسم والصفة")
        notes = st.text_area("ملاحظات تحقق")
        if st.form_submit_button("إضافة شخص") and name.strip():
            add_item(case["parties"], {"name": name, "role": role, "relation": relation, "evidence": evidence, "notes": notes}, "طرف")
            st.success("تمت إضافة الشخص.")
    for person in case["parties"]:
        st.markdown(f"<div class='card'><b>{esc(person['name'])}</b> — {esc(person['role'])}<br>العلاقة: {esc(person['relation'])}<br>المصدر: {esc(person['evidence'])}<br>{esc(person['notes'])}</div>", unsafe_allow_html=True)

with summary_tabs[4]:
    st.subheader("الأصول والعقارات")
    with st.form("asset_form"):
        asset = st.text_input("وصف الأصل / العقار")
        ownership = st.text_input("سند أو مصدر الملكية")
        holder = st.text_input("الحائز أو المدير الحالي")
        branch = st.text_input("الفرع أو القضايا المرتبطة")
        notes = st.text_area("ملاحظات")
        if st.form_submit_button("إضافة أصل") and asset.strip():
            add_item(case["assets"], {"asset": asset, "ownership": ownership, "holder": holder, "branch": branch, "notes": notes}, "أصل")
            st.success("تمت إضافة الأصل.")
    for item in case["assets"]:
        st.markdown(f"<div class='card'><b>{esc(item['asset'])}</b><br>الملكية: {esc(item['ownership'])}<br>الحيازة: {esc(item['holder'])}<br>الارتباطات: {esc(item['branch'])}<br>{esc(item['notes'])}</div>", unsafe_allow_html=True)

with summary_tabs[5]:
    st.subheader("الخط الزمني")
    with st.form("timeline_form"):
        event_date = st.date_input("تاريخ الحدث")
        event = st.text_area("الحدث أو الإجراء")
        source = st.text_input("المصدر")
        if st.form_submit_button("إضافة حدث") and event.strip():
            add_item(case["timeline"], {"date": str(event_date), "event": event, "source": source}, "حدث")
            case["timeline"].sort(key=lambda x: x["date"])
            st.success("تمت إضافة الحدث.")
    for item in case["timeline"]:
        st.markdown(f"- **{item['date']}** — {esc(item['event'])} _(المصدر: {esc(item['source'])})_", unsafe_allow_html=True)

with summary_tabs[6]:
    st.subheader("المهام والمواعيد")
    with st.form("task_form"):
        task = st.text_input("المهمة")
        due = st.date_input("الموعد")
        responsible = st.text_input("المسؤول")
        priority = st.selectbox("الأولوية", ["عادية", "مهمة", "عاجلة"])
        linked = st.text_input("القضية / المحرر المرتبط")
        if st.form_submit_button("إضافة مهمة") and task.strip():
            add_item(case["tasks"], {"task": task, "due": str(due), "responsible": responsible, "priority": priority, "linked": linked, "done": False}, "مهمة")
            st.success("تمت إضافة المهمة.")
    for item in case["tasks"]:
        done = st.checkbox(f"{item['task']} — {item['due']} — {item['priority']} — المسؤول: {item['responsible'] or 'غير محدد'}", value=item["done"], key=f"task_{item['id']}")
        item["done"] = done

with summary_tabs[7]:
    st.subheader("المراجعة والتدقيق")
    st.info("قبل أي رأي: افصل الوقائع المؤكدة عن الادعاءات، وراجع الصفة والرقم والتاريخ والمصدر مع المحامي.")
    with st.form("question_form"):
        question = st.text_input("سؤال يحتاج إجابة قبل الرأي")
        if st.form_submit_button("إضافة سؤال") and question.strip():
            add_item(case["questions"], {"question": question, "answered": False}, "سؤال")
            st.success("تمت إضافة السؤال.")
    for q in case["questions"]:
        q["answered"] = st.checkbox(q["question"], value=q["answered"], key=f"question_{q['id']}")
    st.divider()
    st.session_state.model_choice = st.selectbox("نموذج التحليل الاختياري", ["gemini-2.5-flash", "gemini-2.5-pro"])
    if st.button("إنشاء مسودة مراجعة منظمة"):
        generate_review()
    for report in reversed(case["reports"]):
        with st.expander(f"مسودة مراجعة — {report['time']}", expanded=True):
            st.markdown(report["text"])
    st.subheader("سجل التدقيق")
    for item in reversed(case["audit"][-30:]):
        st.caption(f"{item['time']} — {item['action']} {item['detail']}")

st.divider()
st.caption("الإصدار الحالي يحفظ البيانات في جلسة التطبيق فقط. قبل الاستخدام الحقيقي يلزم تخزين آمن دائم، تسجيل دخول، تشفير، صلاحيات، نسخ احتياطي، وسياسة احتفاظ.")
