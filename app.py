import streamlit as st
import os
import fitz
import google.generativeai as genai
from fpdf import FPDF
import base64

# --- 1. SETUP & STYLE ---
st.set_page_config(page_title="Legal Vault (Gemini)", layout="centered")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("🔑 Vault Access")
    api_key = st.text_input("Enter Gemini API Key", type="password")
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
            st.error("Enter your Gemini API Key in the sidebar.")
        elif not u_query:
            st.warning("Enter a question.")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                with st.spinner("Gemini is reviewing files..."):
                    context = ""
                    for name, pages in all_docs.items():
                        for i, txt in enumerate(pages):
                            if any(w in txt.lower() for w in u_query.lower().split()[:3]):
                                context += f"\n[Doc: {name}, p.{i+1}]\n{txt[:800]}\n"

                    prompt = f"Prosecutor Mode: Cite [File, p.X]. Answer in user language.\n\nEvidence:\n{context}\n\nQuestion: {u_query}"
                    response = model.generate_content(prompt)
                    
                    st.session_state['last_analysis'] = response.text
                    st.markdown("---")
                    st.subheader("🏛️ Findings")
                    st.write(response.text)

            except Exception as e:
                st.error(f"Gemini Error: {str(e)}")

# --- 5. EXPORT TO PDF ---
if 'last_analysis' in st.session_state:
    if st.button("📄 Export Findings to PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, st.session_state['last_analysis'].encode('latin-1', 'ignore').decode('latin-1'))
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="Legal_Analysis.pdf" style="text-decoration:none;"><button style="width:100%; height:3em; background-color:#4CAF50; color:white; border:none; border-radius:15px; font-weight:bold;">📥 DOWNLOAD PDF TO IPHONE</button></a>'
        st.markdown(href, unsafe_allow_html=True)
