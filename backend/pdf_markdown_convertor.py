# backend/pdf_markdown_convertor.py
 
import fitz  # PyMuPDF for image extraction
import pdfplumber  # For text and table extraction
import os
import re
import pandas as pd
import boto3
import tempfile
 
# Load AWS credentials dynamically from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
 
# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)
 
 
def upload_file_to_s3(file_path, s3_key):
    """Uploads a file to S3 and returns its public URL."""
    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{s3_key}"
        return s3_url
    except Exception as e:
        print(f"⚠️ Failed to upload {file_path} to S3: {e}")
        return None
 
 
def clean_text(text):
    """Removes excessive spaces and unwanted symbols from extracted text."""
    text = re.sub(r"\s+", " ", text)  # Replace multiple spaces/newlines with a single space
    return text.strip()
 
 
def extract_pdf_content(pdf_path, s3_folder):
    """Extracts text, tables, and images while maintaining document order."""
    doc = fitz.open(pdf_path)
    md_content = ""
 
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(len(doc)):
            page = doc[page_num]
            pdf_page = pdf.pages[page_num] if page_num < len(pdf.pages) else None
 
            # Extract text first
            if pdf_page:
                page_text = pdf_page.extract_text()
                if page_text:
                    md_content += f"{clean_text(page_text)}\n\n"
 
            # Extract tables immediately after text
            if pdf_page:
                tables = pdf_page.extract_tables()
                for table in tables:
                    if table:
                        df = pd.DataFrame(table)
                        md_content += f"{df.to_markdown(index=False)}\n\n"
 
            # Extract images immediately after text/tables
            images = page.get_images(full=True)
            image_folder = f"{s3_folder}Images/"  # Fix: Ensure images are placed in 'Images/'
 
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
 
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                img_filename = f"image_{page_num+1}_{img_index+1}.{image_ext}"
 
                # Save image temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_ext}") as tmp_img:
                    tmp_img.write(image_bytes)
                    tmp_path = tmp_img.name
 
                # Fix: Ensure images are uploaded under "Images/" inside the PDF folder
                s3_image_key = f"{image_folder}{img_filename}"  # Fix: Correct image path
                s3_url = upload_file_to_s3(tmp_path, s3_image_key)
                os.remove(tmp_path)
 
                if s3_url:
                    md_content += f"![Image]({s3_url})\n\n"
 
    doc.close()
    return md_content
 
 
def pdf_to_markdown_s3(pdf_path, pdf_name):
    """Extracts PDF content, uploads images, and saves Markdown to S3 while preserving document order."""
    
    s3_folder = f"{pdf_name}/"  # Ensure folder matches actual PDF name
    markdown_filename = f"{pdf_name}.md"
 
    # Define S3 directories
    s3_image_folder = f"{s3_folder}Images/"  # Ensure images are inside "Images/"
    s3_markdown_key = f"{s3_folder}{markdown_filename}"
    s3_pdf_key = f"{s3_folder}{pdf_name}.pdf"
 
    # Upload the PDF file to S3
    pdf_s3_url = upload_file_to_s3(pdf_path, s3_pdf_key)
 
    # Extract content while maintaining document order
    md_content = extract_pdf_content(pdf_path, s3_folder)
 
    # Save Markdown to a **single file**
    markdown_temp_path = os.path.join(tempfile.gettempdir(), markdown_filename)
    with open(markdown_temp_path, "w", encoding="utf-8") as md_file:
        md_file.write(md_content)
 
    # Upload Markdown to S3
    md_s3_url = upload_file_to_s3(markdown_temp_path, s3_markdown_key)
    os.remove(markdown_temp_path)
 
    return {
        "pdf_url": pdf_s3_url,
        "markdown_url": md_s3_url,
        "s3_folder": s3_folder  # Now this will have the correct name
    }
 
 
    return {
        "pdf_url": pdf_s3_url,
        "markdown_url": md_s3_url,
        "s3_folder": s3_folder  # Now this will have the correct name
    }
 
 
 
# This function is called dynamically with the PDF path from Streamlit UI
if __name__ == "__main__":
    print("⚠️ This script is designed to be called dynamically from the backend.")