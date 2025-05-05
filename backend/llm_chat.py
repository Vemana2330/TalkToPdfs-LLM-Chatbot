import os
import tiktoken
import litellm
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
import anthropic
import re
import logging
 
# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
 
# Configure Logging for LiteLLM
logging.basicConfig(
    filename="token_usage.log",  # ✅ Log all token usage to this file
    level=logging.INFO,  # ✅ Log INFO level and above
    format="%(asctime)s - %(levelname)s - %(message)s",  # ✅ Log format
)

# Configure LiteLLM for OpenAI (GPT-4o Mini)
litellm.api_key = OPENAI_API_KEY
litellm.verbose = True  # ✅ Correct way to enable logging
litellm.monitoring = "athina"  # ✅ Enable Athina tracking

# ✅ Log token usage for every request
def log_token_usage(model: str, tokens_used: int, cost: float):
    logging.info(f"Model: {model} | Tokens Used: {tokens_used} | Cost: ${cost:.6f}")

# Configure DeepSeek API client
deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
 
 
def count_tokens(text: str, model: str) -> int:
    """
    Count tokens using tiktoken if supported.
    For Gemini and Claude models, use an approximate method (word count) as a fallback.
    """
    try:
        if model in ["gemini flash free", "claude-3.5 haiku"]:
            return len(text.split())
        else:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
    except Exception as e:
        print(f"Token count error: {e}")
        return 0
 
 
def summarize_markdown(markdown_text: str) -> str:
    """
    Extracts a summary from the Markdown file by:
    - Identifying key sections (Abstract, Introduction, Summary)
    - Using LLM (GPT-4o Mini) to summarize if content is too large
    """
    lines = markdown_text.strip().split("\n")
 
    # Extract abstract or introduction if present
    summary_lines = []
    capturing = False
    for line in lines:
        if re.search(r"(?i)\b(abstract|introduction|summary)\b", line):  # Case insensitive match
            capturing = True
        if capturing:
            summary_lines.append(line)
        if len(summary_lines) >= 10:  # Limit extracted lines
            break
 
    # If we found a key section, return that
    if summary_lines:
        summary = "\n".join(summary_lines).strip()
    else:
        # Otherwise, take the first few lines as a fallback
        summary = "\n".join(lines[:5])
 
    summary = summary.replace("#", "").strip()  # Remove Markdown headers
 
    # Use LLM for better summarization
    prompt = f"Summarize the following document content in 3-4 sentences:\n\n{summary}"
    
    response = litellm.completion(
        model="gpt-4o",  # Use GPT-4o Mini
        messages=[{"role": "user", "content": prompt}]
    )
    return f"📝 **Summary:** {response['choices'][0]['message']['content']}"
 
 
 
def build_prompt(pdf_data: dict, question: str) -> str:
    """
    Constructs a prompt using the extracted PDF content and the user's question.
    """
    return f"""
You are a helpful assistant. Use the following document content to answer the question.

Document Content:
{pdf_data.get("pdf_content", "No document content available.")}
 
Tables Extracted:
{pdf_data.get("tables", "No tables available.")}
 
User Question:
{question}
 
Answer the question based solely on the document above.
"""
 
 
import os
import logging
import litellm
import google.generativeai as genai
from openai import OpenAI
import anthropic

# ✅ Configure Logging
logging.basicConfig(
    filename="token_usage.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ✅ Function to Log Token Usage
def log_token_usage(model: str, tokens_used: int, cost: float):
    logging.info(f"Model: {model} | Tokens Used: {tokens_used} | Cost: ${cost:.6f}")

def get_llm_response(pdf_data: dict, question: str, llm_choice: str) -> dict:
    """
    Calls the selected LLM from the 4 approved models and logs token usage.
    """
    prompt_text = build_prompt(pdf_data, question)
    llm_choice = llm_choice.strip().lower()  # Normalize input

    try:
        if llm_choice == "gpt-4o mini":
            response = litellm.completion(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt_text}]
            )

            # ✅ Debug: Log Raw Response
            logging.info(f"GPT-4o Response: {response}")

            # ✅ Extract Token Usage & Cost Calculation
            usage = response.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)  # Input Tokens
            output_tokens = usage.get("completion_tokens", 0)  # Output Tokens
            total_tokens = usage.get("total_tokens", 0)

            # ✅ Cost Calculation (GPT-4o Mini)
            input_cost = input_tokens * 0.00000015
            output_cost = output_tokens * 0.0000006
            total_cost = input_cost + output_cost

            # ✅ Log Token Usage
            log_token_usage("GPT-4o Mini", total_tokens, total_cost)

            return {
                "response": response["choices"][0]["message"]["content"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": total_cost
            }

        elif llm_choice == "gemini flash free":
            token_count = count_tokens(prompt_text, model="gemini-1.5-pro-latest")

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(prompt_text)

            # ✅ Debug: Log Raw Response
            logging.info(f"Gemini Response: {response}")

            # ✅ Extract Token Usage
            prompt_tokens = response.result.usage_metadata["prompt_token_count"]
            output_tokens = response.result.usage_metadata["candidates_token_count"]
            total_tokens = response.result.usage_metadata["total_token_count"]

            # ✅ Cost Calculation (Gemini)
            cost = total_tokens * 0.000002  # Adjust this value based on pricing

            # ✅ Log Token Usage
            log_token_usage("Gemini Flash Free", total_tokens, cost)

            return {
                "response": response.text,
                "input_tokens": prompt_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost
            }

        elif llm_choice == "deepseek chat":
            token_count = count_tokens(prompt_text, model="deepseek-chat")

            response = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            ).chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt_text}],
                stream=False
            )

            # ✅ Debug: Log Raw Response
            logging.info(f"DeepSeek Response: {response}")

            # ✅ Extract Tokens & Cost
            usage = getattr(response, "usage", None)
            tokens_used = getattr(usage, "total_tokens", token_count) if usage else token_count
            cost = getattr(usage, "total_cost", token_count * 0.000002) if usage else token_count * 0.000002

            # ✅ Log Token Usage
            log_token_usage("DeepSeek Chat", tokens_used, cost)

            return {
                "response": response.choices[0].message.content,
                "tokens_used": tokens_used,
                "cost": cost
            }

        elif llm_choice == "claude-3.5 haiku":
            token_count = count_tokens(prompt_text, model="claude-3-5-haiku-20241022")

            client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt_text}]
            )

            # ✅ Debug: Log Raw Response
            logging.info(f"Claude Response: {response}")

            # ✅ Approximate Cost Calculation
            cost = token_count * 0.000003  # Assume $3 per 1M tokens

            # ✅ Log Token Usage
            log_token_usage("Claude-3.5 Haiku", token_count, cost)

            return {
                "response": response.content,
                "tokens_used": token_count,
                "cost": cost
            }

        else:
            return {"response": f"⚠️ LLM choice '{llm_choice}' not recognized.", "tokens_used": 0, "cost": 0.0}

    except Exception as e:
        logging.error(f"Error processing LLM request: {e}")
        return {"response": f"Error: {e}", "tokens_used": 0, "cost": 0.0}


 
 
def process_request(pdf_data: dict, question: str, llm_choice: str | None, text_summary: bool = False) -> str:
    """
    Determines whether to generate a **summary** or engage in **LLM chat**.
    - If `text_summary=True`, it summarizes Markdown content.
    - Otherwise, it passes data to an LLM.
    """
    if text_summary:
        return summarize_markdown(pdf_data["pdf_content"])
    elif llm_choice:
        return get_llm_response(pdf_data, question, llm_choice)
    else:
        return "⚠️ No valid LLM choice provided."