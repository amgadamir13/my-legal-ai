import streamlit as st
import os
import fitz
import openai
from thefuzz import fuzz

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Legal Vault", layout="centered")
st.markdown("<style>div.stButton > button:first-child { height: 3em; width: 100%; font-size: 20px; }</style>", unsafe_allow_html=True)

# --- 2. SIDEBAR (SECURITY & REFRESH) ---
with st.sidebar:
    st.header("🔑 Vault Access")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    st.divider()
    if st.button("♻️ Refresh & Sync Files"):
        st.cache_data.clear()
        st.success("Documents Sync Complete")

st.title("⚖️ Legal Commander Pro")

# --- 3. THE DATA ENGINE ---
DOCS_PATH = "./documents"
if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)

@st.cache_data
def load_and_index_docs():
    docs = {}
    for f in os.listdir(DOCS_PATH):
        path = os.path.join(DOCS_PATH, f)
        try:
            if f.endswith(".pdf"):
                with fitz.open(path) as doc:
                    docs[f] = [p.get_text() for p in doc]
            elif f.endswith((".xlsx", ".csv")):
                df = pd.read_excel(path) if f.endswith(".xlsx") else pd.read_csv(path)
                docs[f] = [df.to_string()]
        except: continue
    return docs

all_docs = load_and_index_docs()

# --- 4. THE PROSECUTOR INTERFACE ---
with st.form("prosecutor_form"):
    st.info(f"📁 Currently monitoring {len(all_docs)} files in the vault.")
    u_query = st.text_area("Consult the Evidence (EN/AR):", 
                          placeholder="Dictate using 🎙️ or type your legal question...", height=150)
    
    submitted = st.form_submit_button("⚖️ RUN LEGAL ANALYSIS")

    if submitted:
        if not api_key:
            st.error("Missing API Key. Please open the sidebar.")
        elif not u_query:
            st.warning("Please provide a question for the Prosecutor.")
        else:
            openai.api_key = api_key
            with st.spinner("Prosecutor is cross-referencing all 50+ files..."):
                # RAG: Search through files for context
                context = ""
                for name, pages in all_docs.items():
                    for i, txt in enumerate(pages):
                        if any(w in txt.lower() for w in u_query.lower().split()[:3]):
                            context += f"\n[Doc: {name}, p.{i+1}]\n{txt[:800]}\n"

                # AI Logic
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o", # Handles Arabic handwriting & logic
                        messages=[
                            {"role": "system", "content": "You are a Senior Prosecutor. Cite everything: [Filename, p.X]. If handwriting is messy, write [UNCLEAR]."},
                            {"role": "user", "content": f"Context Evidence:\n{context[:10000]}\n\nQuestion: {u_query}"}
                        ]
                    ).choices[0].message.content
                    
                    st.markdown("---")
                    st.subheader("🏛️ Official Prosecutor Findings")
                    st.write(response)
                    
                except Exception as e:
                    st.error(f"Vault Connection Error: {str(e)}")

# --- 5. TIMELINE TAB ---
with st.expander("📅 View Automated Case Timeline"):
    # Simple logic to show files by date modified if no dates in text
    st.caption("Sequence of evidence based on your file uploads:")
    for f in sorted(os.listdir(DOCS_PATH)):
        st.write(f"• {f}")
