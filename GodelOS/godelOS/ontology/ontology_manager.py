"""
Ontology Manager (OM) for GödelOS.

This module provides the OntologyManager class, which is responsible for managing
the system's ontology, including concepts, relations, and properties.
"""

from typing import Dict, List, Set, Optional, Any, Tuple
import logging
from collections import defaultdict

# Setup logging
logger = logging.getLogger(__name__)

class OntologyManager:
    """
    Manages the system's ontology, including concepts, relations, and properties.
    
    The OntologyManager is responsible for:
    - Managing the system's ontology (concepts, relations, properties)
    - Supporting operations for adding, removing, and modifying ontological elements
    - Ensuring ontological consistency and integrity
    - Providing query mechanisms for ontological information
    - Integrating with the KR System for knowledge representation
    """
    
    def __init__(self):
        """Initialize the OntologyManager."""
        # Core data structures
        self._concepts = {}  # Dict[str, Dict[str, Any]] - concept_id -> concept data
        self._relations = {}  # Dict[str, Dict[str, Any]] - relation_id -> relation data
        self._properties = {}  # Dict[str, Dict[str, Any]] - property_id -> property data
        
        # Indices for efficient querying
        self._concept_relations = defaultdict(set)  # Dict[str, Set[str]] - concept_id -> relation_ids
        self._relation_concepts = defaultdict(list)  # Dict[str, List[Tuple[str, str]]] - relation_id -> [(subject_id, object_id)]
        self._concept_properties = defaultdict(dict)  # Dict[str, Dict[str, Any]] - concept_id -> {property_id: value}
        
        # Taxonomic relationships
        self._is_a_hierarchy = defaultdict(set)  # Dict[str, Set[str]] - concept_id -> parent_concept_ids
        self._has_part_hierarchy = defaultdict(set)  # Dict[str, Set[str]] - concept_id -> part_concept_ids
        
        logger.info("OntologyManager initialized")
    
    # Concept management methods
    
    def add_concept(self, concept_id: str, concept_data: Dict[str, Any]) -> bool:
        """
        Add a new concept to the ontology.
        
        Args:
            concept_id: Unique identifier for the concept
            concept_data: Dictionary containing concept information
            
        Returns:
            bool: True if the concept was added successfully, False otherwise
        """
        if concept_id in self._concepts:
            logger.warning(f"Concept {concept_id} already exists")
            return False
        
        self._concepts[concept_id] = concept_data
        logger.info(f"Added concept: {concept_id}")
        return True
    
    def remove_concept(self, concept_id: str) -> bool:
        """
        Remove a concept from the ontology.
        
        Args:
            concept_id: Identifier of the concept to remove
            
        Returns:
            bool: True if the concept was removed successfully, False otherwise
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return False
        
        # Remove the concept
        del self._concepts[concept_id]
        
        # Clean up related data structures
        for relation_id in list(self._concept_relations[concept_id]):
            self.remove_relation_from_concept(concept_id, relation_id)
        
        # Remove from taxonomic hierarchies
        if concept_id in self._is_a_hierarchy:
            del self._is_a_hierarchy[concept_id]
        
        for parent_id, children in self._is_a_hierarchy.items():
            if concept_id in children:
                children.remove(concept_id)
        
        # Similar cleanup for has_part hierarchy
        if concept_id in self._has_part_hierarchy:
            del self._has_part_hierarchy[concept_id]
        
        for whole_id, parts in self._has_part_hierarchy.items():
            if concept_id in parts:
                parts.remove(concept_id)
        
        # Remove properties
        if concept_id in self._concept_properties:
            del self._concept_properties[concept_id]
        
        logger.info(f"Removed concept: {concept_id}")
        return True
    
    def update_concept(self, concept_id: str, concept_data: Dict[str, Any]) -> bool:
        """
        Update an existing concept in the ontology.
        
        Args:
            concept_id: Identifier of the concept to update
            concept_data: New data for the concept
            
        Returns:
            bool: True if the concept was updated successfully, False otherwise
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return False
        
        self._concepts[concept_id] = concept_data
        logger.info(f"Updated concept: {concept_id}")
        return True
    
    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a concept from the ontology.
        
        Args:
            concept_id: Identifier of the concept to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The concept data if found, None otherwise
        """
        return self._concepts.get(concept_id)
    
    def get_all_concepts(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all concepts in the ontology.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping concept IDs to concept data
        """
        return self._concepts.copy()
    
    # Relation management methods
    
    def add_relation(self, relation_id: str, relation_data: Dict[str, Any]) -> bool:
        """
        Add a new relation type to the ontology.
        
        Args:
            relation_id: Unique identifier for the relation
            relation_data: Dictionary containing relation information
            
        Returns:
            bool: True if the relation was added successfully, False otherwise
        """
        if relation_id in self._relations:
            logger.warning(f"Relation {relation_id} already exists")
            return False
        
        self._relations[relation_id] = relation_data
        logger.info(f"Added relation: {relation_id}")
        return True
    
    def add_relation_instance(self, relation_id: str, subject_id: str, object_id: str) -> bool:
        """
        Add a relation instance between two concepts.
        
        Args:
            relation_id: Identifier of the relation type
            subject_id: Identifier of the subject concept
            object_id: Identifier of the object concept
            
        Returns:
            bool: True if the relation instance was added successfully, False otherwise
        """
        if relation_id not in self._relations:
            logger.warning(f"Relation {relation_id} does not exist")
            return False
        
        if subject_id not in self._concepts:
            logger.warning(f"Subject concept {subject_id} does not exist")
            return False
        
        if object_id not in self._concepts:
            logger.warning(f"Object concept {object_id} does not exist")
            return False
        
        # Add to indices
        self._concept_relations[subject_id].add(relation_id)
        self._relation_concepts[relation_id].append((subject_id, object_id))
        
        # Special handling for taxonomic relations
        if relation_id == "is_a":
            self._is_a_hierarchy[subject_id].add(object_id)
        elif relation_id == "has_part":
            self._has_part_hierarchy[subject_id].add(object_id)
        
        logger.info(f"Added relation instance: {subject_id} -{relation_id}-> {object_id}")
        return True
    
    def remove_relation_from_concept(self, concept_id: str, relation_id: str) -> bool:
        """
        Remove all instances of a relation from a concept.
        
        Args:
            concept_id: Identifier of the concept
            relation_id: Identifier of the relation
            
        Returns:
            bool: True if the relation instances were removed successfully, False otherwise
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return False
        
        if relation_id not in self._relations:
            logger.warning(f"Relation {relation_id} does not exist")
            return False
        
        # Remove from concept_relations
        if relation_id in self._concept_relations[concept_id]:
            self._concept_relations[concept_id].remove(relation_id)
        
        # Remove from relation_concepts
        self._relation_concepts[relation_id] = [
            (subj, obj) for subj, obj in self._relation_concepts[relation_id]
            if subj != concept_id
        ]
        
        # Special handling for taxonomic relations
        if relation_id == "is_a" and concept_id in self._is_a_hierarchy:
            del self._is_a_hierarchy[concept_id]
        elif relation_id == "has_part" and concept_id in self._has_part_hierarchy:
            del self._has_part_hierarchy[concept_id]
        
        logger.info(f"Removed relation {relation_id} from concept {concept_id}")
        return True
    
    # Property management methods
    
    def add_property(self, property_id: str, property_data: Dict[str, Any]) -> bool:
        """
        Add a new property type to the ontology.
        
        Args:
            property_id: Unique identifier for the property
            property_data: Dictionary containing property information
            
        Returns:
            bool: True if the property was added successfully, False otherwise
        """
        if property_id in self._properties:
            logger.warning(f"Property {property_id} already exists")
            return False
        
        self._properties[property_id] = property_data
        logger.info(f"Added property: {property_id}")
        return True
    
    def set_concept_property(self, concept_id: str, property_id: str, value: Any) -> bool:
        """
        Set a property value for a concept.
        
        Args:
            concept_id: Identifier of the concept
            property_id: Identifier of the property
            value: Value to set for the property
            
        Returns:
            bool: True if the property was set successfully, False otherwise
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return False
        
        if property_id not in self._properties:
            logger.warning(f"Property {property_id} does not exist")
            return False
        
        self._concept_properties[concept_id][property_id] = value
        logger.info(f"Set property {property_id} for concept {concept_id}")
        return True
    
    def get_concept_property(self, concept_id: str, property_id: str) -> Optional[Any]:
        """
        Get a property value for a concept.
        
        Args:
            concept_id: Identifier of the concept
            property_id: Identifier of the property
            
        Returns:
            Optional[Any]: The property value if found, None otherwise
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return None
        
        if property_id not in self._properties:
            logger.warning(f"Property {property_id} does not exist")
            return None
        
        return self._concept_properties.get(concept_id, {}).get(property_id)
    
    # Query methods
    
    def get_related_concepts(self, concept_id: str, relation_id: str) -> List[str]:
        """
        Get concepts related to the given concept via the specified relation.
        
        Args:
            concept_id: Identifier of the concept
            relation_id: Identifier of the relation
            
        Returns:
            List[str]: List of concept IDs related to the given concept
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return []
        
        if relation_id not in self._relations:
            logger.warning(f"Relation {relation_id} does not exist")
            return []
        
        related_concepts = []
        for subj, obj in self._relation_concepts[relation_id]:
            if subj == concept_id:
                related_concepts.append(obj)
        
        return related_concepts
    
    def get_concepts_with_property(self, property_id: str, value: Optional[Any] = None) -> List[str]:
        """
        Get concepts that have the specified property, optionally with a specific value.
        
        Args:
            property_id: Identifier of the property
            value: Optional value to match
            
        Returns:
            List[str]: List of concept IDs with the specified property
        """
        if property_id not in self._properties:
            logger.warning(f"Property {property_id} does not exist")
            return []
        
        matching_concepts = []
        for concept_id, properties in self._concept_properties.items():
            if property_id in properties:
                if value is None or properties[property_id] == value:
                    matching_concepts.append(concept_id)
        
        return matching_concepts
    
    # Taxonomic query methods
    
    def get_parent_concepts(self, concept_id: str) -> Set[str]:
        """
        Get the parent concepts of the given concept (via is_a relation).
        
        Args:
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of parent concept IDs
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return set()
        
        return self._is_a_hierarchy.get(concept_id, set()).copy()
    
    def get_child_concepts(self, concept_id: str) -> Set[str]:
        """
        Get the child concepts of the given concept (via is_a relation).
        
        Args:
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of child concept IDs
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return set()
        
        children = set()
        for child_id, parents in self._is_a_hierarchy.items():
            if concept_id in parents:
                children.add(child_id)
        
        return children
    
    def get_part_concepts(self, concept_id: str) -> Set[str]:
        """
        Get the part concepts of the given concept (via has_part relation).
        
        Args:
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of part concept IDs
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return set()
        
        return self._has_part_hierarchy.get(concept_id, set()).copy()
    
    def get_whole_concepts(self, concept_id: str) -> Set[str]:
        """
        Get the whole concepts that the given concept is a part of (via has_part relation).
        
        Args:
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of whole concept IDs
        """
        if concept_id not in self._concepts:
            logger.warning(f"Concept {concept_id} does not exist")
            return set()
        
        wholes = set()
        for whole_id, parts in self._has_part_hierarchy.items():
            if concept_id in parts:
                wholes.add(whole_id)
        
        return wholes
    
    # Consistency and integrity methods
    
    def check_consistency(self) -> List[str]:
        """
        Check the consistency of the ontology and return any inconsistencies found.
        
        Returns:
            List[str]: List of inconsistency descriptions
        """
        inconsistencies = []
        
        # Check for circular is_a relationships
        for concept_id in self._concepts:
            visited = set()
            to_visit = list(self.get_parent_concepts(concept_id))
            
            while to_visit:
                current = to_visit.pop(0)
                if current in visited:
                    continue
                
                if current == concept_id:
                    inconsistencies.append(f"Circular is_a relationship detected for concept {concept_id}")
                    break
                
                visited.add(current)
                to_visit.extend(self.get_parent_concepts(current))
        
        # Check for dangling relations
        for relation_id, instances in self._relation_concepts.items():
            for subject_id, object_id in instances:
                if subject_id not in self._concepts:
                    inconsistencies.append(f"Relation {relation_id} references non-existent subject concept {subject_id}")
                if object_id not in self._concepts:
                    inconsistencies.append(f"Relation {relation_id} references non-existent object concept {object_id}")
        
        # Check for dangling properties
        for concept_id, properties in self._concept_properties.items():
            if concept_id not in self._concepts:
                inconsistencies.append(f"Properties reference non-existent concept {concept_id}")
            
            for property_id in properties:
                if property_id not in self._properties:
                    inconsistencies.append(f"Concept {concept_id} references non-existent property {property_id}")
        
        return inconsistencies
    
    def repair_inconsistencies(self) -> int:
        """
        Attempt to repair inconsistencies in the ontology.
        
        Returns:
            int: Number of inconsistencies repaired
        """
        repairs_count = 0
        
        # Remove dangling relations
        for relation_id, instances in list(self._relation_concepts.items()):
            valid_instances = []
            for subject_id, object_id in instances:
                if subject_id in self._concepts and object_id in self._concepts:
                    valid_instances.append((subject_id, object_id))
                else:
                    repairs_count += 1
            
            self._relation_concepts[relation_id] = valid_instances
        
        # Remove dangling properties
        for concept_id in list(self._concept_properties.keys()):
            if concept_id not in self._concepts:
                del self._concept_properties[concept_id]
                repairs_count += 1
                continue
            
            for property_id in list(self._concept_properties[concept_id].keys()):
                if property_id not in self._properties:
                    del self._concept_properties[concept_id][property_id]
                    repairs_count += 1
        
        # Remove circular is_a relationships
        for concept_id in self._concepts:
            visited = set()
            to_visit = list(self.get_parent_concepts(concept_id))
            circular_parents = set()
            
            while to_visit:
                current = to_visit.pop(0)
                if current in visited:
                    continue
                
                if current == concept_id:
                    # Found a circular path
                    for parent in self._is_a_hierarchy[concept_id]:
                        path = self._find_path_to(parent, concept_id, set())
                        if path:
                            circular_parents.add(parent)
                    break
                
                visited.add(current)
                to_visit.extend(self.get_parent_concepts(current))
            
            # Remove circular relationships
            for parent in circular_parents:
                self._is_a_hierarchy[concept_id].remove(parent)
                repairs_count += 1
        
        logger.info(f"Repaired {repairs_count} inconsistencies")
        return repairs_count
    
    def _find_path_to(self, start: str, target: str, visited: Set[str]) -> List[str]:
        """
        Find a path from start to target through the is_a hierarchy.
        
        Args:
            start: Starting concept ID
            target: Target concept ID
            visited: Set of already visited concept IDs
            
        Returns:
            List[str]: Path from start to target, or empty list if no path exists
        """
        if start == target:
            return [start]
        
        if start in visited:
            return []
        
        visited.add(start)
        
        for parent in self.get_parent_concepts(start):
            path = self._find_path_to(parent, target, visited.copy())
            if path:
                return [start] + path
        
        return []
    
    # Integration with KR System
    
    def export_to_kr_system(self) -> Dict[str, Any]:
        """
        Export the ontology to a format suitable for the KR System.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the ontology
        """
        # This is a placeholder for integration with the KR System
        # The actual implementation would depend on the KR System's API
        
        export_data = {
            "concepts": self._concepts,
            "relations": self._relations,
            "properties": self._properties,
            "relation_instances": {
                relation_id: instances
                for relation_id, instances in self._relation_concepts.items()
            },
            "property_instances": {
                concept_id: props
                for concept_id, props in self._concept_properties.items()
            }
        }
        
        return export_data
    
    def import_from_kr_system(self, kr_data: Dict[str, Any]) -> bool:
        """
        Import ontology data from the KR System.
        
        Args:
            kr_data: Dictionary representation of the ontology from the KR System
            
        Returns:
            bool: True if the import was successful, False otherwise
        """
        # This is a placeholder for integration with the KR System
        # The actual implementation would depend on the KR System's API
        
        try:
            # Clear existing data
            self._concepts.clear()
            self._relations.clear()
            self._properties.clear()
            self._concept_relations.clear()
            self._relation_concepts.clear()
            self._concept_properties.clear()
            self._is_a_hierarchy.clear()
            self._has_part_hierarchy.clear()
            
            # Import concepts
            for concept_id, concept_data in kr_data.get("concepts", {}).items():
                self._concepts[concept_id] = concept_data
            
            # Import relations
            for relation_id, relation_data in kr_data.get("relations", {}).items():
                self._relations[relation_id] = relation_data
            
            # Import properties
            for property_id, property_data in kr_data.get("properties", {}).items():
                self._properties[property_id] = property_data
            
            # Import relation instances
            for relation_id, instances in kr_data.get("relation_instances", {}).items():
                self._relation_concepts[relation_id] = instances
                
                for subject_id, object_id in instances:
                    self._concept_relations[subject_id].add(relation_id)
                    
                    # Update taxonomic hierarchies
                    if relation_id == "is_a":
                        self._is_a_hierarchy[subject_id].add(object_id)
                    elif relation_id == "has_part":
                        self._has_part_hierarchy[subject_id].add(object_id)
            
            # Import property instances
            for concept_id, props in kr_data.get("property_instances", {}).items():
                self._concept_properties[concept_id] = props
            
            logger.info("Successfully imported ontology from KR System")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import ontology from KR System: {e}")
            return False