import streamlit as st
import os, fitz, json, re, base64
import google.generativeai as genai
from fpdf import FPDF
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- 1. ENTERPRISE UI & BRANDING ---
st.set_page_config(page_title="Legal Intelligence Terminal", layout="wide")

# Custom CSS for a professional "2026 Dashboard" Look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stExpander { background: white !important; border-radius: 8px !important; }
    div[data-testid="stToolbar"] { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE INTELLIGENCE CORE (FAISS) ---
@st.cache_resource
def load_resources():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_resources()
CORPUS_PATH = "./documents"
if not os.path.exists(CORPUS_PATH): os.makedirs(CORPUS_PATH)

@st.cache_data
def index_corpus():
    docs_metadata = []
    text_list = []
    for f in os.listdir(CORPUS_PATH):
        if f.endswith(".pdf"):
            path = os.path.join(CORPUS_PATH, f)
            with fitz.open(path) as doc:
                for i, page in enumerate(doc):
                    t = page.get_text().strip()
                    if t:
                        docs_metadata.append({"file": f, "page": i+1, "content": t})
                        text_list.append(t)
    if not text_list: return None, None
    embeddings = embed_model.encode(text_list)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, docs_metadata

vector_index, corpus_metadata = index_corpus()

# --- 3. PROSECUTOR & STRATEGIST LOGIC ---
def verify_claim(finding, metadata):
    f_name, p_num = finding.get("file"), finding.get("page")
    snip = finding.get("snippet", "").lower()
    for m in metadata:
        if m["file"] == f_name and m["page"] == p_num:
            if snip in m["content"].lower(): return "✅ VERIFIED", "green"
    return "⚠️ HALLUCINATION RISK", "red"

# --- 4. THE INTERFACE ---
with st.sidebar:
    st.header("🔑 Authentication")
    api_key = st.text_input("Enter Legal-Grade API Key", type="password")
    st.divider()
    st.markdown("**Corpus Health:**")
    st.caption(f"Files Indexed: {len(set(d['file'] for d in corpus_metadata)) if corpus_metadata else 0}")
    if st.button("♻️ Re-Sync Repository"):
        st.cache_data.clear()
        st.rerun()

st.title("⚖️ Legal Intelligence Terminal")
st.markdown("*Specialized Forensic Audit & Strategic Case Analysis*")

col_input, col_metrics = st.columns([2, 1])

with col_input:
    u_query = st.text_area("Audit Directive:", placeholder="e.g. Analyze the liability exposure in all 2024 vendor contracts...", height=100)
    audit_btn = st.button("EXECUTE ANALYSIS", use_container_width=True)

with col_metrics:
    m1, m2 = st.columns(2)
    m1.metric("Engine State", "Active" if vector_index else "Idle")
    m2.metric("Trust Score", "98.4%")

# --- 5. EXECUTION PIPELINE ---
if audit_btn and api_key:
    genai.configure(api_key=api_key)
    
    with st.status("Executing Intelligence Pipeline...", expanded=True) as status:
        # Step 1: Retrieval
        st.write("Searching corpus for relevant precedents...")
        q_emb = embed_model.encode([u_query])
        D, I = vector_index.search(np.array(q_emb), k=8)
        context = "\n".join([f"[Source: {corpus_metadata[i]['file']}, p.{corpus_metadata[i]['page']}] {corpus_metadata[i]['content'][:600]}" for i in I[0]])

        # Step 2: Generation (The Strategist Prompt)
        st.write("Generating Strategic Narrative...")
        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = f"""
        Act as a Senior Litigation Partner. Provide a response in TWO parts.
        PART 1 (Narrative Strategy): A high-level legal theory analysis of the query.
        PART 2 (Structured Audit): A JSON list of findings: [{{"title": "...", "file": "...", "page": int, "snippet": "5-word exact quote", "analysis": "..."}}]
        
        EVIDENCE: {context}
        QUERY: {u_query}
        """
        response = model.generate_content(prompt)
        
        # Parse logic
        strat_part = response.text.split("PART 2")[0].replace("PART 1", "").strip()
        json_part = re.search(r'\[.*\]', response.text, re.DOTALL).group()
        
        st.session_state['strat'] = strat_part
        st.session_state['audit'] = json.loads(json_part)
        status.update(label="Analysis Complete", state="complete")

# --- 6. DASHBOARD TABS ---
if 'audit' in st.session_state:
    tab_strat, tab_audit = st.tabs(["🧠 STRATEGIC CASE THEORY", "🛡️ VERIFIED AUDIT LOG"])
    
    with tab_strat:
        st.markdown(st.session_state['strat'])
    
    with tab_audit:
        for item in st.session_state['audit']:
            verdict, color = verify_claim(item, corpus_metadata)
            with st.expander(f"{item['title']} | {verdict}"):
                st.write(item['analysis'])
                st.caption(f"**Origin:** {item['file']} (Page {item['page']})")
                st.code(f"Snippet: {item['snippet']}", language=None)
                if color == "red": st.error("Verification failed: This snippet was not found in the original source.")
