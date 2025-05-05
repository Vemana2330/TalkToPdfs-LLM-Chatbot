import os
import json
import redis
import boto3
import uvicorn
import re
import urllib.parse  # Ensure proper URL encoding
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
 
from pdf_markdown_convertor import pdf_to_markdown_s3
from llm_chat import process_request  # Using process_request for both Summary & LLM Chat
 
# Load environment variables
load_dotenv()

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")  
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")  
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")  
S3_BUCKET_ENDPOINT = f"https://{S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com"
 
# Initialize FastAPI
app = FastAPI()
 
# Initialize Redis (Local)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
 
# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)
 
########################################
#           Pydantic Models            #
########################################
class MarkdownRequest(BaseModel):
    pdf_name: str
    markdown_filename: str
 
class ChatRequest(BaseModel):
    pdf_name: str  # <-- Added this field to fix the error
    question: str
    pdf_json: str | None = None
    markdown_filename: str | None = None
    llm_choice: str | None = None  # Optional if text_summary=True
    text_summary: bool = False  # Flag to differentiate between summary & chat
 
########################################
#         Redis Cache Utility          #
########################################
def get_cached_response(key: str):
    """Retrieve response from Redis cache and convert JSON string back to dictionary."""
    cached_value = redis_client.get(key)
    if cached_value:
        return json.loads(cached_value)  # ✅ Convert JSON string back to dictionary
    return None  # Return None if key doesn't exist
 

def set_cached_response(key: str, value: dict, ttl: int = 86400):
    """Store response in Redis as a JSON string with a TTL (default: 24 hours)."""
    redis_client.setex(key, ttl, json.dumps(value))  # ✅ Convert dictionary to JSON string

 
########################################
#         S3 Utility Functions         #
########################################
def clean_pdf_name(filename: str) -> str:
    """Cleans the PDF filename by removing unwanted characters like (1), spaces, and file extensions."""
    filename = os.path.splitext(filename)[0]  # Remove extension
    filename = re.sub(r"[^a-zA-Z0-9_-]", "_", filename)  # Replace spaces & special chars
    return filename.strip("_")  # Remove trailing underscores
 
def get_markdown_from_s3(pdf_name: str, markdown_filename: str):
    """Fetches the content of a selected Markdown file from S3."""
    object_key = f"{pdf_name}/{markdown_filename}"
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        markdown_content = response["Body"].read().decode("utf-8")
        return markdown_content
    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail=f"Markdown file '{markdown_filename}' not found in {pdf_name}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Markdown content: {e}")
 
def list_images_from_s3(pdf_name: str):
    """Lists image files in the 'Images/' folder of the given PDF directory in S3."""
    image_urls = []
    prefix = f"{pdf_name}/Images/"
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                if obj["Key"].endswith((".png", ".jpg", ".jpeg", ".gif")):
                    encoded_url = urllib.parse.quote(obj["Key"])  # Encode special characters
                    image_urls.append(f"{S3_BUCKET_ENDPOINT}/{encoded_url}")
        return image_urls
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching images: {e}")
 
########################################
#            API Endpoints             #
########################################
@app.get("/fetch_markdown_files/")
def fetch_markdown_files():
    """Fetches Markdown file names grouped by their PDF folders."""
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        pdf_folders = {}
 
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                parts = key.split("/")
                
                if len(parts) > 1 and parts[-1].endswith(".md"):
                    pdf_folder = parts[0]
                    markdown_file = parts[-1]
 
                    if pdf_folder not in pdf_folders:
                        pdf_folders[pdf_folder] = []
                    
                    pdf_folders[pdf_folder].append(markdown_file)
 
        return {"markdown_files": pdf_folders}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Markdown files: {e}")
 
@app.post("/get_markdown_content/")
def get_markdown_content(request: MarkdownRequest):
    """Fetches the content of a selected Markdown file from S3."""
    markdown_content = get_markdown_from_s3(request.pdf_name, request.markdown_filename)
    return {"markdown_content": markdown_content}
 
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Uploads a PDF, extracts its content, converts to Markdown, and uploads to S3.
    Returns structured JSON containing file URLs.
    """
    try:
        import tempfile
        pdf_name = clean_pdf_name(file.filename)  # Ensure clean and correct folder name
 
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
 
        # Pass pdf_name explicitly
        result = pdf_to_markdown_s3(tmp_path, pdf_name)
        os.remove(tmp_path)  # Clean up temporary file
 
        # Include correct markdown filename in the response
        result["markdown_filename"] = f"{pdf_name}.md"
        
        return JSONResponse(content=result)
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
 
@app.post("/chat/")
def chat(request: ChatRequest):
    """
    Handles both **Text Summary** and **LLM Chat** based on `text_summary` flag.
    Uses Redis caching to store and retrieve previous responses for each LLM model.
    """
    try:
        # Ensure `pdf_name`, `question`, and `llm_choice` (if chat) are provided
        if not request.pdf_name or not request.question:
            raise HTTPException(status_code=400, detail="Missing required fields: 'pdf_name' and 'question'.")
        if not request.text_summary and not request.llm_choice:
            raise HTTPException(status_code=400, detail="LLM choice is required for chat.")

        # Generate a unique cache key including the LLM model name
        cache_key = f"{request.pdf_name}:{request.question}:{request.text_summary}:{request.llm_choice}"

        # ✅ Check Redis cache first
        cached_response = get_cached_response(cache_key)
        if cached_response:
            try:
                cached_response = json.loads(cached_response)  # Ensure it is a dictionary
                return {
                    "answer": cached_response.get("response", "No response available."),
                    "tokens_used": cached_response.get("tokens_used", "N/A"),
                    "input_tokens": cached_response.get("input_tokens", "N/A"),
                    "output_tokens": cached_response.get("output_tokens", "N/A"),
                    "cost": cached_response.get("cost", "N/A"),
                    "cached": True,
                    "llm_choice": request.llm_choice
                }
            except json.JSONDecodeError:
                pass  # If cache is corrupted, ignore and continue fresh request

        # ✅ Fetch Markdown content from S3 if Markdown file is selected
        if request.markdown_filename:
            markdown_content = get_markdown_from_s3(request.pdf_name, request.markdown_filename)
            pdf_data = {"pdf_content": markdown_content or "No content available.", "tables": []}
        elif request.pdf_json:
            pdf_data = json.loads(request.pdf_json)
        else:
            raise HTTPException(status_code=400, detail="No valid input provided.")

        # ✅ Process the request based on `text_summary` flag
        answer = process_request(
            pdf_data=pdf_data,
            question=request.question,
            llm_choice=None if request.text_summary else request.llm_choice,  # LLM not needed for summary
            text_summary=request.text_summary
        )

        # ✅ Extract tokens & cost calculations if response contains usage data
        usage = answer.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        input_token_cost = input_tokens * 0.00000015  # ✅ Cost per input token
        output_token_cost = output_tokens * 0.0000006  # ✅ Cost per output token
        total_cost = input_token_cost + output_token_cost  # ✅ Total cost

        # ✅ Ensure `answer` is a dictionary before storing in Redis
        if not isinstance(answer, dict):
            answer = {
                "response": str(answer),
                "tokens_used": "N/A",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": total_cost
            }

        # ✅ Cache response in Redis (storing it as a JSON string)
        set_cached_response(cache_key, json.dumps(answer))

        return {
            "answer": answer.get("response", "No response available."),
            "tokens_used": answer.get("tokens_used", "N/A"),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_cost,
            "cached": False,
            "llm_choice": request.llm_choice
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {e}")