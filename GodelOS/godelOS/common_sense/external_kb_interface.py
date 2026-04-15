"""
Module 9.1: External Common Sense Knowledge Base Interface (ECSKI)

This module provides interfaces to external common sense knowledge bases such as
ConceptNet and WordNet. It handles querying, caching, normalization, and fallback
mechanisms for external knowledge sources.
"""

import json
import os
import time
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from pathlib import Path
import requests
from urllib.parse import quote
import nltk
from nltk.corpus import wordnet as wn

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.scalability.caching import CachingSystem

# Configure logging
logger = logging.getLogger(__name__)


class ExternalCommonSenseKB_Interface:
    """Interface to external common sense knowledge bases.
    
    This class provides methods for querying external knowledge bases like
    ConceptNet and WordNet, handling caching of frequently used knowledge,
    normalizing external knowledge into GödelOS's internal representation,
    and implementing fallback mechanisms for when external sources are unavailable.
    """
    
    def __init__(self, 
                 knowledge_store: KnowledgeStoreInterface,
                 cache_system: Optional[CachingSystem] = None,
                 cache_dir: str = "cache/common_sense",
                 conceptnet_api_url: str = "http://api.conceptnet.io/c/en/",
                 wordnet_enabled: bool = True,
                 conceptnet_enabled: bool = True,
                 max_cache_age: int = 86400 * 7,  # 1 week in seconds
                 offline_mode: bool = False):
        """Initialize the External Common Sense KB Interface.
        
        Args:
            knowledge_store: The knowledge store to integrate external knowledge with
            cache_system: Optional caching system from the Scalability module
            cache_dir: Directory to store cached knowledge
            conceptnet_api_url: URL for the ConceptNet API
            wordnet_enabled: Whether to enable WordNet as a knowledge source
            conceptnet_enabled: Whether to enable ConceptNet as a knowledge source
            max_cache_age: Maximum age of cached data in seconds
            offline_mode: If True, only use cached data and don't query external sources
        """
        self.knowledge_store = knowledge_store
        self.cache_system = cache_system
        self.cache_dir = cache_dir
        self.conceptnet_api_url = conceptnet_api_url
        self.wordnet_enabled = wordnet_enabled
        self.conceptnet_enabled = conceptnet_enabled
        self.max_cache_age = max_cache_age
        self.offline_mode = offline_mode
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize WordNet if enabled
        if self.wordnet_enabled:
            try:
                nltk.data.find('corpora/wordnet')
            except LookupError:
                logger.info("Downloading WordNet...")
                try:
                    nltk.download('wordnet', quiet=True)
                    logger.info("WordNet downloaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to download WordNet: {e}")
                    logger.warning("Some WordNet functionality may be unavailable")
    
    def query_concept(self, concept: str, relation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query information about a concept from external knowledge bases.
        
        Args:
            concept: The concept to query
            relation_types: Optional list of relation types to filter by
            
        Returns:
            Dictionary containing normalized information about the concept
        """
        # Normalize concept name
        concept = concept.lower().replace(' ', '_')
        
        # Check cache first
        cached_data = self._get_from_cache(f"concept_{concept}")
        if cached_data:
            return cached_data
        
        # Initialize result dictionary
        result = {
            "concept": concept,
            "relations": [],
            "definitions": [],
            "source": []
        }
        
        # Query enabled knowledge bases
        if self.wordnet_enabled and not self.offline_mode:
            wordnet_data = self._query_wordnet(concept)
            if wordnet_data:
                result["definitions"].extend(wordnet_data["definitions"])
                result["relations"].extend(wordnet_data["relations"])
                if "wordnet" not in result["source"]:
                    result["source"].append("wordnet")
        
        if self.conceptnet_enabled and not self.offline_mode:
            conceptnet_data = self._query_conceptnet(concept)
            if conceptnet_data:
                # Filter by relation types if specified
                if relation_types:
                    conceptnet_data["relations"] = [
                        r for r in conceptnet_data["relations"] 
                        if r["relation"] in relation_types
                    ]
                
                result["relations"].extend(conceptnet_data["relations"])
                if "conceptnet" not in result["source"]:
                    result["source"].append("conceptnet")
        
        # Filter relations by type if needed
        if relation_types:
            result["relations"] = [
                r for r in result["relations"] 
                if r["relation"] in relation_types
            ]
        
        # Cache the result
        self._save_to_cache(f"concept_{concept}", result)
        
        # Add to knowledge store in normalized form
        self._integrate_with_knowledge_store(result)
        
        return result
    
    def query_relation(self, source_concept: str, target_concept: str, 
                       relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query relations between two concepts.
        
        Args:
            source_concept: The source concept
            target_concept: The target concept
            relation_type: Optional specific relation type to query
            
        Returns:
            List of relations between the concepts
        """
        # Normalize concept names
        source_concept = source_concept.lower().replace(' ', '_')
        target_concept = target_concept.lower().replace(' ', '_')
        
        # Check cache first
        cache_key = f"relation_{source_concept}_{target_concept}"
        if relation_type:
            cache_key += f"_{relation_type}"
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Initialize results
        relations = []
        
        # Query source concept to get all its relations
        source_data = self.query_concept(source_concept)
        
        # Filter relations that connect to target concept
        for rel in source_data["relations"]:
            if rel["target"] == target_concept:
                if relation_type is None or rel["relation"] == relation_type:
                    relations.append(rel)
        
        # If no direct relations found and not in offline mode, query ConceptNet directly
        if not relations and self.conceptnet_enabled and not self.offline_mode:
            try:
                url = f"{self.conceptnet_api_url}{quote(source_concept)}/r?other={quote(target_concept)}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for edge in data.get("edges", []):
                        rel = self._normalize_conceptnet_relation(edge)
                        if relation_type is None or rel["relation"] == relation_type:
                            relations.append(rel)
            except Exception as e:
                logger.warning(f"Error querying ConceptNet for relation: {e}")
        
        # Cache the result
        self._save_to_cache(cache_key, relations)
        
        return relations
    
    def get_common_sense_facts(self, concept: str, limit: int = 10) -> List[str]:
        """Get common sense facts about a concept in natural language.
        
        Args:
            concept: The concept to get facts about
            limit: Maximum number of facts to return
            
        Returns:
            List of natural language facts about the concept
        """
        # Query the concept
        concept_data = self.query_concept(concept)
        
        # Convert relations to natural language facts
        facts = []
        for relation in concept_data["relations"][:limit]:
            fact = self._relation_to_natural_language(relation)
            if fact:
                facts.append(fact)
        
        # Add definitions as facts
        for definition in concept_data["definitions"][:limit]:
            facts.append(f"{concept.replace('_', ' ')} is defined as: {definition}")
        
        return facts[:limit]
    
    def _query_wordnet(self, concept: str) -> Optional[Dict[str, Any]]:
        """Query WordNet for information about a concept.
        
        Args:
            concept: The concept to query
            
        Returns:
            Dictionary with WordNet information or None if not found
        """
        try:
            # Replace underscores with spaces for WordNet lookup
            concept_for_lookup = concept.replace('_', ' ')
            
            # Get synsets for the concept
            synsets = wn.synsets(concept_for_lookup)
            
            if not synsets:
                return None
            
            result = {
                "definitions": [],
                "relations": []
            }
            
            # Get definitions and examples
            for synset in synsets:
                result["definitions"].append(synset.definition())
                
                # Get hypernyms (is-a relations)
                for hypernym in synset.hypernyms():
                    relation = {
                        "source": concept,
                        "relation": "is_a",
                        "target": hypernym.name().split('.')[0],
                        "weight": 1.0,
                        "source_kb": "wordnet"
                    }
                    result["relations"].append(relation)
                
                # Get hyponyms (has-type relations)
                for hyponym in synset.hyponyms():
                    relation = {
                        "source": concept,
                        "relation": "has_type",
                        "target": hyponym.name().split('.')[0],
                        "weight": 1.0,
                        "source_kb": "wordnet"
                    }
                    result["relations"].append(relation)
                
                # Get meronyms (has-part relations)
                for meronym in synset.part_meronyms():
                    relation = {
                        "source": concept,
                        "relation": "has_part",
                        "target": meronym.name().split('.')[0],
                        "weight": 1.0,
                        "source_kb": "wordnet"
                    }
                    result["relations"].append(relation)
                
                # Get holonyms (part-of relations)
                for holonym in synset.part_holonyms():
                    relation = {
                        "source": concept,
                        "relation": "part_of",
                        "target": holonym.name().split('.')[0],
                        "weight": 1.0,
                        "source_kb": "wordnet"
                    }
                    result["relations"].append(relation)
            
            return result
            
        except Exception as e:
            logger.warning(f"Error querying WordNet: {e}")
            return None
    
    def _query_conceptnet(self, concept: str) -> Optional[Dict[str, Any]]:
        """Query ConceptNet for information about a concept.
        
        Args:
            concept: The concept to query
            
        Returns:
            Dictionary with ConceptNet information or None if not found
        """
        try:
            url = f"{self.conceptnet_api_url}{quote(concept)}"
            response = requests.get(url)
            
            if response.status_code != 200:
                logger.warning(f"ConceptNet API returned status {response.status_code}")
                return None
            
            data = response.json()
            
            result = {
                "relations": []
            }
            
            # Process edges (relations)
            for edge in data.get("edges", []):
                relation = self._normalize_conceptnet_relation(edge)
                result["relations"].append(relation)
            
            return result
            
        except Exception as e:
            logger.warning(f"Error querying ConceptNet: {e}")
            return None
    
    def _normalize_conceptnet_relation(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a ConceptNet relation to the internal format.
        
        Args:
            edge: The ConceptNet edge data
            
        Returns:
            Normalized relation dictionary
        """
        # Extract source and target concepts
        source = edge["start"]["label"].lower() if "label" in edge["start"] else ""
        target = edge["end"]["label"].lower() if "label" in edge["end"] else ""
        
        # Extract relation type (remove /r/ prefix)
        relation = edge["rel"]["label"].lower() if "label" in edge["rel"] else ""
        
        # Extract weight
        weight = edge.get("weight", 1.0)
        
        # Normalize relation type
        relation_mapping = {
            "isa": "is_a",
            "partof": "part_of",
            "haspart": "has_part",
            "madeof": "made_of",
            "usedfor": "used_for",
            "capableof": "capable_of",
            "atlocation": "at_location",
            "causes": "causes",
            "hassubevent": "has_subevent",
            "hasproperty": "has_property",
            "motivatedbygoal": "motivated_by_goal",
            "hascontext": "has_context",
            "conceptuallyrelatedto": "related_to",
            "similarto": "similar_to",
            "synonym": "synonym",
            "antonym": "antonym",
            "derivedfrom": "derived_from",
            "symbolof": "symbol_of",
            "definedas": "defined_as",
            "externalurl": "external_url",
            "formof": "form_of",
            "etymologicallyrelatedto": "etymologically_related_to",
            "etymologicallyderivedfrom": "etymologically_derived_from",
            "causesdesire": "causes_desire",
            "createdby": "created_by",
            "hasfirstsubevent": "has_first_subevent",
            "haslastsubevent": "has_last_subevent",
            "hasprerequisite": "has_prerequisite",
            "hasa": "has_a",
            "memberof": "member_of",
            "receivesaction": "receives_action",
            "obstructedby": "obstructed_by",
        }
        
        normalized_relation = relation_mapping.get(relation.replace(" ", ""), relation)
        
        return {
            "source": source.replace(" ", "_"),
            "relation": normalized_relation,
            "target": target.replace(" ", "_"),
            "weight": weight,
            "source_kb": "conceptnet"
        }
    
    def _relation_to_natural_language(self, relation: Dict[str, Any]) -> Optional[str]:
        """Convert a relation to a natural language statement.
        
        Args:
            relation: The relation dictionary
            
        Returns:
            Natural language statement or None if conversion not possible
        """
        source = relation["source"].replace("_", " ")
        target = relation["target"].replace("_", " ")
        rel_type = relation["relation"]
        
        # Map relation types to natural language templates
        templates = {
            "is_a": "{source} is a type of {target}.",
            "has_type": "{source} has a type called {target}.",
            "part_of": "{source} is part of {target}.",
            "has_part": "{source} has {target} as a part.",
            "made_of": "{source} is made of {target}.",
            "used_for": "{source} is used for {target}.",
            "capable_of": "{source} can {target}.",
            "at_location": "{source} is typically found at {target}.",
            "causes": "{source} causes {target}.",
            "has_subevent": "{source} involves {target}.",
            "has_property": "{source} is {target}.",
            "motivated_by_goal": "{source} is motivated by wanting to {target}.",
            "has_context": "{source} is relevant in the context of {target}.",
            "related_to": "{source} is related to {target}.",
            "similar_to": "{source} is similar to {target}.",
            "synonym": "{source} means the same as {target}.",
            "antonym": "{source} means the opposite of {target}.",
            "derived_from": "{source} is derived from {target}.",
            "symbol_of": "{source} is a symbol of {target}.",
            "defined_as": "{source} is defined as {target}.",
        }
        
        if rel_type in templates:
            return templates[rel_type].format(source=source, target=target)
        else:
            return f"{source} {rel_type.replace('_', ' ')} {target}."
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found or expired
        """
        # Try to use the caching system from the Scalability module if available
        if self.cache_system:
            return self.cache_system.get(f"common_sense:{key}")
        
        # Otherwise use file-based caching
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Check if cache is expired
        if self.max_cache_age > 0:
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age > self.max_cache_age:
                return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading cache file {cache_file}: {e}")
            return None
    
    def _save_to_cache(self, key: str, data: Any) -> None:
        """Save data to cache.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        # Try to use the caching system from the Scalability module if available
        if self.cache_system:
            self.cache_system.set(f"common_sense:{key}", data, ttl=self.max_cache_age)
            return
        
        # Otherwise use file-based caching
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Error writing to cache file {cache_file}: {e}")
    
    def _integrate_with_knowledge_store(self, concept_data: Dict[str, Any]) -> None:
        """Integrate external knowledge into the knowledge store.
        
        Args:
            concept_data: Concept data to integrate
        """
        # This method would convert the external knowledge into the format
        # expected by the knowledge store and add it to the store
        
        # For now, we'll just implement a basic integration
        try:
            concept = concept_data["concept"]
            
            # Add concept as an entity
            self.knowledge_store.add_entity(concept)
            
            # Add relations
            for relation in concept_data.get("relations", []):
                source = relation["source"]
                rel_type = relation["relation"]
                target = relation["target"]
                weight = relation.get("weight", 1.0)
                
                # Add the target as an entity if it doesn't exist
                self.knowledge_store.add_entity(target)
                
                # Add the relation with confidence based on weight
                self.knowledge_store.add_relation(source, rel_type, target, confidence=weight)
            
            # Add definitions as properties
            for i, definition in enumerate(concept_data.get("definitions", [])):
                self.knowledge_store.add_property(concept, "definition", definition)
                
        except Exception as e:
            logger.warning(f"Error integrating concept {concept_data.get('concept')} with knowledge store: {e}")
    
    def get_fallback_knowledge(self, concept: str) -> Dict[str, Any]:
        """Get fallback knowledge when external sources are unavailable.
        
        Args:
            concept: The concept to get knowledge for
            
        Returns:
            Dictionary with fallback knowledge
        """
        # Check if we have cached data first
        cached_data = self._get_from_cache(f"concept_{concept}")
        if cached_data:
            return cached_data
        
        # If no cached data and we're in offline mode, return minimal information
        logger.debug(f"Returning fallback knowledge for concept: {concept}")
        return {
            "concept": concept,
            "relations": [],
            "definitions": [],
            "source": ["fallback"]
        }
    
    def bulk_import_concepts(self, concepts: List[str]) -> Dict[str, bool]:
        """Import multiple concepts at once.
        
        Args:
            concepts: List of concepts to import
            
        Returns:
            Dictionary mapping concepts to success status
        """
        results = {}
        
        for concept in concepts:
            try:
                self.query_concept(concept)
                results[concept] = True
            except Exception as e:
                logger.warning(f"Error importing concept {concept}: {e}")
                results[concept] = False
        
        return results
    
    def clear_cache(self, concept: Optional[str] = None) -> None:
        """Clear the cache for a specific concept or all concepts.
        
        Args:
            concept: Optional concept to clear cache for. If None, clear all cache.
        """
        if self.cache_system:
            if concept:
                # Delete specific concept from cache
                self.cache_system.delete(f"common_sense:concept_{concept}")
                # Also delete any relation cache entries involving this concept
                self.cache_system.delete(f"common_sense:relation_{concept}_*")
            else:
                # Clear all common sense cache entries
                # This depends on the implementation of the cache system
                # For now, we'll just log that this operation is not fully supported
                logger.info("Clearing all cache entries is not fully supported with the caching system")
        else:
            # File-based cache clearing
            if concept:
                # Clear specific concept cache
                logger.debug(f"Clearing cache for concept: {concept}")
                
                # The exact filename format used in the tests
                concept_file = os.path.join(self.cache_dir, f"concept_{concept}.json")
                if os.path.exists(concept_file):
                    try:
                        os.remove(concept_file)
                        logger.debug(f"Removed cache file: {concept_file}")
                    except Exception as e:
                        logger.warning(f"Error removing cache file {concept_file}: {e}")
                
                # Also check for any relation files with this concept
                for file in os.listdir(self.cache_dir):
                    if file.startswith(f"relation_{concept}_") and file.endswith(".json"):
                        try:
                            os.remove(os.path.join(self.cache_dir, file))
                            logger.debug(f"Removed cache file: {file}")
                        except Exception as e:
                            logger.warning(f"Error removing cache file {file}: {e}")
            else:
                # Clear all cache files
                logger.debug("Clearing all cache files")
                for file in os.listdir(self.cache_dir):
                    if file.endswith(".json"):
                        try:
                            os.remove(os.path.join(self.cache_dir, file))
                            logger.debug(f"Removed cache file: {file}")
                        except Exception as e:
                            logger.warning(f"Error removing cache file {file}: {e}")