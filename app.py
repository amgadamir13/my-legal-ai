import streamlit as st
import os
import fitz
import openai

# --- 1. SETUP & STYLE ---
st.set_page_config(page_title="Legal Vault", layout="centered")

# --- 2. SIDEBAR (API KEY) ---
with st.sidebar:
    st.header("🔑 Authentication")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    st.divider()
    if st.button("♻️ Refresh Documents"):
        st.cache_data.clear()
        st.success("Docs Re-indexed!")

st.title("⚖️ Legal Commander")

# --- 3. DATA LOADING ---
DOCS_PATH = "./documents"
if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)

@st.cache_data
def load_data():
    docs = {}
    for f in os.listdir(DOCS_PATH):
        try:
            path = os.path.join(DOCS_PATH, f)
            if f.endswith(".pdf"):
                with fitz.open(path) as doc:
                    docs[f] = [p.get_text() for p in doc]
        except: continue
    return docs

all_docs = load_data()

# --- 4. THE BULLETPROOF FORM (Solves the "No Enter" Issue) ---
# Wrapping everything in a 'form' creates a physical Submit button
with st.form("prosecutor_form", clear_on_submit=False):
    st.write("📝 **Step 1: Input your question** (Use 🎙️ on keyboard for Voice)")
    u_query = st.text_area("", placeholder="What does the contract say about the 2026 deadline?", height=150)
    
    st.write("🚀 **Step 2: Tap the button below**")
    submitted = st.form_submit_button("RUN LEGAL ANALYSIS")

    if submitted:
        if not api_key:
            st.error("Please enter your API Key in the sidebar.")
        elif not u_query:
            st.warning("Please enter a question first.")
        else:
            openai.api_key = api_key
            with st.spinner("Analyzing 50+ documents..."):
                # Simulating response for UI check
                st.success("Analysis Complete")
                st.markdown("### 🏛️ Official Findings")
                st.write("The AI logic is now triggered by the physical button above.")
