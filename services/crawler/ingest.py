"""
Document Ingestor - Ingest documents into Qdrant

Handles:
- Document chunking
- Embedding generation
- Qdrant storage
- Batch processing
"""

import os
import uuid
from typing import List, Dict, Any

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


class DocumentIngestor:
    """
    Ingest parsed documents into Qdrant vector database.
    
    Handles chunking, embedding, and storage.
    """
    
    def __init__(
        self,
        qdrant_url: str = None,
        collection_name: str = None,
        embedding_model: str = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """
        Initialize document ingestor.
        
        Args:
            qdrant_url: Qdrant URL
            collection_name: Collection name
            embedding_model: Model for embeddings
            chunk_size: Characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION", "documents")
        self.embedding_model_name = embedding_model or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Ensure collection exists
        self._ensure_collection()
        
        logger.info(f"DocumentIngestor initialized (collection: {self.collection_name})")
    
    def _ensure_collection(self):
        """Ensure Qdrant collection exists."""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("✓ Collection created")
            else:
                logger.debug(f"Collection exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def ingest_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """
        Ingest documents into Qdrant.
        
        Args:
            documents: List of parsed documents
            batch_size: Batch size for ingestion
            
        Returns:
            Number of documents ingested
        """
        if not documents:
            return 0
        
        logger.info(f"Ingesting {len(documents)} documents...")
        
        total_chunks = 0
        
        for i, doc in enumerate(documents, 1):
            try:
                # Chunk document
                chunks = self._chunk_document(doc)
                
                if not chunks:
                    logger.warning(f"No chunks for document: {doc.get('url', 'unknown')}")
                    continue
                
                # Generate embeddings
                embeddings = self._generate_embeddings([c["text"] for c in chunks])
                
                # Create points for Qdrant
                points = []
                for chunk, embedding in zip(chunks, embeddings):
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload=chunk,
                    )
                    points.append(point)
                
                # Upsert to Qdrant
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                )
                
                total_chunks += len(chunks)
                logger.debug(f"✓ Ingested {i}/{len(documents)}: {len(chunks)} chunks from {doc.get('url', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Error ingesting document: {e}")
        
        logger.info(f"✓ Ingested {len(documents)} documents ({total_chunks} chunks)")
        return len(documents)
    
    def _chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk document text.
        
        Args:
            doc: Document with 'text' field
            
        Returns:
            List of chunks with metadata
        """
        text = doc.get("text", "")
        
        if not text:
            return []
        
        chunks = []
        start = 0
        chunk_num = 0
        
        while start < len(text):
            # Extract chunk
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Create chunk with metadata
            chunk = {
                "text": chunk_text,
                "url": doc.get("url"),
                "title": doc.get("title"),
                "type": doc.get("type", "text"),
                "chunk_number": chunk_num,
                "metadata": doc.get("metadata", {}),
            }
            
            # Add structured data if present
            if doc.get("structured_data"):
                chunk["structured_data"] = doc["structured_data"]
            
            chunks.append(chunk)
            
            # Move to next chunk (with overlap)
            start = end - self.chunk_overlap
            chunk_num += 1
        
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        
        return embeddings.tolist()
    
    def ingest_structured_data(
        self,
        data: List[Dict[str, Any]],
        data_type: str = "structured",
    ) -> int:
        """
        Ingest structured data (tables, etc.).
        
        Args:
            data: List of structured data records
            data_type: Type of structured data
            
        Returns:
            Number of records ingested
        """
        logger.info(f"Ingesting {len(data)} structured records...")
        
        points = []
        
        for record in data:
            # Create searchable text from record
            text = self._record_to_text(record)
            
            # Generate embedding
            embedding = self._generate_embeddings([text])[0]
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": text,
                    "type": data_type,
                    "structured_data": record,
                    **record,  # Include all fields in payload
                },
            )
            points.append(point)
        
        # Upsert to Qdrant
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        
        logger.info(f"✓ Ingested {len(data)} structured records")
        return len(data)
    
    def _record_to_text(self, record: Dict[str, Any]) -> str:
        """
        Convert structured record to searchable text.
        
        Args:
            record: Structured data record
            
        Returns:
            Text representation
        """
        # Simple implementation: concatenate all values
        parts = []
        
        for key, value in record.items():
            if isinstance(value, (str, int, float)):
                parts.append(f"{key}: {value}")
        
        return " | ".join(parts)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information.
        
        Returns:
            Collection info dict
        """
        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vector_size": self.embedding_dim,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def list_documents(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List documents in collection.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of document payloads
        """
        try:
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            
            documents = []
            for point in results[0]:
                documents.append(point.payload)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def reset_collection(self):
        """Reset collection (delete all data)."""
        logger.warning(f"Resetting collection: {self.collection_name}")
        
        try:
            # Delete collection
            self.qdrant_client.delete_collection(self.collection_name)
            
            # Recreate
            self._ensure_collection()
            
            logger.info("✓ Collection reset")
            
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise
