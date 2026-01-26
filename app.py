import streamlit as st
import os, fitz, json
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- 1. SETUP ---
st.set_page_config(page_title="Legal Intelligence Terminal", layout="wide")

@st.cache_resource
def load_brain_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_brain_model()
DOCS_FOLDER = "documents"

# --- 2. THE STABILIZED DOCUMENT ENGINE ---
@st.cache_data
def build_document_index():
    metadata = []
    texts = []
    
    # Create folder if it's missing (helps local testing)
    if not os.path.exists(DOCS_FOLDER):
        os.makedirs(DOCS_FOLDER)
        return None, None
        
    # Read every PDF
    files = [f for f in os.listdir(DOCS_FOLDER) if f.lower().endswith(".pdf")]
    
    if not files:
        return None, None

    for f in files:
        path = os.path.join(DOCS_FOLDER, f)
        try:
            with fitz.open(path) as doc:
                for i, page in enumerate(doc):
                    content = page.get_text().strip()
                    if content:
                        metadata.append({"file": f, "page": i+1, "text": content})
                        texts.append(content)
        except Exception:
            continue
    
    if not texts: 
        return None, None
    
    # Mathematical Search Engine (FAISS)
    embeddings = embed_model.encode(texts)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype('float32'))
    return index, metadata

# Initialize the library
vector_index, doc_library = build_document_index()

# --- 3. THE PROFESSIONAL INTERFACE ---
st.title("⚖️ Legal Intelligence Terminal")

with st.sidebar:
    st.header("🔑 System Access")
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    
    # Status Indicators
    if vector_index is None:
        st.error("⚠️ Corpus Empty: Upload PDFs to the 'documents' folder on GitHub.")
    else:
        st.success(f"✅ Active: {len(doc_library)} Pages Processed")
    
    if st.button("♻️ Force Re-Sync"):
        st.cache_data.clear()
        st.rerun()

# Layout
u_query = st.text_area("Audit Directive (Strategic Question):", height=120)
audit_btn = st.button("EXECUTE ANALYSIS", use_container_width=True)

# --- 4. THE SAFE EXECUTION ---
if audit_btn:
    if not api_key:
        st.error("Error: Gemini API Key is missing.")
    elif vector_index is None:
        st.error("Error: No document data found. Please check your 'documents' folder on GitHub.")
    elif not u_query:
        st.warning("Please enter a directive or question.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            with st.spinner("⚖️ Building Strategic Case Theory..."):
                # SEARCH
                query_vec = embed_model.encode([u_query])
                distances, indexes = vector_index.search(np.array(query_vec).astype('float32'), k=5)
                
                # PREPARE CONTEXT
                context = ""
                for idx in indexes[0]:
                    if idx != -1:
                        m = doc_library[idx]
                        context += f"\n[Doc: {m['file']}, p.{m['page']}]\n{m['text'][:1000]}\n"

                # STRATEGIC PROMPT
                prompt = f"""
                Analyze the Evidence like a Senior Legal Partner.
                Provide:
                1. SUMMARY: The core answer.
                2. THEORY: The strategic implication.
                3. FINDINGS: Citations with file names.
                
                Evidence: {context}
                Question: {u_query}
                """
                
                response = model.generate_content(prompt)
                st.markdown("---")
                st.subheader("🏛️ Strategic Intelligence Report")
                st.markdown(response.text)
        except Exception as e:
            st.error(f"System Error: {str(e)}")
