import os
import requests
import json
from dotenv import load_dotenv

def download_from_gdrive(file_id, output_path):
    """Download file from Google Drive"""
    
    # Create download URL
    url = f"https://drive.google.com/uc?id={file_id}&export=download"
    
    # Initialize session
    session = requests.Session()
    
    try:
        # First request to get cookies
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        # Check for large file confirmation token
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                # Add confirmation token to URL
                url = f"{url}&confirm={value}"
                response = session.get(url, stream=True)
                break
        
        # Download the file
        print("Downloading PDF file...")
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        
        # Verify if it's a PDF
        with open(output_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise ValueError("Downloaded file is not a valid PDF")
        
        print(f"Successfully downloaded PDF to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def main():
    # File ID from the Google Drive URL
    file_id = "12lh7gGdsxpBSeSJJEK8pugLswcJfL1RR"
    
    # Create pdfs directory if it doesn't exist
    os.makedirs("pdfs", exist_ok=True)
    
    # Output path
    output_path = os.path.join("pdfs", "downloaded.pdf")
    
    # Download the file
    success = download_from_gdrive(file_id, output_path)
    
    if success:
        print("PDF downloaded successfully!")
        print(f"File saved as: {output_path}")
    else:
        print("Failed to download PDF")

if __name__ == "__main__":
    main()
