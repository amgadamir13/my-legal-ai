 import streamlit as st
import google.generativeai as genai

# 1. Page Configuration
st.set_page_config(page_title="AI Legal Consultant", page_icon="⚖️")
st.title("⚖️ Private Legal AI")

# 2. Secure API Connection
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 3. Legal Persona System Instructions
    instructions = """
    You are a high-level Legal Consultant. 
    1. Tone: Professional, precise, and empathetic. 
    2. Format: Use bolding for key terms and bullet points for clarity.
    3. Strategy: Analyze risks, identify loopholes, and provide actionable next steps.
    4. Constraint: Always clarify you are an AI, not a human attorney.
    """

    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=instructions
    )

    # 4. Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 5. Fixed "Save History" Button
    # This button appears at the top once you start talking
    if st.session_state.messages:
        chat_text = ""
        for m in st.session_state.messages:
            chat_text += f"{m['role'].upper()}: {m['content']}\n\n"
        
        st.download_button(
            label="📥 Download Consultation History",
            data=chat_text,
            file_name="legal_consultation.txt",
            mime="text/plain"
        )
        st.divider()

    # 6. Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 7. Chat Input Logic
    if prompt := st.chat_input("How can I assist you with your legal query?"):
        # Display User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and Display AI Response
        with st.chat_message("assistant"):
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

else:
    st.error("Missing API Key! Please add 'GEMINI_API_KEY' to your Streamlit Secrets.")
