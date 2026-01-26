import streamlit as st
import os
import fitz  
import pandas as pd
import re
import openai
from thefuzz import fuzz

# --- UI & VOICE CONFIG ---
st.set_page_config(page_title="Legal Commander", layout="centered")

# Custom CSS to make the input area look better for mobile
st.markdown("""
    <style>
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- THE PRIVATE SIDEBAR ---
with st.sidebar:
    st.header("🔐 Vault Security")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    st.divider()
    if st.button("♻️ Refresh & Index New Files"):
        st.cache_data.clear()
        st.success("Vault Updated with New Files!")

st.title("⚖️ Legal Commander Pro")

# --- DATA ENGINE ---
DOCS_PATH = "./documents"
if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)

@st.cache_data
def load_all_data():
    content = {}
    for f in os.listdir(DOCS_PATH):
        path = os.path.join(DOCS_PATH, f)
        try:
            if f.endswith(".pdf"):
                with fitz.open(path) as doc: content[f] = [p.get_text() for p in doc]
            elif f.endswith((".xlsx", ".csv")):
                df = pd.read_excel(path) if f.endswith(".xlsx") else pd.read_csv(path)
                content[f] = [df.to_string()]
        except: continue
    return content

data = load_all_data()

# --- MAIN INTERFACE ---
tab1, tab2, tab3 = st.tabs(["🔍 Analysis", "📅 Timeline", "📎 Court List"])

with tab1:
    st.caption("🎤 Tip: Tap the Microphone icon on your iPhone keyboard to dictate.")
    u_query = st.text_area("Consult Case (EN/AR):", placeholder="Ask a question or dictate your thoughts...", height=100)
    
    if st.button("🚀 ANALYZE CASE"):
        if not api_key:
            st.error("❌ Enter API Key in Sidebar.")
        elif not u_query:
            st.warning("⚠️ Enter a question.")
        else:
            openai.api_key = api_key
            with st.spinner("Prosecutor is cross-referencing files..."):
                # Retrieval Logic
                context = ""
                for name, pages in data.items():
                    for i, txt in enumerate(pages):
                        if any(w in txt.lower() for w in u_query.lower().split()[:3]):
                            context += f"\n[Doc: {name}, p.{i+1}]\n{txt[:800]}\n"
                
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a Prosecutor. Use [File, p.X] citations. Answer in user's language."},
                            {"role": "user", "content": f"Evidence:\n{context[:10000]}\n\nQuestion: {u_query}"}
                        ]
                    ).choices[0].message.content
                    
                    st.markdown("### 🏛️ Official Analysis")
                    st.write(response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    st.subheader("📅 Automated Timeline")
    # Date extraction logic...
    st.info(f"Currently indexing {len(data)} documents.")

with tab3:
    st.subheader("📁 Courtroom Checklist")
    st.checkbox("USB with Incident Videos")
    st.checkbox("Physical Case Folder")
