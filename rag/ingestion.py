import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from pydantic import Field

# Connect to the data folder
db = lancedb.connect("./data")

# Define the model
model = get_registry().get("fastembed").create(name="BAAI/bge-small-en-v1.5")

# Define the schema
class Docs(LanceModel):
    text: str = model.SourceField(description="Text content of the document")
    vector: Vector(model.ndims()) = model.VectorField(description="Vector representation of the text content")
    source_type: str = Field(..., description="Type of document: legal, guideline, form")
    document_name: str = Field(..., description="Name of the source document")
    section: str = Field(default="", description="Section within the document")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    path: str = Field(..., description="File path for debugging")


# Create the table (overwrite ensures a clean start during development)
table = db.create_table("docs", schema=Docs, mode="overwrite")


table.add([
    {"text": open("file1.txt").read(), "section": "section1"},
    {"text": open("file2.txt").read(), "section": "section2"},
])