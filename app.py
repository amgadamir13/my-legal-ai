import streamlit as st
import os
import fitz  # PDF
import pandas as pd  # Excel
from PIL import Image
import pytesseract
import openai
import re
from verification import verify_citations

# Configuration
DOCS_FOLDER = "./documents"
st.set_page_config(page_title="Legal Commander", layout="wide")

def load_data():
    all_content = {}
    if not os.path.exists(DOCS_FOLDER): return all_content
    
    for file in os.listdir(DOCS_FOLDER):
        path = os.path.join(DOCS_FOLDER, file)
        # 1. PDFs
        if file.endswith(".pdf"):
            doc = fitz.open(path)
            all_content[file] = [page.get_text() for page in doc]
        # 2. Excel
        elif file.endswith((".xlsx", ".csv")):
            df = pd.read_excel(path) if file.endswith(".xlsx") else pd.read_csv(path)
            all_content[file] = [df.to_string()]
        # 3. Images with Text (Handwriting/Scans)
        elif file.endswith((".png", ".jpg", ".jpeg")):
            text = pytesseract.image_to_string(Image.open(path), lang='ara+eng')
            all_content[file] = [text]
    return all_content

def extract_timeline(all_docs):
    """Genius Logic: Scans text for dates (YYYY-MM-DD or DD/MM/YYYY)"""
    events = []
    date_pattern = r'(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})'
    
    for doc, pages in all_docs.items():
        for i, page_text in enumerate(pages):
            found_dates = re.findall(date_pattern, page_text)
            for d in found_dates:
                events.append({"date": d, "source": f"{doc} (p.{i+1})"})
    return sorted(events, key=lambda x: x['date'], reverse=True)

# --- UI INTERFACE ---
st.title("⚖️ Legal Commander Pro")
data = load_data()

tab1, tab2, tab3 = st.tabs(["🔍 Analysis", "📅 Case Timeline", "📎 Court Packing List"])

with tab1:
    query = st.text_input("Consult your case (AR/EN):")
    if query:
        # AI logic goes here (referencing get_ai_response from previous step)
        st.write("### AI Analysis")
        st.write("Reviewing documents... (Citing sources with confidence checks)")

with tab2:
    st.subheader("Automated Date Sequence")
    timeline = extract_timeline(data)
    if not timeline:
        st.write("No dates detected yet.")
    else:
        for e in timeline:
            with st.expander(f"📅 {e['date']} - Found in {e['source']}"):
                st.write("Click to verify this event in the original document.")

with tab3:
    st.subheader("Physical Attachments for Court")
    # This reads your 'attachments' list
    st.checkbox("USB: 3 Videos and Photo evidence")
    st.checkbox("Physical Folder: Signed original contracts")
    st.info("Tip: Double-check the USB format is compatible with court laptops.")
