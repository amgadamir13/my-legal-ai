import streamlit as st
import os
import fitz  # PDF
import pandas as pd
import re
import openai
from thefuzz import fuzz
from PIL import Image

# --- 1. PROSECUTOR & VERIFICATION LOGIC ---
def verify_evidence(ai_response, docs_data):
    citation_pattern = r"\[(.*?),\s*p\.\s*(\d+)\]"
    matches = re.findall(citation_pattern, ai_response)
    results = []
    for doc_name, page_num in matches:
        try:
            p_idx = int(page_num) - 1
            if doc_name in docs_data and p_idx < len(docs_data[doc_name]):
                actual = docs_data[doc_name][p_idx].lower()
                claim = ai_response.split(f"[{doc_name}")[0].strip().split('.')[-1][-150:].lower()
                score = fuzz.token_set_ratio(claim, actual)
                status = "PASS" if score > 75 else "FAIL"
                reason = "Text match confirmed" if status == "PASS" else "Text mismatch or unclear handwriting"
                results.append({"citation": f"{doc_name} (p.{page_num})", "status": status, "score": score, "reason": reason})
        except: continue
    return results

# --- 2. THE UI CONFIG ---
st.set_page_config(page_title="Legal Commander", layout="centered")
st.markdown("<style>.stButton>button {width:100%; border-radius:15px; height:3em; font-weight:bold;}</style>", unsafe_allow_html=True)

st.title("⚖️ Legal Commander Pro")

with st.sidebar:
    st.header("🔑 Security")
    api_key = st.text_input("OpenAI API Key", type="password")
    st.divider()
    st.caption("Mode: Prosecutor (Strict Accuracy)")

# --- 3. DATA ENGINE ---
DOCS_PATH = "./documents"
if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)

@st.cache_data
def load_and_index():
    docs = {}
    for f in os.listdir(DOCS_PATH):
        path = os.path.join(DOCS_PATH, f)
        try:
            if f.endswith(".pdf"):
                with fitz.open(path) as doc: docs[f] = [p.get_text() for p in doc]
            elif f.endswith((".xlsx", ".csv")):
                df = pd.read_excel(path) if f.endswith(".xlsx") else pd.read_csv(path)
                docs[f] = [df.to_string()]
        except: continue
    return docs

all_docs = load_and_index()

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["🔍 Analysis", "📅 Timeline", "📎 Attachments"])

with tab1:
    u_query = st.text_input("Consult Case (EN/AR):", placeholder="Ask about dates, contracts, or evidence...")
    
    if st.button("🚀 ANALYZE CASE"):
        if not api_key:
            st.error("Please enter your API Key in the sidebar.")
        elif not u_query:
            st.warning("Please type a question.")
        else:
            openai.api_key = api_key
            with st.spinner("Prosecutor is reviewing 50+ documents..."):
                # Context Retrieval (Parent Logic)
                context = ""
                for name, pages in all_docs.items():
                    for i, txt in enumerate(pages):
                        if any(w in txt.lower() for w in u_query.lower().split()[:3]):
                            context += f"\n[Doc: {name}, p.{i+1}]\n{txt[:1000]}\n"
                
                # AI Prosecution
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a Senior Prosecutor. Cite everything: [Filename, p. X]. If handwriting is messy, write [UNCLEAR]."},
                        {"role": "user", "content": f"Context:\n{context[:10000]}\n\nQuestion: {u_query}"}
                    ]
                ).choices[0].message.content
                
                st.markdown("### 🏛️ Official Analysis")
                st.write(response)
                
                # The Prosecutor UI logic for Verification
                st.divider()
                st.subheader("🛡️ Evidence Audit")
                v_results = verify_evidence(response, all_docs)
                for res in v_results:
                    if res["status"] == "PASS":
                        st.success(f"Verified: {res['citation']} (Confidence: {res['score']}%)")
                    else:
                        st.error(f"Hallucination Warning: {res['citation']} - {res['reason']}")

with tab2:
    st.subheader("📅 Automated Case Timeline")
    # Search logic for dates
    all_text = " ".join([txt for pages in all_docs.values() for txt in pages])
    dates = re.findall(r'(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})', all_text)
    if dates:
        for d in sorted(list(set(dates)), reverse=True):
            st.write(f"• **{d}**: Referenced in Case Files")
    else: st.info("No clear dates found in documents yet.")

with tab3:
    st.subheader("📁 Courtroom Packing List")
    st.checkbox("USB: Incident Videos (3) and Digital Photos")
    st.checkbox("Original Signed Contracts (Blue Ink)")
    st.checkbox("Printed Evidence Bundle")
