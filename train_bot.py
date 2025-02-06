import os
import json
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class MistralTrainer:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("No API key found in .env file!")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.mistral.ai/v1"

    def upload_training_file(self, file_path):
        """Upload a training file to Mistral AI"""
        print(f"Uploading training file: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/files",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files
            )
            response.raise_for_status()
            return response.json()['id']

    def create_fine_tuning_job(self, training_file_id, model="mistral-small"):
        """Create a fine-tuning job"""
        print(f"Creating fine-tuning job for file: {training_file_id}")
        
        data = {
            "model": model,
            "training_file": training_file_id
        }
        
        response = requests.post(
            f"{self.base_url}/fine_tuning/jobs",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()['id']

    def check_fine_tuning_status(self, job_id):
        """Check the status of a fine-tuning job"""
        response = requests.get(
            f"{self.base_url}/fine_tuning/jobs/{job_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def wait_for_fine_tuning(self, job_id, check_interval=60):
        """Wait for fine-tuning job to complete"""
        print("Waiting for fine-tuning to complete...")
        while True:
            status = self.check_fine_tuning_status(job_id)
            print(f"Status: {status['status']}")
            
            if status['status'] == 'succeeded':
                print("Fine-tuning completed successfully!")
                return status
            elif status['status'] == 'failed':
                raise Exception(f"Fine-tuning failed: {status.get('error', 'Unknown error')}")
            
            time.sleep(check_interval)

def create_training_example(user_input, assistant_response):
    """Create a training example in JSONL format"""
    example = {
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": assistant_response}
        ]
    }
    return json.dumps(example)

def add_training_example(file_path, user_input, assistant_response):
    """Add a new training example to the JSONL file"""
    example = create_training_example(user_input, assistant_response)
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(example + '\n')
    print(f"Added new training example to {file_path}")

def main():
    trainer = MistralTrainer()
    training_file = "training_data/training_examples.jsonl"
    
    # Example of adding a new training example
    while True:
        print("\nOptions:")
        print("1. Add new training example")
        print("2. Start fine-tuning")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            user_input = input("\nEnter user message: ")
            assistant_response = input("Enter assistant response: ")
            add_training_example(training_file, user_input, assistant_response)
            
        elif choice == '2':
            try:
                # Upload training file
                file_id = trainer.upload_training_file(training_file)
                print(f"Training file uploaded. File ID: {file_id}")
                
                # Create and start fine-tuning job
                job_id = trainer.create_fine_tuning_job(file_id)
                print(f"Fine-tuning job created. Job ID: {job_id}")
                
                # Wait for completion
                result = trainer.wait_for_fine_tuning(job_id)
                print(f"Fine-tuned model ID: {result.get('fine_tuned_model')}")
                
            except Exception as e:
                print(f"Error during fine-tuning: {str(e)}")
                
        elif choice == '3':
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
