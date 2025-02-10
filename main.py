from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from mistralai.client import MistralClient
import os
from dotenv import load_dotenv
import uvicorn
import logging
from pathlib import Path

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Souqcoom Support API",
    description="AI-powered support chat API for Souqcoom",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mistral AI client
client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    language: str = "en"

@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        template_path = Path("templates/index.html")
        if not template_path.exists():
            raise FileNotFoundError("Template file not found")
            
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving template: {str(e)}")
        return HTMLResponse(content="<h1>Service Temporarily Unavailable</h1>", status_code=503)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Log incoming request
        logger.info(f"Received chat request: {request.message[:100]}...")

        # Prepare system prompt based on language
        system_prompt = """You are a helpful customer service assistant for Souq.com, an e-commerce platform. 
        Provide clear, concise, and helpful responses. If you don't know something, say so honestly.
        Keep responses friendly but professional."""

        if request.language == "ar":
            system_prompt += "\nRespond in Arabic with proper RTL formatting."
        
        # Call Mistral AI
        chat_response = client.chat(
            model="mistral-tiny",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=500
        )

        # Extract and return response
        response_text = chat_response.messages[-1].content
        return {"response": response_text}

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
