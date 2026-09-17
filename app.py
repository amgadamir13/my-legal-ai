# -*- coding: utf-8 -*-
"""ملف العائلة القانونية - واجهة عربية سهلة الاستخدام."""
import json
from datetime import datetime

import streamlit as st
import google.api_core.exceptions as gapi_errors
import google.generativeai as genai

from storage import load_case, save_case, append_audit, init_db

st.set_page_config(page_title="ملف العائلة القانونية", page_icon="⚖️", layout="wide")

# ----- General Arabic-friendly styling -----
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important;
        text-align: right !important;
        unicode-bidi: plaintext !important;
        font-family: 'Tahoma', 'Segoe UI', sans-serif !important;
        letter-spacing: normal !important;
    }
    .block-container { max-width: 1500px; }
    .panel { background: #f8fafc; border: 1px solid #dbe3ee; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
    .notice { background: #fff8e1; border-right: 5px solid #f59e0b; padding: 12px 14px; border-radius: 10px; margin-bottom: 14px; }
    .warning { background: #fff1f2; border-right: 5px solid #be123c; padding: 12px 14px; border-radius: 10px; }
    .pill { display: inline-block; background: #e0f2fe; color: #0f172a; padding: 5px 10px; border-radius: 999px; font-size: 12px; margin: 4px 4px 4px 0; }
    .chat-box { background: #ffffff; border: 1px solid #dfe7f1; border-radius: 14px; padding: 14px; min-height: 220px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----- Defaults -----
DOMAIN_LIST = ["عقارات", "إيجارات", "تركات ومواريث", "جنائي", "متعدد المجالات"]
STATUS_LIST = ["قيد التجميع", "تحت المراجعة", "توجد مواعيد عاجلة", "بانتظار مستندات", "مغلق مؤقتاً"]
RECORD_TYPES = [
    "محضر شرطة", "محضر نيابة", "قضية جنائية", "دعوى مدنية", "دعوى كلية", "دعوى جزئية",
    "إنذار رسمي", "إعلان", "حكم", "قرار ندب خبير", "تقرير خبير", "عقد قسمة", "عقد إيجار",
    "مذكرة", "خطاب", "إيصال", "مستند ملكية", "توكيل", "أخرى"
]
ROLE_LIST = ["وارث", "مؤجر", "مستأجر", "مقاول", "متهم", "مجني عليه / مدعٍ", "شاهد", "خبير", "محامٍ", "جهة", "غير محددة"]


def new_case():
    return {
        "id": 1,
        "title": "",
        "owner": "",
        "summary": "",
        "status": "قيد التجميع",
        "domains": [],
        "records": [],
        "parties": [],
        "assets": [],
        "timeline": [],
        "tasks": [],
        "questions": [],
        "reports": [],
        "audit": [],
        "branches": [],
        "chat": [],
    }


# Initialize DB
init_db()

# Session state
if "case" not in st.session_state:
    raw = load_case(1)
    st.session_state.case = raw if raw else new_case()
if "model_choice" not in st.session_state:
    st.session_state.model_choice = "gemini-2.5-flash"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

case = st.session_state.case
chat_messages = st.session_state.chat_messages


def persist_case():
    case["updated_at"] = datetime.now().isoformat(timespec="seconds")
    save_case(case)


def push_audit(action, detail=""):
    case["audit"].append({
        "time": datetime.now().isoformat(timespec="minutes"),
        "action": action,
        "detail": detail,
    })
    persist_case()
    append_audit(case.get("id", 1), action, detail)


def add_item(collection, item, label):
    item["id"] = len(collection) + 1
    collection.append(item)
    push_audit(f"إضافة {label}", str(item.get("title") or item.get("name") or item.get("type") or item.get("event") or item.get("task") or ""))


def summary_text():
    return case.get("summary") or "لا يوجد ملخص بعد."


def build_ai_prompt():
    return f"""
أنت مساعد في تنظيم ملف قانوني مصري. أجب بالعربية فقط، وبأقصر صورة عملية ممكنة.
لا تعتبر اتهام الفساد أو المؤامرة أو التلفيق حقيقة مكتملة؛ صنفه كادعاء يحتاج دليلًا ودراسة.
لا تخترع مادة قانونية أو حكم أو خبر أو واقعة.
ابحث في الملف التالي فقط، ثم قدم:
1) الوقائع المسجلة
2) الادعاءات غير المثبتة
3) فجوات المعلومات
4) أسئلة حيوية
5) خطوات تنفيذية

المحتوى:
{json.dumps(case, ensure_ascii=False, indent=2)}
"""


def generate_review():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        st.warning("لم يتم إعداد المفتاح. يمكنك متابعة إدخال البيانات يدويًا."
                   )
        return
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(st.session_state.model_choice)
        response = model.generate_content(build_ai_prompt())
        text = getattr(response, "text", "") or ""
        if text:
            case["reports"].append({"time": datetime.now().isoformat(timespec="minutes"), "text": text})
            push_audit("إنشاء مراجعة آلية")
            st.success("تم إنشاء مسودة مراجعة.")
        else:
            st.warning("لم يصل رد قابِل للاستعمال.")
    except gapi_errors.GoogleAPIError as exc:
        st.error(f"خطأ في خدمة Gemini: {exc}")
    except Exception as exc:
        st.error(f"خطأ غير متوقع: {exc}")


def add_chat_message(role, content):
    st.session_state.chat_messages.append({"role": role, "content": content})
    case.setdefault("chat", []).append({"role": role, "content": content, "time": datetime.now().isoformat(timespec="minutes")})
    persist_case()


st.title("⚖️ ملف العائلة القانونية")
st.caption("نسخة عربية سهلة الاستخدام — بيانات ملفية وملخصات ومواعيد ومحررات")

st.markdown(
    """
    <div class='notice'>
    <b>مهم:</b> هذه الأداة لا تثبت فسادًا أو مؤامرة أو تلفيقًا تلقائيًا، إنها تسجل الادعاء والتوثيق وتساعد على التنظيم فقط.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("لوحة التحكم")
    st.subheader("ملف القضية")
    st.write(f"**العنوان:** {case.get('title') or 'غير محدد'}")
    st.write(f"**المالك/الوارث:** {case.get('owner') or 'غير محدد'}")
    st.write(f"**الحالة:** {case.get('status') or 'قيد التجميع'}")
    st.write(f"**المجالات:** {', '.join(case.get('domains') or []) or 'غير محددة'}")
    st.markdown("---")
    if st.button("حفظ الملف الآن", use_container_width=True):
        persist_case()
        st.success("تم حفظ الملف.")
    if st.button("ابدأ ملف جديد", use_container_width=True):
        st.session_state.case = new_case()
        st.session_state.chat_messages = []
        persist_case()
        st.rerun()
    st.markdown("---")
    st.caption("ملاحظات: التطبيق الحالي محلي، ولا يزال يحتاج إلى تسجيل دخول وتشفير قبل الاستخدام الحقيقي.")

# ---- Main top area ----
left, right = st.columns([2, 1])

with left:
    st.subheader("محادثة الملف")
    chat_container = st.container()
    with chat_container:
        for message in chat_messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])

    prompt = st.chat_input("اكتب سؤالاً أو طلباً عن الملف")
    if prompt:
        add_chat_message("user", prompt)
        # Simple auto response
        auto_reply = (
            "تم تسجيل السؤال في الملف. "
            "يرجى مراجعة تفاصيل القضايا والملفات المرفقة، ثم تحديد: "
            "1) الواقعة، 2) المصدر، 3) هل يوجد مستند أو محضر، 4) من هو الطرف، 5) ما المعلومة الناقصة."
        )
        add_chat_message("assistant", auto_reply)
        st.rerun()

with right:
    st.subheader("ملخص سريع")
    st.markdown(f"<div class='panel'><b>عنوان الملف:</b><br>{case.get('title') or 'غير محدد'}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel'><b>صاحب الملف:</b><br>{case.get('owner') or 'غير محدد'}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel'><b>حالة الملف:</b><br>{case.get('status') or 'قيد التجميع'}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel'><b>التقييم السريع:</b><br>{summary_text()}</div>", unsafe_allow_html=True)

st.markdown("---")

# ----- Data entry form -----
with st.container():
    st.subheader("إعداد الملف الرئيسي")
    with st.form("case_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("اسم الملف", value=case.get("title", ""), placeholder="مثال: قضية تركة وعقارات الأسرة")
            owner = st.text_input("الوارث / صاحب الأصول", value=case.get("owner", ""))
        with col2:
            domains = st.multiselect("مجالات الملف", DOMAIN_LIST, default=case.get("domains", []))
            status = st.selectbox("الحالة", STATUS_LIST, index=STATUS_LIST.index(case.get("status", "قيد التجميع")))
        summary = st.text_area("ملخص الملف", value=case.get("summary", ""), height=120)
        if st.form_submit_button("حفظ بيانات الملف"):
            case.update({"title": title, "owner": owner, "domains": domains, "status": status, "summary": summary})
            persist_case()
            push_audit("تحديث ملف القضية")
            st.success("تم حفظ البيانات.")

# Tabs for organization
main_tabs = st.tabs(["المحررات", "الأطراف", "الأصول", "المهام", "الخط الزمني", "التقارير"])

with main_tabs[0]:
    st.subheader("إضافة محضر أو محرر أو قضية")
    with st.form("record_form"):
        col1, col2 = st.columns(2)
        with col1:
            rtype = st.selectbox("نوع المحرر", RECORD_TYPES)
            number = st.text_input("الرقم / رقم القضية")
            record_date = st.date_input("تاريخ المحرر")
            authority = st.text_input("الجهة")
        with col2:
            received = st.date_input("تاريخ الاستلام")
            verification = st.selectbox("حالة التحقق", ["غير مراجع", "مراجع من المستخدم", "يحتاج مراجعة محامٍ", "تمت مراجعته مع محامٍ"])
            allegation = st.checkbox("يحتوي على ادعاء فساد / تلفيق / مؤامرة")
        content = st.text_area("محتوى المحرر أو ملخصه", height=180)
        notes = st.text_area("ملاحظات إضافية", height=80)
        if st.form_submit_button("إضافة السجل"):
            new_record = {
                "type": rtype,
                "number": number,
                "date": str(record_date),
                "authority": authority,
                "received": str(received),
                "verification": verification,
                "allegation": allegation,
                "content": content,
                "notes": notes,
            }
            add_item(case["records"], new_record, "محرر")
            persist_case()
            st.success("تمت إضافة السجل.")

    for item in reversed(case.get("records", [])):
        with st.expander(f"#{item['id']} — {item['type']} — {item['number'] or 'بلا رقم'}"):
            if item.get("allegation"):
                st.warning("هذا السجل يحتوي على ادعاء يحتاج إلى إثبات مستقل.")
            st.write(f"**الجهة:** {item.get('authority') or 'غير محددة'}")
            st.write(f"**التاريخ:** {item.get('date') or 'غير محدد'}")
            st.write(item.get("content") or "لا يوجد نص.")
            if item.get("notes"):
                st.caption(item.get("notes"))

with main_tabs[1]:
    st.subheader("الأطراف والأشخاص")
    with st.form("party_form"):
        name = st.text_input("الاسم")
        role = st.selectbox("الصفة", ROLE_LIST)
        relation = st.text_input("العلاقة بالقضية أو الأصل")
        evidence = st.text_input("مصدر إثبات الصفة")
        notes = st.text_area("ملاحظات", height=80)
        if st.form_submit_button("إضافة طرف") and name.strip():
            add_item(case["parties"], {"name": name, "role": role, "relation": relation, "evidence": evidence, "notes": notes}, "طرف")
            persist_case()
            st.success("تمت إضافة الطرف.")
    for p in case.get("parties", []):
        st.markdown(f"<div class='panel'><b>{p.get('name')}</b> — {p.get('role')}<br>العلاقة: {p.get('relation')}<br>المصدر: {p.get('evidence')}<br>{p.get('notes')}</div>", unsafe_allow_html=True)

with main_tabs[2]:
    st.subheader("الأصول والعقارات")
    with st.form("asset_form"):
        asset = st.text_input("اسم الأصل أو العقار")
        ownership = st.text_input("سند الملكية أو مصدرها")
        holder = st.text_input("الحائز الحالي")
        notes = st.text_area("ملاحظات إضافية")
        if st.form_submit_button("إضافة أصل") and asset.strip():
            add_item(case["assets"], {"asset": asset, "ownership": ownership, "holder": holder, "notes": notes}, "أصل")
            persist_case()
            st.success("تمت إضافة الأصل.")
    for a in case.get("assets", []):
        st.markdown(f"<div class='panel'><b>{a.get('asset')}</b><br>الملكية: {a.get('ownership')}<br>الحائز: {a.get('holder')}<br>{a.get('notes')}</div>", unsafe_allow_html=True)

with main_tabs[3]:
    st.subheader("المهام والمواعيد")
    with st.form("task_form"):
        task = st.text_input("المهمة")
        due = st.date_input("الموعد")
        responsible = st.text_input("المسؤول")
        priority = st.selectbox("الأولوية", ["عادية", "مهمة", "عاجلة"])
        if st.form_submit_button("إضافة مهمة") and task.strip():
            add_item(case["tasks"], {"task": task, "due": str(due), "responsible": responsible, "priority": priority, "done": False}, "مهمة")
            persist_case()
            st.success("تمت إضافة المهمة.")

    for item in case.get("tasks", []):
        done = st.checkbox(f"{item.get('task')} — {item.get('due')} — {item.get('priority')}", value=item.get("done", False), key=f"task_{item['id']}")
        item["done"] = done
        persist_case()

with main_tabs[4]:
    st.subheader("الخط الزمني")
    with st.form("timeline_form"):
        event = st.text_area("الحدث")
        event_date = st.date_input("تاريخ الحدث")
        source = st.text_input("المصدر")
        if st.form_submit_button("إضافة حدث") and event.strip():
            add_item(case["timeline"], {"event": event, "date": str(event_date), "source": source}, "حدث")
            persist_case()
            st.success("تمت إضافة الحدث.")
    for t in case.get("timeline", []):
        st.markdown(f"- **{t.get('date')}** — {t.get('event')} (_{t.get('source') or 'غير محدد'}_)")

with main_tabs[5]:
    st.subheader("المراجعة والتقارير")
    st.session_state.model_choice = st.selectbox("نموذج التحليل", ["gemini-2.5-flash", "gemini-2.5-pro"], index=0)
    if st.button("إنشاء مراجعة أولية"):
        generate_review()
    for report in reversed(case.get("reports", [])):
        with st.expander(f"تقارير — {report.get('time')}", expanded=False):
            st.markdown(report.get("text", ""))

st.markdown("---")

# Add quick questions section
st.subheader("أسئلة تحتاج إجابة قبل إصدار رأي")
with st.form("question_form"):
    q = st.text_input("اكتب السؤال")
    if st.form_submit_button("إضافة سؤال") and q.strip():
        add_item(case["questions"], {"question": q, "answered": False}, "سؤال")
        persist_case()
        st.success("تمت إضافة السؤال.")
for q in case.get("questions", []):
    q["answered"] = st.checkbox(q.get("question"), value=q.get("answered", False), key=f"q_{q['id']}")
    persist_case()

# Final note
st.caption("الواجهة الحالية هي نسخة سهلة الاستخدام للفترة الأولى. لا تزال بحاجة إلى تسجيل دخول، صلاحيات، وتخزين آمن قبل استخدام بيانات محكمة أو جنائية حقيقية.")
