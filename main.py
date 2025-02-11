from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    logger.warning("MISTRAL_API_KEY not found in environment variables")

# Initialize Mistral client
client = MistralClient(api_key=api_key)

# Initialize FastAPI
app = FastAPI(
    title="Souqcoom Support Chat",
    description="AI-powered customer support chat for Souq.com",
    version="1.0.0"
)

# Base directory for templates and static files
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Default training data
DEFAULT_TRAINING_DATA = {
    "company_info": {
        "name": "Souq.com",
        "description": "Souq.com is the largest e-commerce platform in the Arab world.",
        "values": ["Customer satisfaction", "Fast delivery", "Authentic products"]
    },
    "common_responses": {
        "shipping": {
            "en": "Shipping takes 2-5 business days.",
            "ar": "يستغرق الشحن من 2 إلى 5 أيام عمل."
        }
    },
    "product_categories": ["Electronics", "Fashion", "Home"],
    "faqs": {},
    "support_workflow": {
        "greeting": {
            "en": "Welcome to Souq.com support!",
            "ar": "مرحباً بكم في دعم سوق.كوم!"
        }
    }
}

# Load training data
def load_training_data():
    try:
        training_file = BASE_DIR / "training_data.json"
        if not training_file.exists():
            # Create default training data file if it doesn't exist
            with open(training_file, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_TRAINING_DATA, f, indent=4, ensure_ascii=False)
            return DEFAULT_TRAINING_DATA
            
        with open(training_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading training data: {str(e)}")
        return DEFAULT_TRAINING_DATA

# Load initial training data
training_data = load_training_data()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    language: str = "en"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "souqcoom2024"

security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials):
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# Serve static files
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    file = STATIC_DIR / file_path
    if not file.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file)

# Serve index page
@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        index_file = TEMPLATES_DIR / "index.html"
        if not index_file.exists():
            raise HTTPException(status_code=404, detail="Template not found")
            
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving template: {str(e)}")
        return HTMLResponse(
            content="<h1>Service Temporarily Unavailable</h1>",
            status_code=503
        )

# Serve admin page
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(credentials: HTTPBasicCredentials = Depends(security)):
    verify_admin(credentials)
    try:
        admin_file = TEMPLATES_DIR / "admin.html"
        if not admin_file.exists():
            raise HTTPException(status_code=404, detail="Admin template not found")
            
        with open(admin_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving admin template: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Get training data
@app.get("/admin/data")
async def get_training_data(credentials: HTTPBasicCredentials = Depends(security)):
    verify_admin(credentials)
    return JSONResponse(content=training_data)

# Update training data
@app.post("/admin/data")
async def update_training_data(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    verify_admin(credentials)
    try:
        data = await request.json()
        
        # Validate data structure
        required_keys = ["company_info", "common_responses", "product_categories", "faqs", "support_workflow"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")

        # Save backup if possible
        try:
            backup_file = BASE_DIR / f"training_data_backup_{int(time.time())}.json"
            with open(BASE_DIR / "training_data.json", "r", encoding="utf-8") as f:
                current_data = f.read()
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(current_data)
        except Exception as e:
            logger.warning(f"Failed to create backup: {str(e)}")

        # Save new data
        with open(BASE_DIR / "training_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Reload training data
        global training_data
        training_data = load_training_data()

        return JSONResponse(content={"status": "success", "message": "Training data updated"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating training data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating training data")

# Chat endpoint
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
"""

        # Prepare system prompt
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

        # Add language-specific instructions
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

        # Check for predefined responses
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

        # Return predefined response if available
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
