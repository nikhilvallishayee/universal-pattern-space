"""
Vector Store for GodelOS Semantic Search.
"""

import logging
from typing import List, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Manages vector embeddings for semantic search using FAISS.
    """

    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2', dimension: int = 384):
        """
        Initialize the vector store with fallback for offline mode.

        Args:
            embedding_model: The name of the SentenceTransformer model to use.
            dimension: The dimension of the embeddings.
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.id_map = []
        
        # Try to load the embedding model with fallback
        try:
            # Test network connectivity first
            import requests
            response = requests.get("https://huggingface.co", timeout=5)
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"Successfully loaded SentenceTransformer model: {embedding_model}")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer model ({e}). Using fallback TF-IDF vectorizer.")
            self.embedding_model = None
            self._init_fallback_vectorizer()
        
        logger.info("VectorStore initialized.")
    
    def _init_fallback_vectorizer(self):
        """Initialize a fallback TF-IDF vectorizer when SentenceTransformer is unavailable."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            
            # Create TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Create dimensionality reduction to match expected dimension
            self.dimension_reducer = TruncatedSVD(n_components=min(384, 1000))
            self.fallback_texts = []  # Store texts for TF-IDF fitting
            
            logger.info("Fallback TF-IDF vectorizer initialized")
        except ImportError:
            logger.warning("sklearn not available. Vector search will be limited.")
            self.tfidf_vectorizer = None
            self.dimension_reducer = None

    def add_items(self, items: List[Tuple[str, str]]):
        """
        Add items to the vector store.

        Args:
            items: A list of tuples, where each tuple contains an ID and the text to embed.
        """
        if not items:
            return

        ids, texts = zip(*items)
        
        if self.embedding_model is not None:
            # Use SentenceTransformer
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            if embeddings.shape[0] > 0:
                self.index.add(embeddings.astype('float32'))
                self.id_map.extend(ids)
                logger.info(f"Added {len(items)} items to the vector store.")
        elif self.tfidf_vectorizer is not None:
            # Use TF-IDF fallback
            self.fallback_texts.extend(texts)
            self.id_map.extend(ids)
            
            # Refit the vectorizer with all texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.fallback_texts)
            reduced_embeddings = self.dimension_reducer.fit_transform(tfidf_matrix)
            
            # Pad or truncate to match expected dimension
            if reduced_embeddings.shape[1] < self.dimension:
                padding = np.zeros((reduced_embeddings.shape[0], self.dimension - reduced_embeddings.shape[1]))
                reduced_embeddings = np.hstack([reduced_embeddings, padding])
            elif reduced_embeddings.shape[1] > self.dimension:
                reduced_embeddings = reduced_embeddings[:, :self.dimension]
            
            # Rebuild the index with all embeddings
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(reduced_embeddings.astype('float32'))
            logger.info(f"Added {len(items)} items to the vector store using TF-IDF.")
        else:
            # No vectorization available - just store IDs for basic text matching
            self.id_map.extend(ids)
            logger.info(f"Added {len(items)} items with basic storage (no vectorization).")

    def search(self, query_text: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Search for similar items in the vector store.

        Args:
            query_text: The text to search for.
            k: The number of similar items to return.

        Returns:
            A list of tuples, where each tuple contains the ID of a similar item and its distance.
        """
        if len(self.id_map) == 0:
            return []

        if self.embedding_model is not None:
            # Use SentenceTransformer
            if self.index.ntotal == 0:
                return []
            
            query_embedding = self.embedding_model.encode([query_text], convert_to_tensor=False)
            distances, indices = self.index.search(query_embedding.astype('float32'), k)

            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                if idx < len(self.id_map):
                    results.append((self.id_map[idx], distances[0][i]))
                    
        elif self.tfidf_vectorizer is not None:
            # Use TF-IDF fallback
            if not hasattr(self, 'fallback_texts') or not self.fallback_texts:
                return []
                
            query_vector = self.tfidf_vectorizer.transform([query_text])
            query_reduced = self.dimension_reducer.transform(query_vector)
            
            # Pad or truncate to match dimension
            if query_reduced.shape[1] < self.dimension:
                padding = np.zeros((1, self.dimension - query_reduced.shape[1]))
                query_reduced = np.hstack([query_reduced, padding])
            elif query_reduced.shape[1] > self.dimension:
                query_reduced = query_reduced[:, :self.dimension]
            
            distances, indices = self.index.search(query_reduced.astype('float32'), min(k, self.index.ntotal))
            
            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                if idx < len(self.id_map):
                    results.append((self.id_map[idx], distances[0][i]))
        else:
            # Basic text matching fallback
            results = []
            query_lower = query_text.lower()
            for i, id_val in enumerate(self.id_map[:k]):
                # Basic relevance score based on whether query terms appear in ID
                score = 1.0 if any(word in id_val.lower() for word in query_lower.split()) else 0.5
                results.append((id_val, score))
        
        logger.info(f"Found {len(results)} results for query: '{query_text[:50]}...'")
        return results