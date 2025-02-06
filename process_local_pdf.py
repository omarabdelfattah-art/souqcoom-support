import os
import json
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, requests_per_minute):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        
    def wait(self):
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(minutes=1)]
        
        if len(self.requests) >= self.requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            sleep_time = 61 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                print(f"\nRate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        
        self.requests.append(now)

def process_pdf(pdf_path):
    """Process a local PDF file and generate training examples"""
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")
    
    # Initialize rate limiter (5 requests per minute)
    rate_limiter = RateLimiter(5)
    
    print(f"🔍 Processing PDF: {pdf_path}")
    
    try:
        # Extract text from PDF
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        print(f"📄 Extracted {len(text)} characters of text")
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        print(f"📚 Split into {len(chunks)} chunks")
        print("\n" + "="*80)
        print(f"🎯 Progress: 0/{len(chunks)} chunks processed")
        print(f"📊 Total Q&A pairs: 0")
        print("="*80 + "\n")
        
        # Process each chunk with Mistral AI
        training_examples = []
        processed_chunks = 0
        
        for i, chunk in enumerate(chunks):
            print(f"\nProcessing chunk {i+1}/{len(chunks)}")
            
            # Create prompt for Mistral AI
            prompt = f"""Based on the following text, generate 3 relevant question-answer pairs.
            Each pair should be on a new line in valid JSON format with 'question' and 'answer' keys.
            
            Text: {chunk}
            
            Format each response exactly like this:
            {{"question": "What is X?", "answer": "X is Y."}}
            {{"question": "How does Z work?", "answer": "Z works by..."}}
            {{"question": "Why is W important?", "answer": "W is important because..."}}"""
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Wait for rate limiting
                    rate_limiter.wait()
                    
                    # Call Mistral AI API
                    response = requests.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "mistral-small-latest",
                            "messages": [
                                {"role": "system", "content": "You are a helpful assistant that generates question-answer pairs from text. Always format your responses as JSON objects with 'question' and 'answer' keys, one per line."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 500
                        }
                    )
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_count += 1
                        wait_time = min(2 ** retry_count, 60)  # Exponential backoff
                        print(f"\nRate limit hit. Waiting {wait_time} seconds before retry {retry_count}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    response_json = response.json()
                    
                    if 'error' in response_json:
                        print(f"API Error: {response_json['error']}")
                        break
                        
                    content = response_json['choices'][0]['message']['content']
                    print(f"\n{'='*80}")
                    print(f"🔄 Processing Chunk {i+1}/{len(chunks)}")
                    print(f"{'='*80}\n")
                    
                    # Clean up the content
                    content_lines = []
                    current_line = ""
                    
                    for line in content.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        if line == '```json' or line == '```':
                            continue
                            
                        # Remove any markdown formatting
                        line = line.strip('`')
                        
                        if line.startswith('{'):
                            current_line = line
                            if line.endswith('}'):
                                content_lines.append(current_line)
                                current_line = ""
                        elif line.endswith('}') and current_line:
                            current_line += line
                            content_lines.append(current_line)
                            current_line = ""
                        elif current_line:
                            current_line += line
                    
                    # Process cleaned content
                    successful_pairs = 0
                    for line in content_lines:
                        try:
                            qa_pair = json.loads(line)
                            if 'question' in qa_pair and 'answer' in qa_pair:
                                example = {
                                    "messages": [
                                        {"role": "user", "content": qa_pair['question']},
                                        {"role": "assistant", "content": qa_pair['answer']}
                                    ]
                                }
                                training_examples.append(example)
                                successful_pairs += 1
                                print(f"\n📝 Q&A Pair #{len(training_examples)}:")
                                print(f"❓ Question: {qa_pair['question']}")
                                print(f"💡 Answer: {qa_pair['answer']}")
                                print("-" * 80)
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Skipping malformed JSON: {line}")
                            continue
                    
                    print(f"\n✅ Successfully processed {successful_pairs} Q&A pairs from chunk {i+1}")
                    print(f"📊 Total Q&A pairs so far: {len(training_examples)}")
                    print("=" * 80 + "\n")
                    
                    # Success, break the retry loop
                    processed_chunks += 1
                    print("\n" + "="*80)
                    print(f"🎯 Progress: {processed_chunks}/{len(chunks)} chunks processed")
                    print(f"📊 Total Q&A pairs: {len(training_examples)}")
                    print("="*80 + "\n")
                    break
                    
                except Exception as e:
                    print(f"Error processing chunk response: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    continue
        
        # Save training examples
        output_file = "training_data/training_examples.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in training_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"\nGenerated {len(training_examples)} training examples")
        print(f"Saved to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return False

if __name__ == "__main__":
    pdf_path = "pdfs/downloaded.pdf"
    if os.path.exists(pdf_path):
        process_pdf(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")
