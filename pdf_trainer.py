import os
import json
import PyPDF2
import requests
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import torch
import time
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

# Download required NLTK data
nltk.download('punkt')

class PDFTrainer:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("No API key found in .env file!")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Initialize sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create directories if they don't exist
        os.makedirs("training_data", exist_ok=True)
        os.makedirs("pdfs", exist_ok=True)

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file with multiple fallback methods"""
        print(f"Extracting text from {pdf_path}")
        
        # Method 1: Try PyPDF2
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                # Add error checking for PDF header
                header = file.read(5)
                if header != b'%PDF-':
                    print("Warning: File does not start with PDF header")
                file.seek(0)  # Reset to start of file
                
                try:
                    pdf_reader = PyPDF2.PdfReader(file, strict=False)
                    if len(pdf_reader.pages) == 0:
                        raise ValueError("No pages found in PDF")
                    
                    for page in pdf_reader.pages:
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                        except Exception as e:
                            print(f"Warning: Error extracting text from page: {str(e)}")
                            continue
                    
                    if text.strip():
                        return text
                except Exception as e:
                    print(f"PyPDF2 extraction failed: {str(e)}")
            
            # If PyPDF2 failed or extracted no text, try alternative method
            if not text.strip():
                raise ValueError("No text extracted with PyPDF2")
                
        except Exception as primary_error:
            print(f"Primary PDF extraction failed: {str(primary_error)}")
            
            # Method 2: Try pdfplumber as fallback
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        try:
                            text += page.extract_text() + "\n"
                        except Exception as e:
                            print(f"Warning: pdfplumber page extraction error: {str(e)}")
                            continue
                    
                    if text.strip():
                        return text
            except Exception as e:
                print(f"pdfplumber extraction failed: {str(e)}")
            
            # Method 3: Try pdf2image + pytesseract as last resort
            try:
                print("Attempting OCR extraction...")
                images = convert_from_path(pdf_path)
                text = ""
                
                for i, image in enumerate(images):
                    try:
                        page_text = pytesseract.image_to_string(image)
                        text += page_text + "\n"
                    except Exception as e:
                        print(f"Warning: OCR extraction error on page {i}: {str(e)}")
                        continue
                
                if text.strip():
                    return text
                
            except Exception as e:
                print(f"OCR extraction failed: {str(e)}")
        
        raise Exception("All PDF extraction methods failed")

    def download_from_google_drive(self, url, output_path):
        """Download a file from Google Drive"""
        try:
            # Extract file ID from Google Drive URL
            file_id = None
            if 'drive.google.com' in url:
                if '/file/d/' in url:
                    file_id = url.split('/file/d/')[1].split('/')[0]
                elif 'id=' in url:
                    file_id = url.split('id=')[1].split('&')[0]
            
            if not file_id:
                raise ValueError("Could not extract Google Drive file ID from URL")
            
            print(f"Extracted Google Drive file ID: {file_id}")
            
            # Create download URL
            download_url = f"https://drive.google.com/uc?id={file_id}"
            
            # Initialize session
            session = requests.Session()
            
            # Get download token
            response = session.get(download_url, stream=True)
            
            # Handle download confirmation page
            if 'download_warning' in response.text:
                token = response.text.split('download_warning')[1].split('"')[2]
                response = session.get(f"{download_url}&confirm={token}", stream=True)
            
            # Download the file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify if it's a PDF
            with open(output_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    raise ValueError("Downloaded file is not a valid PDF")
            
            return True
            
        except Exception as e:
            print(f"Error downloading from Google Drive: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

    def download_pdf(self, url, output_path):
        """Download a PDF file with proper error handling"""
        try:
            # Check if it's a Google Drive URL
            if 'drive.google.com' in url:
                return self.download_from_google_drive(url, output_path)
            
            # Regular download for other URLs
            # Send a HEAD request first to check content type
            head_response = requests.head(url, allow_redirects=True)
            content_type = head_response.headers.get('content-type', '').lower()
            
            if 'pdf' not in content_type:
                print(f"Warning: URL might not be a PDF (Content-Type: {content_type})")
            
            # Download the file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save the file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify if it's a PDF
            with open(output_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    raise ValueError("Downloaded file is not a valid PDF")
            
            return True
            
        except Exception as e:
            print(f"Error downloading PDF: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

    def process_text_into_chunks(self, text):
        """Split text into manageable chunks"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        return text_splitter.split_text(text)

    def generate_qa_pairs(self, chunk):
        """Generate Q&A pairs from a text chunk using Mistral AI"""
        try:
            # Create a prompt to generate questions
            prompt = f"""Given the following text, generate 3 relevant question-answer pairs. 
            Format each pair as a JSON object with 'question' and 'answer' keys.
            
            Text: {chunk}
            
            Generate natural questions that could be asked about this text."""

            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "mistral-small-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            
            # Parse the response and extract Q&A pairs
            content = response.json()['choices'][0]['message']['content']
            # Assuming the model returns properly formatted JSON
            qa_pairs = []
            try:
                # Split the content by newlines and try to parse each line as JSON
                for line in content.split('\n'):
                    line = line.strip()
                    if line and line.startswith('{') and line.endswith('}'):
                        qa_pair = json.loads(line)
                        if 'question' in qa_pair and 'answer' in qa_pair:
                            qa_pairs.append(qa_pair)
            except json.JSONDecodeError:
                print("Error parsing Q&A pairs from model response")
            
            return qa_pairs
        except Exception as e:
            print(f"Error generating Q&A pairs: {str(e)}")
            return []

    def create_training_examples(self, qa_pairs):
        """Convert Q&A pairs into training examples"""
        examples = []
        for pair in qa_pairs:
            example = {
                "messages": [
                    {"role": "user", "content": pair['question']},
                    {"role": "assistant", "content": pair['answer']}
                ]
            }
            examples.append(example)
        return examples

    def save_training_examples(self, examples, output_file):
        """Save training examples to a JSONL file"""
        with open(output_file, 'a', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')

    def process_pdf(self, pdf_path):
        """Process a PDF file and generate training examples"""
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return False
        
        # Split text into chunks
        chunks = self.process_text_into_chunks(text)
        print(f"Split text into {len(chunks)} chunks")
        
        # Generate training examples for each chunk
        all_examples = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}")
            qa_pairs = self.generate_qa_pairs(chunk)
            examples = self.create_training_examples(qa_pairs)
            all_examples.extend(examples)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        # Save training examples
        output_file = "training_data/training_examples.jsonl"
        self.save_training_examples(all_examples, output_file)
        print(f"Saved {len(all_examples)} training examples to {output_file}")
        return True

