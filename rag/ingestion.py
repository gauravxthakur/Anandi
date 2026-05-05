import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from pydantic import Field
import os
from pathlib import Path
from transformers import AutoTokenizer

# Connect to the data folder
db = lancedb.connect("./rag/data")

# Define the embedding model
model = get_registry().get("sentence-transformers").create(name="BAAI/bge-small-en-v1.5")
# Initialize BGE tokenizer
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")

# Define the schema
class Docs(LanceModel):
    text: str = model.SourceField(description="Text content of the document")
    vector: Vector(model.ndims()) = model.VectorField(description="Vector representation of the text content")
    source_type: str = Field(..., description="Type of document: legal, guideline, form")
    document_name: str = Field(..., description="Name of the source document")
    section: str = Field(default="", description="Section within the document")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    path: str = Field(..., description="File path for debugging")


# Metadata mapping for files
DOCUMENT_METADATA = {
    "Handbook on PC_PNDT Act _ Rules with Amendments.md": {
        "source_type": "legal",
        "document_name": "PCPNDT_Handbook"
    },
    "pre-conception-pre-natal-diagnostic-techniques-act-1994.md": {
        "source_type": "legal", 
        "document_name": "PCPNDT_Act_1994"
    },
    "Stander Operating Guidelines for PC& PNDT.md": {
        "source_type": "guideline",
        "document_name": "PCPNDT_SOG"
    },
    "ISUOG Practice Guidelines (updated) performance of theroutine mid-trimester fetal ultrasound scan.md": {
        "source_type": "guideline",
        "document_name": "ISUOG_Mid-Trimester"
    },
    "ISUOG Practice Guidelines (updated) use of Doppler.md": {
        "source_type": "guideline",
        "document_name": "ISUOG_Doppler"
    },
    "ISUOG Practice Guidelines performance of third-trimester scan.md": {
        "source_type": "guideline", 
        "document_name": "ISUOG_Third-Trimester"
    },
    "ISUOG-Practice-Guidelines-Updated-performance-of-11-14-week-ultrasound-scan.md": {
        "source_type": "guideline",
        "document_name": "ISUOG_First-Trimester"
    },
    "ISUOG-Practice-Guidelines-ultrasound-twin-pregnancy.md": {
        "source_type": "guideline",
        "document_name": "ISUOG_Twins"
    },
    "Updated-ISUOG-Practice-Guidelines-performance-of-fetal-magnetic-resonance.md": {
        "source_type": "guideline",
        "document_name": "ISUOG_MRI"
    },
    "Sonographic_estimation_of_fetal_weight_The_value_of_femur_length_in_addition_to_head_and_abdomen_measurement.md": {
        "source_type": "research",
        "document_name": "Fetal_Weight_Study"
    }
}

def chunk_text(text, max_tokens=800, overlap_tokens=80):
    """
    Split text into overlapping chunks.
    """
    # Get token count
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    if len(tokens) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        
        # If this is the last chunk, take whatever remains
        if end >= len(tokens):
            chunk_tokens = tokens[start:]
            chunks.append(tokenizer.decode(chunk_tokens))
            break
        
        # Try to break at a sentence boundary within the last 100 tokens
        chunk_end = end
        chunk_text_partial = tokenizer.decode(tokens[start:end])
        
        # Look backward for sentence endings in the decoded text
        for i in range(len(chunk_text_partial) - 1, max(len(chunk_text_partial) - 200, 0), -1):
            if chunk_text_partial[i] in '.!?':
                # Find corresponding token position
                sentence_end_tokens = tokenizer.encode(chunk_text_partial[:i+1], add_special_tokens=False)
                chunk_end = start + len(sentence_end_tokens)
                break
        
        chunk_tokens = tokens[start:chunk_end]
        chunks.append(tokenizer.decode(chunk_tokens))
        start = chunk_end - overlap_tokens
    
    return chunks

# Create the table (overwrite ensures a clean start during development)
table = db.create_table("docs", schema=Docs, mode="overwrite")

# Ingest markdown files
markdown_dir = Path("rag/data/markdown")
documents = []

for filename in os.listdir(markdown_dir):
    if filename.endswith(".md"):
        file_path = markdown_dir / filename
        metadata = DOCUMENT_METADATA.get(filename, {
            "source_type": "other",
            "document_name": filename.replace(".md", "")
        })
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chunk the content with overlap
        chunks = chunk_text(content)
        
        # Add each chunk as a separate document
        for i, chunk in enumerate(chunks):
            documents.append({
                "text": chunk,
                "source_type": metadata["source_type"],
                "document_name": metadata["document_name"],
                "section": "",
                "chunk_id": f"{metadata['document_name']}:{i}",
                "path": str(file_path)
            })

if documents:
    table.add(documents)
    print(f"Added {len(documents)} documents to LanceDB")
else:
    print("No markdown documents found")