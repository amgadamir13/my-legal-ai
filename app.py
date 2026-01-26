import streamlit as st
import os, fitz, json, re
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- 1. SETUP ---
st.set_page_config(page_title="Legal Intelligence Terminal", layout="wide")

@st.cache_resource
def load_ai_models():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_ai_models()
DOCS_FOLDER = "documents" # Ensure this folder exists in GitHub

# --- 2. DOCUMENT ENGINE (WITH SAFETY GATES) ---
@st.cache_data
def process_legal_library():
    metadata = []
    texts = []
    
    # Check if folder exists
    if not os.path.exists(DOCS_FOLDER):
        return None, None
        
    for f in os.listdir(DOCS_FOLDER):
        if f.endswith(".pdf"):
            path = os.path.join(DOCS_FOLDER, f)
            try:
                with fitz.open(path) as doc:
                    for i, page in enumerate(doc):
                        content = page.get_text().strip()
                        if content:
                            metadata.append({"file": f, "page": i+1, "text": content})
                            texts.append(content)
            except:
                continue
    
    if not texts: 
        return None, None
    
    embeddings = embed_model.encode(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    return index, metadata

vector_index, doc_library = process_legal_library()

# --- 3. INTERFACE ---
st.title("⚖️ Legal Intelligence Terminal")

with st.sidebar:
    st.header("🔑 System Access")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    # Visual check for you
    if vector_index is None:
        st.error("❌ No documents found. Please upload PDFs to the 'documents' folder in GitHub.")
    else:
        st.success(f"✅ {len(doc_library)} Pages Indexed")

u_query = st.text_area("Audit Directive:", placeholder="Enter your question...", height=100)
audit_btn = st.button("EXECUTE STRATEGIC ANALYSIS", use_container_width=True)

# --- 4. THE STABILIZED ANALYSIS FLOW ---
if audit_btn:
    if not api_key:
        st.error("Please enter your API Key.")
    elif vector_index is None:
        st.error("The Intelligence Engine is empty. I have no documents to analyze.")
    elif not u_query:
        st.warning("Please enter a question.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        with st.spinner("⚖️ Executive Engine: Building Strategic Analysis..."):
            # SEARCHING
            query_vector = embed_model.encode([u_query])
            distances, indexes = vector_index.search(np.array(query_vector).astype('float32'), k=5)
            
            context_text = ""
            for idx in indexes[0]:
                if idx != -1: # Ensure it found a match
                    match = doc_library[idx]
                    context_text += f"\n[Source: {match['file']}, p.{match['page']}]\n{match['text'][:800]}\n"

            # PROMPTING
            prompt = f"Act as a Senior Legal Strategist. Use the Evidence: {context_text}\n\nQuestion: {u_query}"
            
            try:
                response = model.generate_content(prompt)
                st.divider()
                st.subheader("🏛️ Intelligence Report")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"AI Error: {str(e)}")
