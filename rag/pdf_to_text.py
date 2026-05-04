import os
import pypdf
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from a single PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def convert_pdfs_to_text(data_dir="rag/data", output_dir="rag/data/text"):
    """Convert all PDFs in data directory to text files"""
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    # Convert each PDF to text
    for pdf_file in pdf_files:
        print(f"Converting {pdf_file.name}...")
        
        # Extract text
        text = extract_text_from_pdf(pdf_file)
        
        if text:
            # Save to text file
            output_file = Path(output_dir) / f"{pdf_file.stem}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Saved to {output_file}")
        else:
            print(f"Failed to extract text from {pdf_file.name}")
    
    print(f"\nConversion complete! Text files saved to {output_dir}/")

if __name__ == "__main__":
    convert_pdfs_to_text()