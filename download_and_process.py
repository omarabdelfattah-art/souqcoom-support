import os
import gdown
import PyPDF2
from pdf_trainer import PDFTrainer

def download_and_process_pdf():
    # Create directories if they don't exist
    os.makedirs("pdfs", exist_ok=True)
    os.makedirs("training_data", exist_ok=True)
    
    # File ID and URL
    file_id = "12lh7gGdsxpBSeSJJEK8pugLswcJfL1RR"
    url = f"https://drive.google.com/uc?id={file_id}"
    output_path = "pdfs/downloaded.pdf"
    
    try:
        # Download the file using gdown
        print("Downloading PDF file...")
        gdown.download(url, output_path, quiet=False)
        
        # Verify if it's a valid PDF
        try:
            with open(output_path, 'rb') as f:
                PyPDF2.PdfReader(f)
            print("Successfully downloaded and verified PDF")
            
            # Process the PDF
            print("\nProcessing PDF for training...")
            trainer = PDFTrainer()
            success = trainer.process_pdf(output_path)
            
            if success:
                print("\nPDF processed successfully!")
                print("Training examples have been generated and saved to training_data/training_examples.jsonl")
            else:
                print("\nFailed to process PDF")
            
        except Exception as e:
            print(f"Error verifying PDF: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
            
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False
    
    return True

if __name__ == "__main__":
    download_and_process_pdf()
