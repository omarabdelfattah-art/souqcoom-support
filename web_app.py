from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("No API key found in .env file!")

# API endpoint and headers
endpoint = "https://api.mistral.ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Store conversation history
conversations = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        # Get or create conversation history for this session
        session_id = request.headers.get('X-Session-ID', 'default')
        if session_id not in conversations:
            conversations[session_id] = []
            
        # Add user message to history
        conversations[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare request data
        request_data = {
            "model": "mistral-small-latest",
            "messages": conversations[session_id],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        # Make API request
        response = requests.post(endpoint, headers=headers, json=request_data)
        response.raise_for_status()
        
        # Get assistant's response
        result = response.json()
        assistant_response = result["choices"][0]["message"]["content"]
        
        # Add assistant response to history
        conversations[session_id].append({
            "role": "assistant",
            "content": assistant_response
        })
        
        return jsonify({"response": assistant_response})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
