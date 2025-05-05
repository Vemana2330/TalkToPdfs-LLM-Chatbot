# frontend/app.py
 
import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
 
# Load environment variables
load_dotenv()
 
# Backend API Endpoints
UPLOAD_URL = "http://localhost:8000/upload_pdf/"
CHAT_URL = "http://localhost:8000/chat/"
FETCH_MARKDOWN_URL = "http://localhost:8000/fetch_markdown_files/"
GET_MARKDOWN_CONTENT_URL = "http://localhost:8000/get_markdown_content/"
GET_IMAGES_URL = "http://localhost:8000/get_images/"  # API to fetch images
 
# Sidebar Navigation
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to:", ["Upload & Convert PDF", "Use Existing Markdown"])

# LLM Options
LLM_OPTIONS = ["GPT-4o Mini", "Gemini Flash Free", "DeepSeek", "Claude-3.5 Haiku"]
 
########################################
#      PAGE 1: Upload & Convert PDF    #
########################################
if page == "Upload & Convert PDF":
    st.title("📄 PDF & Markdown Chatbot with LLM")
 
    st.header("📂 Upload a PDF for Processing")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        with st.spinner("⏳ Extracting PDF content..."):
            files = {"file": uploaded_file}
            response = requests.post(UPLOAD_URL, files=files)
            
            if response.status_code == 200:
                pdf_data = response.json()
                pdf_name = pdf_data["s3_folder"].strip('/')  # Ensure no trailing slashes
                st.success(f"✅ PDF '{uploaded_file.name}' processed and uploaded to S3 successfully!")
 
                # Extract correct Markdown filename from backend response
                md_filename = pdf_data.get("markdown_filename", uploaded_file.name.replace('.pdf', '.md'))
 
                # Display extracted Markdown content
                markdown_url = pdf_data.get("markdown_url")
                if markdown_url:
                    
 
                    # Fetch Markdown content using correct filename
                    markdown_response = requests.post(
                        GET_MARKDOWN_CONTENT_URL,
                        json={"pdf_name": pdf_name, "markdown_filename": md_filename}
                    )
                    if markdown_response.status_code == 200:
                        extracted_md = markdown_response.json().get("markdown_content", "")
                        st.text_area("📄 Extracted Markdown Content", extracted_md, height=300)
                    else:
                        st.warning(f"⚠️ Unable to fetch Markdown content for {md_filename}.")
 
            else:
                st.error("❌ Failed to process PDF")
 
########################################
#    PAGE 2: Use Existing Markdown     #
########################################
elif page == "Use Existing Markdown":
    st.title("📁 Select a Markdown File from S3")
 
    # Fetch available Markdown files from S3
    def fetch_markdown_files():
        response = requests.get(FETCH_MARKDOWN_URL)
        if response.status_code == 200:
            return response.json().get("markdown_files", {})
        return {}
 
    markdown_files = fetch_markdown_files()
 
    if markdown_files:
        selected_pdf = st.selectbox("📁 Select a PDF Folder:", list(markdown_files.keys()))
 
        if selected_pdf and selected_pdf in markdown_files:
            selected_md = st.selectbox("📜 Select a Markdown File:", markdown_files[selected_pdf])
 
            # Choose between Text Summary and Chat
            action_choice = st.radio("🔍 Choose Action:", ["Text Summary", "Chat with LLM"])
 
            if action_choice == "Text Summary":
                llm_choice = st.selectbox("🤖 Select LLM for Summary:", LLM_OPTIONS)
                
                if st.button("📄 Generate Summary"):
                    with st.spinner("⏳ Summarizing Markdown..."):
                        response = requests.post(
                            CHAT_URL,
                            json={
                                "question": "Summarize this document.",
                                "pdf_name": selected_pdf,
                                "markdown_filename": selected_md,
                                "llm_choice": llm_choice,
                                "text_summary": True  # Summary mode enabled
                            }
                        )
                        if response.status_code == 200:
                            response_data = response.json()
                            summary = response.json().get("answer", "No summary available.")
                            input_tokens = response_data.get("input_tokens", "N/A")
                            output_tokens = response_data.get("output_tokens", "N/A")
                            cost = response_data.get("cost", "N/A")

                            st.write(summary)
                            st.write(f"📊 **Input Tokens:** {input_tokens}, **Output Tokens:** {output_tokens}, **Cost:** ${cost:.6f}")
                        else:
                            st.error(f"❌ Failed to generate summary: {response.text}")
 
            elif action_choice == "Chat with LLM":
                llm_choice = st.selectbox("🤖 Select LLM for Chat:", LLM_OPTIONS)
                user_question = st.text_input("📝 Ask a question about the document:")
 
                if st.button("🚀 Send Question"):
                    with st.spinner("⏳ Generating answer..."):
                        response = requests.post(
                            CHAT_URL,
                            json={
                                "question": user_question,
                                "pdf_name": selected_pdf,
                                "markdown_filename": selected_md,
                                "llm_choice": llm_choice,
                                "text_summary": False  # Chat mode enabled
                            }
                        )
                        if response.status_code == 200:
                            response_data = response.json()
                            answer = response.json().get("answer", "No answer received.")
                            input_tokens = response_data.get("input_tokens", "N/A")
                            output_tokens = response_data.get("output_tokens", "N/A")
                            cost = response_data.get("cost", "N/A")
                            
                            st.write("💡 **Answer:**", answer)
                            st.write(f"📊 **Input Tokens:** {input_tokens}, **Output Tokens:** {output_tokens}, **Cost:** ${cost:.6f}")
                        else:
                            st.error("❌ Error from backend: " + response.text)
 
    else:
        st.warning("⚠️ No Markdown files found in S3.")