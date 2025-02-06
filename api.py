from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mistralai.client import MistralClient
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Souqcoom Support API",
    description="AI-powered support chat API for Souqcoom",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your WordPress site URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mistral AI client
try:
    client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
except Exception as e:
    logger.error(f"Failed to initialize Mistral AI client: {str(e)}")
    raise

class ChatRequest(BaseModel):
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )

@app.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """Chat endpoint for processing messages"""
    try:
        logger.info(f"Received message: {request.message[:50]}...")
        
        # Create chat message
        messages = [
            {"role": "user", "content": request.message}
        ]

        # Get response from Mistral AI
        response = client.chat(
            model="mistral-small-latest",
            messages=messages,
            temperature=0.7,
        )

        return {
            "message": response.choices[0].message.content,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
