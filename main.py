from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os
import json
import time
import logging

print("Starting application...")

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
api_key = os.getenv("MISTRAL_API_KEY", "")
print(f"Debug: API Key present: {bool(api_key)}")
print(f"Debug: API Key length: {len(api_key) if api_key else 0}")

try:
    if not api_key:
        print("Warning: MISTRAL_API_KEY environment variable is not set!")
        client = None
    else:
        client = MistralClient(api_key=api_key)
        # Test the client with a simple completion
        test_response = client.chat(
            model="mistral-tiny",
            messages=[ChatMessage(role="user", content="test")],
            max_tokens=10
        )
        print("Debug: Mistral client test successful")
except Exception as e:
    print(f"Error initializing/testing Mistral client: {str(e)}")
    client = None

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

# Add favicon route
@app.get('/favicon.ico')
async def favicon():
    return FileResponse('static/favicon.ico')

# Update the chat endpoint with better error handling
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        if not client:
            print("Error: Mistral client not initialized")
            raise HTTPException(status_code=503, detail="Chat service unavailable")
        
        # Sanitize input
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
            
        print(f"Processing chat request: {message[:50]}... in {request.language}")
        
        # Validate language
        if request.language not in ["en", "ar", "fr", "es", "de", "tr"]:
            request.language = "en"

        try:
            # Call Mistral AI directly first
            chat_response = client.chat(
                model="mistral-tiny",
                messages=[
                    ChatMessage(
                        role="system",
                        content=f"You are a helpful customer service assistant for Souq.com. Respond in {request.language}."
                    ),
                    ChatMessage(role="user", content=message)
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            print("Debug: Got response from Mistral API")
            return {"response": chat_response.choices[0].message.content}
            
        except Exception as api_error:
            print(f"Mistral API error: {str(api_error)}")
            raise HTTPException(status_code=500, detail=f"Chat service error: {str(api_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "api_configured": bool(client)}
