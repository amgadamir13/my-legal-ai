import streamlit as st
import os
import fitz # PDF
import pandas as pd # Excel
import openai
from verification import verify_citations

# UI SETUP
st.set_page_config(page_title="Legal Commander", layout="wide")
st.title("⚖️ Legal Case Commander")

# SIDEBAR: Folder Logic
DOCS_FOLDER = "./documents"
if not os.path.exists(DOCS_FOLDER):
    os.makedirs(DOCS_FOLDER)

# 1. LOAD DATA (PDF & EXCEL)
def load_data():
    all_content = {}
    for file in os.listdir(DOCS_FOLDER):
        path = os.path.join(DOCS_FOLDER, file)
        if file.endswith(".pdf"):
            doc = fitz.open(path)
            all_content[file] = [page.get_text() for page in doc]
        elif file.endswith(".xlsx") or file.endswith(".csv"):
            df = pd.read_excel(path) if file.endswith(".xlsx") else pd.read_csv(path)
            all_content[file] = [df.to_string()]
    return all_content

# 2. APP TABS
tab_chat, tab_time, tab_court = st.tabs(["🔍 Analysis", "📅 Timeline", "📎 Attachments"])

with tab_chat:
    query = st.text_input("Ask a question about your 50+ docs (AR/EN):")
    if query:
        st.info("Searching through documents...")
        # Simulating AI Response for UI layout
        response = "The contract specifies a 30-day notice [Contract_A.pdf, p. 5]. The handwriting on page 2 is [UNCLEAR]."
        st.write(response)
        
        # Run Verification
        results = verify_citations(response, load_data())
        for r in results:
            color = "green" if r['verified'] else "red"
            st.markdown(f":{color}[{r['source']} p.{r['page']} - Match: {r['score']}%]")

with tab_time:
    st.subheader("Case Event Sequence")
    # This would be populated by AI date extraction
    st.write("- **Jan 20, 2026**: Contract Signed (Verified)")
    st.write("- **Feb 15, 2026**: Potential Dispute (Estimate based on Letter_B.pdf)")

with tab_court:
    st.subheader("Required for Court Tomorrow")
    st.checkbox("USB with 3 Videos")
    st.checkbox("Printed Evidence Photos (Set of 5)")
    st.checkbox("Physical Case Folder #102")
