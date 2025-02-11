from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import os

# Initialize FastAPI
app = FastAPI()

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

class ChatRequest(BaseModel):
    message: str
    language: str = "en"

@app.get("/")
async def root():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat Test</title>
    </head>
    <body>
        <h1>Chat Test</h1>
        <button onclick="testChat()">Test Chat</button>
        <pre id="result"></pre>

        <script>
            async function testChat() {
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: "Hello",
                            language: "en"
                        })
                    });
                    
                    const data = await response.json();
                    document.getElementById('result').textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    document.getElementById('result').textContent = 'Error: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """)

@app.post("/chat")
async def chat(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    try:
        # Simple system message
        system_message = ChatMessage(
            role="system",
            content="You are a helpful assistant. Keep responses short and simple."
        )

        # Call Mistral AI
        chat_response = client.chat(
            model="mistral-tiny",
            messages=[
                system_message,
                ChatMessage(role="user", content=request.message)
            ],
            temperature=0.7,
            max_tokens=100
        )

        return {"response": chat_response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
