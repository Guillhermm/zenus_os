"""
Semantic Search for Command History

Find similar past commands using sentence embeddings.
Enables learning from previous interactions.
"""

import os
import json
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from pathlib import Path


class SemanticSearch:
    """
    Search past commands semantically
    
    Uses sentence-transformers to find similar commands
    even when wording differs.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic search
        
        Args:
            model_name: Sentence transformer model (default is lightweight)
        """
        self.model = SentenceTransformer(model_name)
        self.cache_dir = Path.home() / ".zenus" / "semantic_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.embeddings_file = self.cache_dir / "embeddings.npy"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        self.embeddings = None
        self.metadata = []
        
        self._load_cache()
    
    def _load_cache(self):
        """Load cached embeddings and metadata"""
        if self.embeddings_file.exists() and self.metadata_file.exists():
            try:
                self.embeddings = np.load(self.embeddings_file)
                with open(self.metadata_file) as f:
                    self.metadata = json.load(f)
            except:
                # Cache corrupted, start fresh
                self.embeddings = None
                self.metadata = []
    
    def _save_cache(self):
        """Save embeddings and metadata to disk"""
        if self.embeddings is not None:
            np.save(self.embeddings_file, self.embeddings)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f)
    
    def add_command(
        self, 
        user_input: str, 
        goal: str, 
        steps: List[Dict],
        success: bool,
        timestamp: Optional[float] = None
    ):
        """
        Add a command to the search index
        
        Args:
            user_input: What user typed
            goal: Interpreted goal
            steps: Execution steps
            success: Whether it succeeded
            timestamp: Unix timestamp (defaults to now)
        """
        import time
        
        if timestamp is None:
            timestamp = time.time()
        
        # Create searchable text
        search_text = f"{user_input} {goal}"
        
        # Generate embedding
        embedding = self.model.encode(search_text, show_progress_bar=False)
        
        # Add to index
        if self.embeddings is None:
            self.embeddings = embedding.reshape(1, -1)
        else:
            self.embeddings = np.vstack([self.embeddings, embedding])
        
        # Add metadata
        self.metadata.append({
            "user_input": user_input,
            "goal": goal,
            "steps": steps,
            "success": success,
            "timestamp": timestamp
        })
        
        # Save to disk
        self._save_cache()
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        Search for similar past commands
        
        Args:
            query: Search query (user input)
            top_k: Number of results to return
            min_similarity: Minimum cosine similarity (0-1)
        
        Returns:
            List of similar commands with metadata
        """
        if self.embeddings is None or len(self.metadata) == 0:
            return []
        
        # Encode query
        query_embedding = self.model.encode(query, show_progress_bar=False)
        
        # Compute cosine similarities
        similarities = self._cosine_similarity(query_embedding, self.embeddings)
        
        # Get top K
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Filter by minimum similarity
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= min_similarity:
                result = self.metadata[idx].copy()
                result["similarity"] = similarity
                results.append(result)
        
        return results
    
    def _cosine_similarity(self, query_vec: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all embeddings"""
        # Normalize vectors
        query_norm = query_vec / np.linalg.norm(query_vec)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Dot product = cosine similarity for normalized vectors
        return np.dot(embeddings_norm, query_norm)
    
    def get_success_rate(self, query: str, top_k: int = 10) -> float:
        """
        Get success rate for similar past commands
        
        Useful for confidence estimation.
        """
        results = self.search(query, top_k=top_k, min_similarity=0.6)
        
        if not results:
            return 0.5  # Unknown, assume 50%
        
        successes = sum(1 for r in results if r["success"])
        return successes / len(results)
    
    def get_stats(self) -> Dict:
        """Get statistics about the search index"""
        if not self.metadata:
            return {
                "total_commands": 0,
                "success_rate": 0.0
            }
        
        total = len(self.metadata)
        successes = sum(1 for m in self.metadata if m["success"])
        
        return {
            "total_commands": total,
            "success_rate": successes / total if total > 0 else 0.0,
            "cache_size_mb": self.embeddings.nbytes / 1024 / 1024 if self.embeddings is not None else 0
        }
