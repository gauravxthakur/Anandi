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
    """Convert plain text to markdown format with legal document structure"""
    import re
    
    try:
        lines = text.split('\n')
        formatted_lines = []
        in_list = False
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            if not line:
                if in_list:
                    formatted_lines.append('')
                    in_list = False
                continue
            
            # Fix stretched text artifacts (like CCCCChhhhhaaaaapppppttttteeeeerrrrr)
            if re.match(r'^([A-Z])\1{3,}', line):
                line = re.sub(r'([A-Z])\1{3,}', r'\1', line)
            
            # Chapter headers (e.g., "Chapter III", "CHAPTER 1")
            if re.match(r'^[Cc]hapter\s+[IVXLCDM\d]+', line):
                line = f"# {line}"
            
            # Section headers (e.g., "Section 1", "Section 2(a)", "Section 4(2)")
            elif re.match(r'^Section\s+\d+[\(\)\w]*', line):
                line = f"## {line}"
            
            # Act references (e.g., "Act 3", "Act of 1994")
            elif re.match(r'^Act\s+[\d\w]+', line):
                line = f"## {line}"
            
            # Rule references (e.g., "Rule 12", "Rule 3(1)")
            elif re.match(r'^Rule\s+[\d\(\)]+', line):
                line = f"### {line}"
            
            # Article/Clause references
            elif re.match(r'^(Article|Clause)\s+[\d\(\)]+', line):
                line = f"### {line}"
            
            # ALL CAPS headers (except common words)
            elif line.isupper() and len(line) > 3 and not line in ['THE', 'AND', 'FOR', 'WITH', 'FROM']:
                # Clean up stretched caps
                line = re.sub(r'([A-Z])\1{2,}', r'\1', line)
                line = f"### {line}"
            
            # Numbered lists (e.g., "1. Requirement", "(a) Subsection")
            elif re.match(r'^\d+\.\s+[\w]', line) or re.match(r'^\([a-z]\)\s+', line):
                line = f"- {line}"
                in_list = True
            
            # Bullet points with (cid:0) - clean them up
            elif line.startswith('(cid:0)'):
                clean_content = line.replace('(cid:0)', '').strip()
                if clean_content:
                    line = f"- {clean_content}"
                    in_list = True
                else:
                    continue
            
            # Regular content
            else:
                if in_list and not line.startswith('-'):
                    formatted_lines.append('')
                    in_list = False
            
            formatted_lines.append(line)
        
        # Clean up multiple empty lines
        result = '\n'.join(formatted_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
        
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
