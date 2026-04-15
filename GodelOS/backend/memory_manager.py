"""
Working Memory Manager for GödelOS

Handles persistent memory across conversations and queries.
"""

import asyncio
import time
import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class WorkingMemoryManager:
    def __init__(self):
        self.memory_store = {}
        self.session_memories = {}
        self.conversation_context = []
        self.max_memory_items = 50
        self.memory_decay_rate = 0.95  # How fast memories fade
        
    async def store_memory(self, session_id: str, content: str, memory_type: str = "factual"):
        """Store memory item with session tracking"""
        if session_id not in self.session_memories:
            self.session_memories[session_id] = []
            
        memory_item = {
            "id": f"mem_{session_id}_{len(self.session_memories[session_id])}",
            "content": content,
            "type": memory_type,
            "timestamp": time.time(),
            "activation_level": 1.0,
            "access_count": 0,
            "session_id": session_id,
            "importance": self._calculate_importance(content, memory_type)
        }
        
        self.session_memories[session_id].append(memory_item)
        logger.info(f"Stored memory: {content[:50]}{'...' if len(content) > 50 else ''}")
        
        # Manage memory capacity
        if len(self.session_memories[session_id]) > self.max_memory_items:
            await self._archive_old_memories(session_id)
            
        return memory_item["id"]
        
    async def retrieve_memories(self, session_id: str, query: str = None) -> List[Dict]:
        """Retrieve relevant memories for session"""
        if session_id not in self.session_memories:
            return []
            
        memories = self.session_memories[session_id]
        
        # Apply memory decay
        current_time = time.time()
        for memory in memories:
            age_factor = (current_time - memory["timestamp"]) / 3600  # Age in hours
            memory["activation_level"] *= (self.memory_decay_rate ** age_factor)
        
        if query:
            # Score memories by relevance
            scored_memories = []
            for memory in memories:
                relevance_score = self._calculate_memory_relevance(memory, query)
                if relevance_score > 0.3:
                    memory["relevance_score"] = relevance_score
                    memory["access_count"] += 1
                    scored_memories.append(memory)
            
            # Sort by combined relevance, importance, and activation
            scored_memories.sort(
                key=lambda m: (
                    m["relevance_score"] * 0.4 + 
                    m["importance"] * 0.3 + 
                    m["activation_level"] * 0.3
                ), 
                reverse=True
            )
            return scored_memories[:10]
        
        # Return most recent and important memories
        memories.sort(key=lambda m: (m["importance"] * m["activation_level"], m["timestamp"]), reverse=True)
        return memories[:10]
    
    async def check_for_memory_request(self, query: str) -> Optional[str]:
        """Check if query contains a memory storage request"""
        memory_patterns = [
            r"remember\s+(?:that\s+)?(.+)",
            r"keep\s+in\s+mind\s+(?:that\s+)?(.+)",
            r"don't\s+forget\s+(?:that\s+)?(.+)",
            r"note\s+(?:that\s+)?(.+)",
            r"my\s+favorite\s+(.+)\s+is\s+(.+)",
            r"i\s+(?:like|prefer|enjoy)\s+(.+)"
        ]
        
        for pattern in memory_patterns:
            match = re.search(pattern, query.lower())
            if match:
                if len(match.groups()) == 1:
                    return match.group(1).strip()
                else:
                    # Handle patterns with multiple groups (like "my favorite X is Y")
                    return " ".join(match.groups()).strip()
        
        return None
    
    def _calculate_importance(self, content: str, memory_type: str) -> float:
        """Calculate importance score for memory item"""
        base_importance = {
            "factual": 0.7,
            "personal": 0.9,
            "preference": 0.8,
            "procedural": 0.6,
            "contextual": 0.5
        }.get(memory_type, 0.5)
        
        # Boost importance for personal information
        personal_indicators = ["my", "i", "me", "mine", "favorite", "prefer", "like", "dislike"]
        personal_score = sum(1 for indicator in personal_indicators if indicator in content.lower()) * 0.1
        
        # Boost importance for specific facts
        specific_indicators = ["is", "are", "was", "were", "called", "named", "located"]
        specific_score = sum(1 for indicator in specific_indicators if indicator in content.lower()) * 0.05
        
        return min(1.0, base_importance + personal_score + specific_score)
        
    def _calculate_memory_relevance(self, memory: Dict, query: str) -> float:
        """Calculate relevance score between memory and query"""
        memory_words = set(memory["content"].lower().split())
        query_words = set(query.lower().split())
        
        if not memory_words or not query_words:
            return 0.0
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        memory_words = memory_words - stop_words
        query_words = query_words - stop_words
        
        if not memory_words or not query_words:
            return 0.0
            
        intersection = memory_words.intersection(query_words)
        union = memory_words.union(query_words)
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Boost score if query asks about memory type
        type_boost = 0.2 if any(word in query.lower() for word in ["favorite", "prefer", "like"]) and memory["type"] == "personal" else 0.0
        
        return min(1.0, jaccard_similarity + type_boost)
    
    async def _archive_old_memories(self, session_id: str):
        """Archive old or low-importance memories"""
        memories = self.session_memories[session_id]
        
        # Sort by activation level and importance
        memories.sort(key=lambda m: (m["activation_level"], m["importance"]), reverse=True)
        
        # Keep the top memories, archive the rest
        keep_count = int(self.max_memory_items * 0.8)  # Keep 80% of max capacity
        self.session_memories[session_id] = memories[:keep_count]
        
        archived_count = len(memories) - keep_count
        if archived_count > 0:
            logger.info(f"Archived {archived_count} old memories for session {session_id}")
    
    def get_memory_stats(self, session_id: str) -> Dict[str, Any]:
        """Get memory statistics for a session"""
        if session_id not in self.session_memories:
            return {"total_memories": 0, "active_memories": 0, "memory_types": {}}
        
        memories = self.session_memories[session_id]
        active_memories = [m for m in memories if m["activation_level"] > 0.3]
        
        memory_types = {}
        for memory in memories:
            mem_type = memory["type"]
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
        
        return {
            "total_memories": len(memories),
            "active_memories": len(active_memories),
            "memory_types": memory_types,
            "oldest_memory": min(memories, key=lambda m: m["timestamp"])["timestamp"] if memories else None,
            "newest_memory": max(memories, key=lambda m: m["timestamp"])["timestamp"] if memories else None
        }

# Global instance
memory_manager = WorkingMemoryManager()
