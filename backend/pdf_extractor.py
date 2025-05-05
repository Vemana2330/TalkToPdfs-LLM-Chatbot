# backend/pdf_extractor.py

import PyPDF2
import camelot
import json
import re

def clean_text(text):
    """Removes excessive spaces, newlines, and unwanted symbols from extracted text."""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    text = text.replace("\ufeff", "").strip()  # Remove invisible BOM characters
    return text

def extract_pdf_content(pdf_path: str) -> dict:
    """Extracts text and tables from a PDF and structures it for LLM processing."""
    text_content = ""
    
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n\n"

    # Clean extracted text
    text_content = clean_text(text_content)

    # Extract tables using Camelot
    tables_data = []
    try:
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
        for table in tables:
            tables_data.append(table.df.to_dict(orient="records"))
    except Exception as e:
        print(f"⚠️ Error extracting tables: {e}")

    return {
        "pdf_content": text_content,
        "tables": tables_data
    }

if __name__ == "__main__":
    # This script should be called from another module with a PDF path dynamically provided
    print("⚠️ This script is designed to be imported and used dynamically.")
