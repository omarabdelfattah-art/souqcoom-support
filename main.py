from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
from dotenv import load_dotenv
import uvicorn
import logging
from pathlib import Path
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

# Get API key
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    logger.error("MISTRAL_API_KEY not found in environment variables")
    raise ValueError("MISTRAL_API_KEY environment variable is required")

# Initialize Mistral AI client
try:
    client = MistralClient(api_key=api_key)
    logger.info("Mistral AI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Mistral AI client: {str(e)}")
    raise

class ChatRequest(BaseModel):
    message: str
    language: str = "en"

@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        template_path = Path("templates/index.html")
        if not template_path.exists():
            logger.error(f"Template file not found at {template_path}")
            raise FileNotFoundError("Template file not found")
            
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving template: {str(e)}")
        return HTMLResponse(content="<h1>Service Temporarily Unavailable</h1>", status_code=503)

@app.get("/translations.js")
async def translations():
    try:
        translations_path = Path("templates/translations.js")
        if not translations_path.exists():
            logger.error(f"Translations file not found at {translations_path}")
            raise FileNotFoundError("Translations file not found")
            
        with open(translations_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except Exception as e:
        logger.error(f"Error serving translations: {str(e)}")
        return Response(
            content="console.error('Failed to load translations');",
            media_type="application/javascript",
            status_code=503
        )

@app.get("/health")
async def health_check():
    try:
        # Test Mistral AI connection with minimal token usage
        messages = [
            ChatMessage(role="user", content="test")
        ]
        
        client.chat(
            model="mistral-tiny",
            messages=messages,
            max_tokens=1
        )
        
        return {
            "status": "healthy",
            "mistral_api": "connected",
            "api_key_configured": bool(api_key)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "api_key_configured": bool(api_key)
        }

# Load training data
def load_training_data():
    try:
        with open("training_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading training data: {str(e)}")
        return None

training_data = load_training_data()

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Log incoming request
        logger.debug(f"Received chat request: {json.dumps(request.dict())}")

        # Validate request
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Validate language
        if request.language not in ["en", "ar", "fr", "es", "de", "tr"]:
            logger.warning(f"Invalid language {request.language}, falling back to English")
            request.language = "en"

        # Prepare context from training data
        context = ""
        if training_data:
            context = f"""
Company Information:
{training_data['company_info']['description']}

Key Values:
{chr(10).join('- ' + value for value in training_data['company_info']['values'])}

Available Product Categories:
{chr(10).join('- ' + category for category in training_data['product_categories'])}

Common Responses and FAQs are available for:
- Shipping information
- Returns policy
- Payment methods
- Order tracking
- Order cancellation
"""

        # Prepare system prompt based on language
        system_message = ChatMessage(
            role="system",
            content=f"""You are a helpful customer service assistant for Souq.com, an e-commerce platform. 
            Use the following context for accurate responses:

            {context}

            Guidelines:
            1. Always be professional and courteous
            2. Provide accurate information based on the context
            3. If information is not in the context, say so honestly
            4. Keep responses concise and clear
            5. ALWAYS respond in {request.language}
            """
        )

        if request.language == "ar":
            system_message.content += """\nأنت مساعد افتراضي ذكي متخصص في خدمة عملاء سوق.كوم. يجب أن تكون إجاباتك:
1. مهنية ودقيقة
2. باللغة العربية الفصحى المبسطة
3. مراعية للسياق الثقافي
4. موجزة ومباشرة
5. ودودة مع الحفاظ على المهنية

استخدم صيغة المخاطب المحترمة (أنتم) عند الحديث مع العملاء."""
        elif request.language == "fr":
            system_message.content += "\nRépondez en français."
        elif request.language == "es":
            system_message.content += "\nResponda en español."
        elif request.language == "de":
            system_message.content += "\nAntworten Sie auf Deutsch."
        elif request.language == "tr":
            system_message.content += "\nTürkçe olarak yanıt verin."
        
        # Check if there's a predefined response in training data
        predefined_response = None
        if training_data and request.language in ["en", "ar"]:
            # Check common responses
            for key, responses in training_data["common_responses"].items():
                if key.lower() in request.message.lower():
                    predefined_response = responses.get(request.language)
                    break
            
            # Check FAQs
            if not predefined_response:
                for faq in training_data["faqs"].values():
                    if (faq["question"][request.language].lower() in request.message.lower() or
                        any(word in request.message.lower() for word in faq["question"][request.language].lower().split())):
                        predefined_response = faq["answer"][request.language]
                        break

        # If we have a predefined response, use it
        if predefined_response:
            return {"response": predefined_response}
            
        # Prepare messages for AI
        messages = [
            system_message,
            ChatMessage(role="user", content=request.message)
        ]
        
        logger.debug(f"Sending request to Mistral AI with messages: {[m.dict() for m in messages]}")

        # Call Mistral AI
        chat_response = client.chat(
            model="mistral-tiny",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        # Extract response
        response_text = chat_response.choices[0].message.content
        logger.debug(f"Received response from Mistral AI: {response_text}")

        return {"response": response_text}

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
