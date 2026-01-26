import streamlit as st
import google.generativeai as genai

# Setup
st.set_page_config(page_title="AI Legal Consultant", page_icon="⚖️")
st.title("⚖️ Private Legal AI")

# Securely grab your API Key from Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Chat History Setup
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # User Input
    if prompt := st.chat_input("Explain this clause to me..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        response = model.generate_content(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.chat_message("assistant").write(response.text)
else:
    st.error("Please add your GEMINI_API_KEY to the Streamlit Secrets!")
