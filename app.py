import streamlit as st
import os, fitz, json, re
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- 1. PROFESSIONAL DASHBOARD SETUP ---
st.set_page_config(page_title="Legal Intelligence Terminal", layout="wide")

@st.cache_resource
def load_ai_models():
    # This is the "brain" that helps the AI understand your documents
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_ai_models()
DOCS_FOLDER = "./documents"
if not os.path.exists(DOCS_FOLDER): os.makedirs(DOCS_FOLDER)

# --- 2. THE DOCUMENT ENGINE ---
@st.cache_data
def process_legal_library():
    metadata = []
    texts = []
    for f in os.listdir(DOCS_FOLDER):
        if f.endswith(".pdf"):
            path = os.path.join(DOCS_FOLDER, f)
            with fitz.open(path) as doc:
                for i, page in enumerate(doc):
                    content = page.get_text().strip()
                    if content:
                        metadata.append({"file": f, "page": i+1, "text": content})
                        texts.append(content)
    
    if not texts: return None, None
    
    # Building the "Search Index" for 50+ docs
    embeddings = embed_model.encode(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, metadata

vector_index, doc_library = process_legal_library()

# --- 3. THE INTERFACE ---
st.title("⚖️ Legal Intelligence Terminal")
st.markdown("### *Forensic Audit & Strategic Analysis Dashboard*")

with st.sidebar:
    st.header("🔑 System Access")
    api_key = st.text_input("Gemini API Key", type="password")
    if st.button("♻️ Refresh Document Library"):
        st.cache_data.clear()
        st.rerun()

# Layout
u_query = st.text_area("Audit Directive (Your Question):", placeholder="e.g., Explain the termination risks in these contracts...", height=100)
audit_btn = st.button("EXECUTE STRATEGIC ANALYSIS", use_container_width=True)

# --- 4. ANALYSIS FLOW ---
if audit_btn and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    with st.spinner("Analyzing Evidence and Building Strategy..."):
        # Find the best matches in your 50+ docs
        query_vector = embed_model.encode([u_query])
        distances, indexes = vector_index.search(np.array(query_vector), k=10)
        
        context_text = ""
        for idx in indexes[0]:
            match = doc_library[idx]
            context_text += f"\n[Doc: {match['file']}, p.{match['page']}]\n{match['text'][:800]}\n"

        # The "Strategist" Prompt (Mimicking the link you liked)
        prompt = f"""
        Act as a Senior Legal Strategist. 
        Provide a response with the following sections:
        1. EXECUTIVE SUMMARY: A high-level view.
        2. CASE THEORY: The strategic interpretation of the facts.
        3. EVIDENTIARY AUDIT: Specific findings with [File, p.X] citations.
        
        Evidence from Corpus:
        {context_text}
        
        Legal Inquiry: {u_query}
        """
        
        response = model.generate_content(prompt)
        
        # Display Results
        st.divider()
        st.subheader("🏛️ Strategic Analysis")
        st.markdown(response.text)
