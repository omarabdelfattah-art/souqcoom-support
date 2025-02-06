import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api():
    print("Testing Souqcoom Support API...")
    
    # Test endpoint
    url = "http://localhost:8000/chat"
    
    # Test message
    test_message = {
        "message": "What is Souqcoom?"
    }
    
    try:
        # Make POST request to API
        response = requests.post(url, json=test_message)
        
        # Check if request was successful
        if response.status_code == 200:
            print("\n✅ API Test Successful!")
            print("\nTest Message:", test_message["message"])
            print("\nAPI Response:", response.json()["message"])
        else:
            print("\n❌ API Test Failed!")
            print("Status Code:", response.status_code)
            print("Error:", response.text)
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print("\n❌ Error:", str(e))

if __name__ == "__main__":
    test_api()
