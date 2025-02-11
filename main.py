from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import json
import time

# Initialize FastAPI
app = FastAPI(
    title="Souqcoom Support Chat",
    description="AI-powered customer support chat for Souq.com",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mistral client
api_key = os.getenv("MISTRAL_API_KEY")
client = MistralClient(api_key=api_key) if api_key else None

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
        with open("training_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default training data file
        with open("training_data.json", "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TRAINING_DATA, f, indent=4, ensure_ascii=False)
        return DEFAULT_TRAINING_DATA
    except Exception as e:
        return DEFAULT_TRAINING_DATA

# Load initial training data
training_data = load_training_data()

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

# Serve index page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Serve admin page
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(credentials: HTTPBasicCredentials = Depends(security)):
    verify_admin(credentials)
    with open("templates/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

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

        # Save backup
        try:
            backup_path = f"training_data_backup_{int(time.time())}.json"
            with open("training_data.json", "r", encoding="utf-8") as f:
                current_data = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(current_data)
        except Exception:
            pass

        # Save new data
        with open("training_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Reload training data
        global training_data
        training_data = load_training_data()

        return JSONResponse(content={"status": "success", "message": "Training data updated"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    try:
        # Validate language
        if request.language not in ["en", "ar", "fr", "es", "de", "tr"]:
            request.language = "en"

        # Check for predefined responses
        if training_data and request.language in ["en", "ar"]:
            # Check common responses
            for key, responses in training_data["common_responses"].items():
                if key.lower() in request.message.lower():
                    return {"response": responses.get(request.language)}
            
            # Check FAQs
            for faq in training_data["faqs"].values():
                if (faq["question"][request.language].lower() in request.message.lower()):
                    return {"response": faq["answer"][request.language]}

        # Prepare context
        context = f"""
Company: {training_data['company_info']['name']}
Description: {training_data['company_info']['description']}
Values: {', '.join(training_data['company_info']['values'])}
Categories: {', '.join(training_data['product_categories'])}
"""

        # Prepare system message
        system_message = ChatMessage(
            role="system",
            content=f"""You are a helpful customer service assistant for Souq.com.
Use this context for accurate responses:

{context}

Guidelines:
1. Be professional and courteous
2. Provide accurate information
3. Keep responses concise
4. Respond in {request.language}
"""
        )

        # Add language-specific instructions
        if request.language == "ar":
            system_message.content += "\nأجب باللغة العربية الفصحى المبسطة."
        elif request.language == "fr":
            system_message.content += "\nRépondez en français."
        elif request.language == "es":
            system_message.content += "\nResponda en español."
        elif request.language == "de":
            system_message.content += "\nAntworten Sie auf Deutsch."
        elif request.language == "tr":
            system_message.content += "\nTürkçe olarak yanıt verin."

        # Call Mistral AI
        chat_response = client.chat(
            model="mistral-tiny",
            messages=[
                system_message,
                ChatMessage(role="user", content=request.message)
            ],
            temperature=0.7,
            max_tokens=200
        )

        return {"response": chat_response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
