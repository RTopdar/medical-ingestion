# Document Ingestion Guide

## Overview

Three-tier ingestion pipeline:
1. **Fetch real data** from APIs (PMC, etc.)
2. **Parse & extract metadata** (JSON/PDF/CSV)
3. **Chunk for RAG** and index

---

## Step 1: Fetch Real Data from PMC

```bash
source .venv/bin/activate
python ingestion/pmc_json_converter.py "diabetes management" 3
```

**Output:** `dummy_docs/pmc_documents.json` with rich metadata from PubMed Central papers.

---

## Step 2: Understand JSON Structure

The generated JSON has **nested, queryable metadata**:

```json
{
  "id": "PMC-12345678",
  "title": "Treatment of Diabetes",
  "content": "Full text...",
  "document_type": "research_paper",
  "source": {
    "type": "pubmed_central",
    "pmcid": "12345678",
    "url": "https://...",
    "accessed_at": "2024-01-15T..."
  },
  "publication_info": {
    "journal": "Journal Name",
    "publication_date": "2023-06-15",
    "volume": "42",
    "issue": "3"
  },
  "article_metadata": {
    "abstract": "...",
    "keywords": ["diabetes", "treatment", "..."],
    "article_sections": [...]
  },
  "authors": [
    {
      "name": "John Smith",
      "affiliation": "Harvard Medical",
      "role": "author"
    }
  ],
  "tags": ["pubmed_central", "research", "diabetes", ...]
}
```

---

## Step 3: Load JSON with Rich Metadata

### Using JSONLoaderService Directly

```python
from ingestion.loaders import LoaderFactory

# Load JSON with automatic metadata flattening
loader = LoaderFactory.json_loader("dummy_docs")
documents = loader.load()

for doc in documents:
    print(f"ID: {doc.id}")
    print(f"Title: {doc.title}")
    print(f"Metadata keys: {list(doc.metadata.extra.keys())}")
    print(f"Flattened metadata: {doc.metadata.extra['nested_metadata']}")
```

### Using Full Ingestion Pipeline

```bash
python scripts/ingest_documents.py
```

**Output:** Loads from all sources (JSON, PDF, CSV/Excel) and creates chunks.

---

## Metadata Extraction Features

### 1. Automatic Field Detection
Searches for content in common fields:
- `content`, `text`, `body`, `description`

### 2. Rich Metadata Preservation
- **Flattened dot-notation**: `article_metadata.abstract` → accessible
- **Nested structure**: Full JSON preserved in `nested_metadata`
- **Auto-extracted fields**: Patient info, diagnoses, providers, etc.

### 3. Queryable Metadata
All flattened keys are searchable:
```python
doc.metadata.extra["nested_metadata"]["publication_info.journal"]
doc.metadata.extra["nested_metadata"]["authors"]
doc.metadata.extra["patient_name"]  # auto-extracted
```

---

## JSONLoaderService Details

### What It Does

1. **Loads JSON** (single file or array of objects)
2. **Extracts content** from any standard field
3. **Flattens nested metadata** to dot-notation
4. **Preserves structure** in raw `nested_metadata` dict
5. **Extracts common fields** (patient info, clinical data, provider)
6. **Creates LangChain Documents** with full metadata

### Example with Complex Nested JSON

```python
from ingestion.loaders import JSONLoaderService, LoaderConfig
from pathlib import Path

config = LoaderConfig(
    source_dir=Path("dummy_docs"),
    clean_text=True
)
loader = JSONLoaderService(config=config)
docs = loader.load()

# Access metadata
doc = docs[0]
flat = doc.metadata.extra["nested_metadata"]

# Dot-notation keys like:
# - "patient_info.name"
# - "clinical_data.diagnoses[0]"
# - "publication_info.journal"
# - etc.

for key in sorted(flat.keys()):
    print(f"{key}: {flat[key]}")
```

---

## Full Pipeline Example

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.loaders import LoaderFactory
from ingestion.chunker import ChunkerConfig, RecursiveChunker

# 1. Load JSON with rich metadata
loader = LoaderFactory.json_loader("data")
docs = loader.load()

# 2. Chunk for RAG
config = ChunkerConfig(chunk_size=512, chunk_overlap=100)
chunker = RecursiveChunker(config=config)
chunks = chunker.chunk_documents(docs)

# 3. Index to vector DB (pseudo-code)
for chunk in chunks:
    vector_db.add(
        text=chunk.content,
        metadata=chunk.metadata.extra  # All flattened metadata
    )

print(f"Indexed {len(chunks)} chunks from {len(docs)} documents")
```

---

## Test Data

### Pre-made dummy JSON
`data/sample_medical_documents.json` — complex medical records with:
- Patient demographics
- Clinical data (diagnoses, medications, vitals)
- Surgical records with implant details
- Provider information
- Discharge instructions

### Real PMC Data
Run `pmc_json_converter.py` to fetch actual research papers from PubMed Central.

---

## Troubleshooting

### JSON not loading
- Ensure `.json` files in target directory
- Check JSON validity: `python -m json.tool data/file.json`

### Metadata not extracted
- Check field names in JSON (looks for `content`, `text`, `body`, etc.)
- Review `nested_metadata` for flattened structure

### Missing auto-extracted fields
- Custom fields need manual extraction
- Add to `JSONLoaderService._load_json()` method

---

## Next Steps

1. **Fetch real data**: `python ingestion/pmc_json_converter.py "your query"`
2. **Ingest documents**: `python scripts/ingest_documents.py`
3. **Index chunks**: Wire to vector DB (Pinecone, Weaviate, etc.)
4. **Query with metadata filters**: Use flattened keys in vector DB
