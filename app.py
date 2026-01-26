import streamlit as st
import os
import fitz
from openai import OpenAI  # New v1.0.0+ syntax

# --- 1. SETUP & STYLE ---
st.set_page_config(page_title="Legal Vault", layout="centered")

# --- 2. SIDEBAR (API KEY) ---
with st.sidebar:
    st.header("🔑 Vault Access")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    st.divider()
    if st.button("♻️ Refresh Documents"):
        st.cache_data.clear()
        st.success("Docs Re-indexed!")

st.title("⚖️ Legal Commander Pro")

# --- 3. DATA ENGINE ---
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

# --- 4. THE INTERFACE ---
with st.form("prosecutor_form"):
    st.info(f"📁 Monitoring {len(all_docs)} files.")
    u_query = st.text_area("Consult Evidence:", placeholder="Ask or Dictate (🎙️)...", height=150)
    submitted = st.form_submit_button("⚖️ RUN ANALYSIS")

    if submitted:
        if not api_key:
            st.error("Enter API Key in Sidebar.")
        elif not u_query:
            st.warning("Enter a question.")
        else:
            try:
                # NEW OPENAI CLIENT LOGIC (Fixes the Error)
                client = OpenAI(api_key=api_key)
                
                with st.spinner("Prosecutor is reviewing files..."):
                    context = ""
                    for name, pages in all_docs.items():
                        for i, txt in enumerate(pages):
                            if any(w in txt.lower() for w in u_query.lower().split()[:3]):
                                context += f"\n[Doc: {name}, p.{i+1}]\n{txt[:800]}\n"

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a Prosecutor. Cite [File, p.X]. Answer in user language."},
                            {"role": "user", "content": f"Evidence:\n{context[:10000]}\n\nQuestion: {u_query}"}
                        ]
                    )
                    
                    st.markdown("---")
                    st.subheader("🏛️ Findings")
                    st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"Connection Error: {str(e)}")