def main():
    trainer = PDFTrainer()
    
    while True:
        print("\nPDF Training Options:")
        print("1. Process PDF file")
        print("2. Process PDF from URL")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            pdf_path = input("Enter the path to your PDF file: ")
            if os.path.exists(pdf_path):
                try:
                    success = trainer.process_pdf(pdf_path)
                    if success:
                        print("PDF processed successfully!")
                    else:
                        print("Failed to process PDF.")
                except Exception as e:
                    print(f"Error processing PDF: {str(e)}")
            else:
                print("File not found!")
                
        elif choice == '2':
            url = input("Enter the URL of the PDF file: ")
            try:
                # Create pdfs directory if it doesn't exist
                os.makedirs("pdfs", exist_ok=True)
                
                # Download PDF
                pdf_path = os.path.join("pdfs", "downloaded.pdf")
                if trainer.download_pdf(url, pdf_path):
                    print(f"Downloaded PDF to {pdf_path}")
                    
                    # Process the downloaded PDF
                    success = trainer.process_pdf(pdf_path)
                    if success:
                        print("PDF processed successfully!")
                    else:
                        print("Failed to process PDF.")
                else:
                    print("Failed to download PDF.")
                
            except Exception as e:
                print(f"Error downloading or processing PDF: {str(e)}")
                
        elif choice == '3':
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
