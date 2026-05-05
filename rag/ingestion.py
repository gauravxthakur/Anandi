import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry

# Connect to the data folder
db = lancedb.connect("./data")

# Define the model
model = get_registry().get("fastembed").create(name="BAAI/bge-small-en-v1.5")

# Define the schema
class Docs(LanceModel):
    text: str = model.SourceField()
    vector: Vector(model.ndims()) = model.VectorField()
    source_type: str
    document_name: str
    section: str
    chunk_id: str
    path: str

# Create the table (overwrite ensures a clean start during development)
table = db.create_table("docs", schema=Docs, mode="overwrite")


table.add([
    {"text": open("file1.txt").read(), "section": "section1"},
    {"text": open("file2.txt").read(), "section": "section2"},
])