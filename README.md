# Talk To Pdfs-LLM-Chatbot

## Live Application Links
[![codelab](https://img.shields.io/badge/codelabs-4285F4?style=for-the-badge&logo=codelabs&logoColor=white)](https://codelabs-preview.appspot.com/?file_id=1onzZthH2AI72qgMpsv3t4V8WDCT_bsVicoxIT6cvyBg#0)
* Fastapi(Not Live): http://34.46.62.44:8502
* Streamlit(Not Live): http://34.46.62.44:8000/docs

## Technologies Used
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)](https://fastapi.tiangolo.com/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-000000?style=for-the-badge&logoWidth=20&logo=https://github.com/user-attachments/assets/01abd2ed-5664-4bea-a523-eb13dbfec54b)](https://github.com/BerriAI/litellm)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-003B57?style=for-the-badge&logo=python&logoColor=white)](https://pymupdf.readthedocs.io/)
[![Amazon AWS](https://img.shields.io/badge/Amazon_AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/)
[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Claude](https://img.shields.io/badge/Claude-2E2E3A?style=for-the-badge&logo=Anthropic&logoColor=white)](https://www.anthropic.com/)
[![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)

## Overview

This project enhances a document analysis pipeline by integrating Large Language Models (LLMs) to provide intelligent summarization and Q&A capabilities. It features a Streamlit frontend, FastAPI backend, and LiteLLM integration, all containerized with Docker and deployed on DigitalOcean for a scalable, real-time solution.

## PROBLEM STATEMENT

With the growth of digital documents, especially PDFs, extracting relevant information from lengthy files has become time-consuming. Build an intelligent document analysis system for automated summarization and Q&A tasks.

## Project Goals
* Enable document summarization using Large Language Models (LLMs)
* Provide context-aware Q&A based on uploaded PDFs
* Seamlessly integrate LLMs via LiteLLM for efficient communication
* Use a containerized architecture with Docker for scalable deployment
* Ensure real-time processing, low latency, and accuracy in document interactions

## **ARCHITECTURE DIAGRAM:**

![Assignment4_Part1](https://github.com/user-attachments/assets/8141654a-bff3-4cf1-91b3-c49dc01e4d2b)

## **DIRECTORY STRUCTURE**
```
BigData_Assignment04.1/
│
├── backend/
│   ├── .env
│   ├── Dockerfile
│   ├── main.py                     
│   ├── llm_chat.py                
│   ├── pdf_extractor.py           
│   ├── pdf_markdown_convertor.py  
│   ├── requirements.txt          
│
├── frontend/
│   ├── app.py                     
│   ├── config.toml
│   ├── Dockerfile
│   ├── requirements.txt                 
│
├── .gitignore
├── docker-compose.yaml           
├── README.md
```

## Prerequisites
Before running this project, ensure you have the following prerequisites set up:

- **Python**: Ensure Python is installed on your system.
- **Docker**: Ensure Docker-desktop is installed on your system.
- **Virtual Environment**: Set up a virtual environment to manage dependencies and isolate your project's environment from other Python projects. You can create a virtual environment using `virtualenv` or `venv`.
- **requirements.txt**: Install the required Python dependencies by running the command:
  ```
  pip install -r requirements.txt
  ```
- Redis: Installed locally or access to a hosted instance.
- API Keys: Add your OpenAI / Claude / Gemini keys to the .env file.
- Ports: Ensure ports 8000 (FastAPI) and 8502 (Streamlit) are free.

## How to run this application
1. Clone the Repository
```
git clone https://github.com/your-username/Talk-To-PDFs-LLM-Chatbot.git
cd Talk-To-PDFs-LLM-Chatbot
```
2. Set Up Environment Configuration
In both backend/ and frontend/ folders, create a .env file with the following variables:
```
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key
CLAUDE_API_KEY=your_key
REDIS_HOST=localhost
REDIS_PORT=6379
LITELLM_API_BASE=https://your-litellm-endpoint
```
3. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate on MacOS # or venv\Scripts\activate on Windows
```

4. Then install the required packages from both folders:
```
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```
5. Ensure Redis is Running: Start Redis locally or use a hosted instance as configured in your .env.

6. Run the Application with Docker, Build and start all services using Docker Compose:
```
docker-compose up --build
```
7. Access the Interfaces
  * FastAPI docs: http://localhost:8000/docs
  * Streamlit app: http://localhost:8502

## **REFERENCES**

1. https://docs.streamlit.io/
2. https://fastapi.tiangolo.com/
3. https://fastapi.tiangolo.com/tutorial/body/
4. https://github.com/BerriAI/litellm
5. https://docs.litellm.ai/
6. https://redis.io/docs/data-types/streams/
7. https://redis-py.readthedocs.io/en/stable/
8. https://platform.openai.com/docs/guides/gpt
9. https://docs.aimlapi.com/api-references/text-models-llm/google/gemini-2.0-flash-exp
10. https://docs.anthropic.com/en/docs
11. https://docs.docker.com/
12. https://docs.docker.com/compose/
13. https://pymupdf.readthedocs.io/en/latest/





 






