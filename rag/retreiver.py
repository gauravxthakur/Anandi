"""
RAG retriever with filtered vector searches.

Provides semantic search capabilities with metadata filtering for
targeted document retrieval from the LanceDB vector store.
"""

import lancedb
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Structured search result."""
    text: str = Field(..., description="Search result text")
    source_type: str = Field(..., description="Source type of the document")
    document_name: str = Field(..., description="Name of the document")
    section: str = Field(..., description="Section of the document")
    chunk_id: str = Field(..., description="Chunk ID of the document")
    path: str = Field(..., description="Path to the document")
    score: float = Field(..., description="Score of the search result")


class Retriever:
    """Vector search retriever with metadata filtering."""
    
    def __init__(self, db_path: str = "rag/data"):
        """Initialize retriever with LanceDB connection."""
        self.db = lancedb.connect(db_path)
        self.table = self.db.open_table("docs")
    
    def search(self, 
               query: str, 
               source_type: Optional[str] = None,
               document_name: Optional[str] = None,
               limit: int = 5,
               threshold: float = 0.5) -> List[SearchResult]:
        """
        Search documents with optional metadata filtering.
        
        Args:
            query: Search query text
            source_type: Filter by document type ('legal', 'guideline', 'research', 'other')
            document_name: Filter by specific document name
            limit: Maximum number of results to return
            
        Returns:
            List of search results with metadata
        """
        # Build filter conditions
        filter_conditions = []
        
        if source_type:
            filter_conditions.append(f"source_type = '{source_type}'")
        
        if document_name:
            filter_conditions.append(f"document_name = '{document_name}'")
        
        # Combine conditions
        where_clause = " AND ".join(filter_conditions) if filter_conditions else None
        
        # Perform search
        results = self.table.search(query).limit(limit)
        
        if where_clause:
            results = results.where(where_clause)
        
        # Convert to list of dictionaries
        search_results = results.to_list()
        
        # Format results as Pydantic models
        formatted_results = []
        for result in search_results:
            try:
                search_result = SearchResult(
                    text=result.get("text", ""),
                    source_type=result.get("source_type", ""),
                    document_name=result.get("document_name", ""),
                    section=result.get("section", ""),
                    chunk_id=result.get("chunk_id", ""),
                    path=result.get("path", ""),
                    score=result.get("_distance", 0.0)
                )
                # Apply threshold filtering
                if search_result.score <= threshold:
                    formatted_results.append(search_result)
            except Exception as e:
                # Skip malformed results
                continue
        
        return formatted_results
    
    def search_legal(self, query: str, limit: int = 5, threshold: float = 0.5) -> List[SearchResult]:
        """Search only legal documents."""
        return self.search(query, source_type="legal", limit=limit, threshold=threshold)
    
    def search_guidelines(self, query: str, limit: int = 5, threshold: float = 0.5) -> List[SearchResult]:
        """Search only guideline documents."""
        return self.search(query, source_type="guideline", limit=limit, threshold=threshold)
    
    def search_research(self, query: str, limit: int = 5, threshold: float = 0.5) -> List[SearchResult]:
        """Search only research documents."""
        return self.search(query, source_type="research", limit=limit, threshold=threshold)
    
    def search_document(self, query: str, document_name: str, limit: int = 5, threshold: float = 0.5) -> List[SearchResult]:
        """Search within a specific document."""
        return self.search(query, document_name=document_name, limit=limit, threshold=threshold)
    
    def get_available_documents(self) -> Dict[str, List[str]]:
        """Get list of available documents by source type."""
        # Get all unique documents
        all_docs = self.table.to_pandas()
        
        documents_by_type = {}
        for source_type in all_docs['source_type'].unique():
            docs = all_docs[all_docs['source_type'] == source_type]['document_name'].unique().tolist()
            documents_by_type[source_type] = sorted(docs)
        
        return documents_by_type
    
    def get_document_chunks(self, document_name: str) -> List[str]:
        """Get all chunk IDs for a specific document."""
        results = self.table.search("").where(f"document_name = '{document_name}'").to_list()
        return [result.get("chunk_id", "") for result in results]


# Global instance for easy access
retriever = Retriever()


# Convenience functions
def search(query: str, 
          source_type: Optional[str] = None,
          document_name: Optional[str] = None,
          limit: int = 5,
          threshold: float = 0.5) -> List[SearchResult]:
    """Convenience function for semantic search with filtering."""
    return retriever.search(query, source_type, document_name, limit, threshold)


def search_legal(query: str, limit: int = 5, threshold: float = 0.5) -> List[SearchResult]:
    """Convenience function for legal document search."""
    return retriever.search(query, source_type="legal", limit=limit, threshold=threshold)


def search_guidelines(query: str, limit: int = 5, threshold: float = 0.5) -> List[SearchResult]:
    """Convenience function for guideline search."""
    return retriever.search(query, source_type="guideline", limit=limit, threshold=threshold)


def search_research(query: str, limit: int = 5, threshold: float = 0.5) -> List[SearchResult]:
    """Convenience function for research document search."""
    return retriever.search(query, source_type="research", limit=limit, threshold=threshold)