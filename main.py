from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mistralai.client import MistralClient
import os
from dotenv import load_dotenv
import uvicorn
from fastapi.responses import HTMLResponse
import logging

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

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Souqcoom Support API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .endpoint { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
                code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>🤖 Souqcoom Support API</h1>
            <p>Welcome to the Souqcoom Support API. This API provides chat functionality for the Souqcoom support system.</p>
            
            <div class="endpoint">
                <h2>POST /chat</h2>
                <p>Send a message to the chatbot.</p>
                <p>Request body:</p>
                <code>{"message": "Your question here"}</code>
            </div>

            <div class="endpoint">
                <h2>GET /health</h2>
                <p>Check the API health status.</p>
            </div>
            <div class="endpoint">
                <h2>POST /test</h2>
                <p>Test endpoint.</p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/test")
async def test():
    return {"status": "success", "message": "Test endpoint working"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        logger.info(f"Received message: {request.message}")
        messages = [
            {"role": "user", "content": request.message}
        ]

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            logger.error("MISTRAL_API_KEY not found in environment variables")
            raise HTTPException(
                status_code=500,
                detail="API key not configured"
            )

        logger.info("Initializing Mistral client")
        client = MistralClient(api_key=api_key)

        logger.info("Sending request to Mistral API")
        response = client.chat(
            model="mistral-small-latest",
            messages=messages,
            temperature=0.7,
        )

        logger.info("Received response from Mistral API")
        return {
            "message": response.choices[0].message.content,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
