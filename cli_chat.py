import requests
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize API key
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("Error: No API key found in .env file!")
        return
        
    print(f"Initializing with API key (starts with: {api_key[:4]}...)")
    
    # API endpoint
    endpoint = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Store conversation history
    messages = []
    
    print("Chatbot initialized! Type 'quit' to exit.")
    print("-" * 50)
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'quit':
            break
            
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Prepare request data
            data = {
                "model": "mistral-small-latest",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            # Make API request
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Get and print assistant's response
            result = response.json()
            assistant_response = result["choices"][0]["message"]["content"]
            print("\nAssistant:", assistant_response)
            
            # Add assistant response to history
            messages.append({"role": "assistant", "content": assistant_response})
            
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
