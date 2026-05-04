import os
import pypdf
import pdfplumber
import markdownify
from pathlib import Path

def extract_text_with_pdfplumber(pdf_path):
    """Extract text using pdfplumber (better for tables and structure)"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error reading {pdf_path} with pdfplumber: {e}")
        return None

def extract_text_with_pypdf(pdf_path):
    """Fallback to pypdf if pdfplumber fails"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading {pdf_path} with pypdf: {e}")
        return None

def text_to_markdown(text):
    """Convert plain text to markdown format"""
    try:
        # Basic preprocessing to help markdownify
        text = text.replace('\n\n', '\n\n\n')  # Add extra spacing for paragraphs
        
        # Convert to markdown
        md_text = markdownify.markdownify(text, heading_style="ATX")
        
        # Post-processing for better legal document formatting
        lines = md_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
                
            # Detect section headers (e.g., "Section 1", "Section 2(a)", "Act 3")
            if any(line.startswith(prefix) for prefix in ['Section ', 'Act ', 'Article ', 'Clause ']):
                if not line.startswith('#'):
                    line = f"## {line}"
            
            # Detect numbered lists
            elif line[0].isdigit() and ('.' in line or ')' in line):
                if not line.startswith('-') and not line.startswith('*'):
                    line = f"{line}"
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    except Exception as e:
        print(f"Error converting to markdown: {e}")
        return text

def convert_pdfs_to_markdown(data_dir="rag/data", output_dir="rag/data/markdown"):
    """Convert all PDFs in data directory to markdown files"""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")
    
    for pdf_file in pdf_files:
        print(f"Converting {pdf_file.name} to markdown...")
        
        # Try pdfplumber first (better for tables), fallback to pypdf
        text = extract_text_with_pdfplumber(pdf_file)
        if not text:
            text = extract_text_with_pypdf(pdf_file)
        
        if text:
            # Convert to markdown
            markdown_text = text_to_markdown(text)
            
            # Save to markdown file
            output_file = Path(output_dir) / f"{pdf_file.stem}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print(f"Saved to {output_file}")
        else:
            print(f"Failed to extract text from {pdf_file.name}")
    
    print(f"\nConversion complete! Markdown files saved to {output_dir}/")

if __name__ == "__main__":
    convert_pdfs_to_markdown()
