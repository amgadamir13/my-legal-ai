# -*- coding: utf-8 -*-
"""منصة ملف العائلة القانونية - نسخة MVP عربية.

هذه النسخة تنظّم الوقائع والمحررات والمحاضر ولا تستبدل المحامي أو جهة التحقيق.
"""
import html
import json
from datetime import datetime

import streamlit as st
import google.api_core.exceptions as gapi_errors
import google.generativeai as genai

st.set_page_config(page_title="ملف العائلة القانونية", page_icon="⚖️", layout="wide")

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] { direction: rtl; text-align: right; }
    .notice { background:#fff8e1; border-right:5px solid #d97706; padding:12px; border-radius:8px; }
    .card { background:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:8px; margin-bottom:8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# State and safe local data model
# -----------------------------
def blank_case():
    return {
        "title": "",
        "owner": "",
        "summary": "",
        "status": "قيد التجميع",
        "records": [],
        "parties": [],
        "assets": [],
        "timeline": [],
        "questions": [],
        "reports": [],
    }

if "case" not in st.session_state:
    st.session_state.case = blank_case()
if "model_choice" not in st.session_state:
    st.session_state.model_choice = "gemini-2.5-flash"

case = st.session_state.case

# -----------------------------
# Helpers
# -----------------------------
def add_record(record):
    record["id"] = len(case["records"]) + 1
    case["records"].append(record)


def record_label(record):
    return f"{record['type']} — {record['number'] or 'بلا رقم'} — {record['date'] or 'بلا تاريخ'}"


def render_text(value):
    return html.escape(str(value or "")).replace("\n", "<br>")


def build_case_context():
    return json.dumps(case, ensure_ascii=False, indent=2)


def generate_review():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        st.error("لم يتم إعداد GEMINI_API_KEY. يمكن استخدام التسجيل اليدوي دون التحليل الآلي.")
        return
    genai.configure(api_key=api_key)
    prompt = f"""
أنت مساعد لتنظيم ملف قانوني مصري، ولست محامياً ولا جهة تحقيق.
حلل البيانات التالية بالعربية فقط. لا تعتبر كلمة «مؤامرة» حقيقة؛ صنّفها كادعاء يحتاج دليلاً.
لا تخترع قانوناً أو مادة أو حكماً أو واقعة. إذا كانت البيانات ناقصة فاذكر الأسئلة اللازمة.
أخرج قوائم قصيرة بالعناوين التالية:
1) الوقائع المؤكدة كما وردت
2) الادعاءات غير المثبتة
3) تناقضات أو فجوات البيانات
4) خريطة القضايا والمحاضر والروابط بينها
5) الأدلة والمحررات المطلوبة
6) المخاطر الإجرائية ومواعيد تحتاج تحققاً من محامٍ
7) أسئلة عاجلة للمستخدم
8) خطوات تنظيمية تالية، دون تعليمات لإخفاء دليل أو التأثير على شاهد أو تعطيل تحقيق

بيانات الملف:
{build_case_context()}
"""
    try:
        model = genai.GenerativeModel(st.session_state.model_choice)
        result = model.generate_content(prompt)
        text = getattr(result, "text", "")
        if text:
            case["reports"].append({"date": datetime.now().isoformat(timespec="minutes"), "text": text})
            st.success("تم إنشاء مسودة مراجعة. يجب مراجعتها مع محامٍ مصري مختص.")
        else:
            st.warning("لم يصل نص قابل للاستخدام من النموذج.")
    except gapi_errors.GoogleAPIError as exc:
        st.error(f"خطأ في خدمة التحليل: {exc}")
    except Exception as exc:
        st.error(f"خطأ غير متوقع: {exc}")

# -----------------------------
# Header and boundaries
# -----------------------------
st.title("⚖️ ملف العائلة القانونية")
st.caption("نسخة MVP عربية لإدارة ملف متشعب: عقارات، إيجارات، تركات، ومحاضر وقضايا جنائية")
st.markdown(
    '<div class="notice"><b>تنبيه مهم:</b> النظام يسجل الوقائع والادعاءات كما تقدمها، لكنه لا يثبت وجود فساد أو مؤامرة تلقائياً. كل اتهام يحتاج مستنداً ومراجعة محامٍ. هذه النسخة تحفظ البيانات في جلسة Streamlit الحالية وليست نظاماً آمناً للإنتاج أو لمشاركة أسرار حساسة قبل إضافة الدخول والتشفير.</div>',
    unsafe_allow_html=True,
)

# -----------------------------
# Case setup
# -----------------------------
with st.expander("إعداد الملف الرئيسي", expanded=not bool(case["title"])):
    with st.form("case_form"):
        title = st.text_input("اسم الملف", value=case["title"], placeholder="مثال: ملف تركة وعقارات الأسرة")
        owner = st.text_input("صاحب الملف / الوارث", value=case["owner"])
        summary = st.text_area("ملخص أولي كما يراه المستخدم (ليس حكماً نهائياً)", value=case["summary"], height=100)
        status = st.selectbox("حالة الملف", ["قيد التجميع", "تحت مراجعة المحامين", "توجد مواعيد عاجلة", "مغلق مؤقتاً"], index=["قيد التجميع", "تحت مراجعة المحامين", "توجد مواعيد عاجلة", "مغلق مؤقتاً"].index(case["status"]))
        if st.form_submit_button("حفظ بيانات الملف"):
            case.update({"title": title, "owner": owner, "summary": summary, "status": status})
            st.success("تم حفظ بيانات الملف في الجلسة الحالية.")

if not case["title"]:
    st.info("ابدأ باسم الملف ثم أضف الأطراف والمحررات والمحاضر.")

# -----------------------------
# Main workspace
# -----------------------------
tab_overview, tab_records, tab_people, tab_assets, tab_timeline, tab_review = st.tabs([
    "نظرة عامة", "المحررات والمحاضر", "الأطراف", "الأصول", "الخط الزمني", "المراجعة والتقارير"
])

with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("المحررات والمحاضر", len(case["records"]))
    c2.metric("الأطراف", len(case["parties"]))
    c3.metric("الأصول", len(case["assets"]))
    c4.metric("التقارير", len(case["reports"]))
    st.subheader("خريطة الملف")
    st.write(case["summary"] or "لم تتم إضافة ملخص بعد.")
    st.markdown("**المبدأ التشغيلي:** نسجل الادعاء، ثم مصدره، ثم درجة التحقق؛ ولا نحول رواية طرف إلى حقيقة آلية.")

with tab_records:
    st.subheader("إضافة محرر أو محضر أو قضية")
    record_types = [
        "محضر شرطة", "قضية جنائية", "دعوى مدنية", "دعوى كلية", "دعوى جزئية",
        "إنذار رسمي", "إعلان", "حكم", "قرار ندب خبير", "عقد قسمة", "عقد إيجار",
        "مذكرة", "خطاب", "إيصال", "مستند ملكية", "أخرى"
    ]
    with st.form("record_form"):
        rtype = st.selectbox("نوع المحرر", record_types)
        number = st.text_input("الرقم / رقم القضية / رقم المحضر")
        record_date = st.date_input("التاريخ")
        authority = st.text_input("الجهة: محكمة، نيابة، قسم، شهر عقاري، خبير...")
        received = st.date_input("تاريخ الاستلام")
        verification = st.selectbox("حالة التحقق", ["غير مراجع", "مراجع من المستخدم", "يحتاج مراجعة محامٍ", "تمت مراجعته مع محامٍ"])
        allegation = st.checkbox("يتضمن ادعاء فساد/تلفيق/تآمر (يسجل كادعاء لا كحقيقة)")
        content = st.text_area("محتوى المحرر أو ملخصه المنقول يدوياً", height=180)
        notes = st.text_area("ملاحظات وربط بقضايا أو محررات أخرى", height=100)
        if st.form_submit_button("إضافة إلى الملف"):
            add_record({"type": rtype, "number": number, "date": str(record_date), "authority": authority, "received": str(received), "verification": verification, "allegation": allegation, "content": content, "notes": notes})
            st.success("تمت إضافة السجل.")
    st.divider()
    for item in reversed(case["records"]):
        with st.expander(f"#{item['id']} — {record_label(item)}"):
            st.write(f"الجهة: {item['authority'] or 'غير محددة'} | التحقق: {item['verification']}")
            if item["allegation"]:
                st.warning("هذا السجل يحتوي ادعاءً يحتاج إثباتاً مستقلاً.")
            st.markdown(render_text(item["content"]), unsafe_allow_html=True)
            if item["notes"]:
                st.caption(item["notes"])

with tab_people:
    st.subheader("الأطراف والأشخاص")
    with st.form("party_form"):
        name = st.text_input("الاسم")
        role = st.selectbox("الصفة في الملف", ["وارث", "مؤجر", "مستأجر", "مقاول", "متهم", "مجني عليه / مدعٍ", "شاهد", "خبير", "محامٍ", "جهة", "غير محددة"])
        relation = st.text_input("علاقته بالقضية أو الأصل")
        evidence = st.text_input("مصدر إثبات الاسم والصفة")
        if st.form_submit_button("إضافة شخص"):
            if name.strip():
                case["parties"].append({"name": name, "role": role, "relation": relation, "evidence": evidence})
                st.success("تمت إضافة الشخص.")
    for person in case["parties"]:
        st.markdown(f"<div class='card'><b>{render_text(person['name'])}</b> — {render_text(person['role'])}<br>{render_text(person['relation'])}<br><small>المصدر: {render_text(person['evidence'])}</small></div>", unsafe_allow_html=True)

with tab_assets:
    st.subheader("الأصول والعقارات")
    with st.form("asset_form"):
        asset = st.text_input("وصف الأصل / العقار")
        ownership = st.text_input("سند أو مصدر الملكية")
        holder = st.text_input("الحائز أو المدير الحالي")
        linked = st.text_input("المحررات أو القضايا المرتبطة")
        if st.form_submit_button("إضافة أصل"):
            if asset.strip():
                case["assets"].append({"asset": asset, "ownership": ownership, "holder": holder, "linked": linked})
                st.success("تمت إضافة الأصل.")
    for item in case["assets"]:
        st.markdown(f"<div class='card'><b>{render_text(item['asset'])}</b><br>الملكية: {render_text(item['ownership'])}<br>الحيازة: {render_text(item['holder'])}<br>الارتباطات: {render_text(item['linked'])}</div>", unsafe_allow_html=True)

with tab_timeline:
    st.subheader("الخط الزمني")
    with st.form("timeline_form"):
        event_date = st.date_input("تاريخ الحدث")
        event = st.text_area("الحدث أو الإجراء")
        source = st.text_input("مصدر الحدث: محرر، شخص، سجل...")
        if st.form_submit_button("إضافة حدث"):
            if event.strip():
                case["timeline"].append({"date": str(event_date), "event": event, "source": source})
                case["timeline"].sort(key=lambda x: x["date"])
                st.success("تمت إضافة الحدث.")
    for item in case["timeline"]:
        st.markdown(f"- **{item['date']}** — {render_text(item['event'])} _(المصدر: {render_text(item['source'])})_", unsafe_allow_html=True)

with tab_review:
    st.subheader("أسئلة قبل أي رأي")
    st.write("استخدم هذه المساحة لتسجيل ما يحتاج إجابة من المستخدم أو المحامين؛ لا ننتقل إلى استنتاج نهائي مع وجود فجوات جوهرية.")
    question = st.text_input("سؤال جديد")
    if st.button("إضافة سؤال") and question.strip():
        case["questions"].append({"question": question, "answered": False})
    for q in case["questions"]:
        st.checkbox(q["question"], value=q["answered"], key=f"q_{id(q)}")
    st.divider()
    st.session_state.model_choice = st.selectbox("نموذج التحليل الاختياري", ["gemini-2.5-flash", "gemini-2.5-pro"])
    if st.button("إنشاء مسودة مراجعة منظمة"):
        generate_review()
    for report in reversed(case["reports"]):
        with st.expander(f"مسودة مراجعة — {report['date']}", expanded=True):
            st.markdown(report["text"])
    st.download_button("تنزيل نسخة JSON من الملف", data=json.dumps(case, ensure_ascii=False, indent=2), file_name="family_legal_case.json", mime="application/json")

st.divider()
if st.button("مسح بيانات الجلسة الحالية"):
    st.session_state.case = blank_case()
    st.rerun()
"