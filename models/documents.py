"""Document/Chunk are superseded by langchain_core.documents.Document — every loader and
the chunker now build/return that directly. Metadata is a plain dict (source, source_type,
tags, extra keys, set by convention rather than a Pydantic schema) so it flows through
LangChain's splitter/vectorstore APIs without a conversion step at each boundary.
"""
