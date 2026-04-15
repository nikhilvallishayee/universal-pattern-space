"""
Abstraction Hierarchy Module (AHM) for GödelOS.

This module provides mechanisms for managing hierarchies of abstractions,
generalizing from specific instances, and finding appropriate levels of
abstraction for different tasks.
"""

from typing import Dict, List, Set, Optional, Any, Tuple, Callable
import logging
from collections import defaultdict
import random

# Setup logging
logger = logging.getLogger(__name__)

class AbstractionHierarchyModule:
    """
    Manages hierarchies of abstractions.
    
    The AbstractionHierarchyModule is responsible for:
    - Managing hierarchies of abstractions
    - Supporting operations for creating, modifying, and navigating abstraction hierarchies
    - Implementing mechanisms for generalizing from specific instances
    - Providing methods for finding appropriate levels of abstraction for different tasks
    - Ensuring consistency across abstraction levels
    """
    
    def __init__(self, ontology_manager):
        """
        Initialize the AbstractionHierarchyModule.
        
        Args:
            ontology_manager: Reference to the OntologyManager
        """
        self._ontology_manager = ontology_manager
        
        # Hierarchies storage
        self._hierarchies = {}  # Dict[str, Dict[str, Any]] - hierarchy_id -> hierarchy data
        
        # Abstraction levels for each hierarchy
        self._abstraction_levels = defaultdict(dict)  # Dict[str, Dict[int, Set[str]]] - hierarchy_id -> {level -> concept_ids}
        
        # Concept abstraction mappings
        self._concept_abstractions = defaultdict(dict)  # Dict[str, Dict[str, Dict[str, Any]]] - hierarchy_id -> {concept_id -> {abstraction_id -> data}}
        
        # Concept specialization mappings
        self._concept_specializations = defaultdict(dict)  # Dict[str, Dict[str, Dict[str, Any]]] - hierarchy_id -> {concept_id -> {specialization_id -> data}}
        
        # Cache for generalization operations
        self._generalization_cache = {}
        
        logger.info("AbstractionHierarchyModule initialized")
    
    # Hierarchy management methods
    
    def create_hierarchy(self, hierarchy_id: str, hierarchy_data: Dict[str, Any]) -> bool:
        """
        Create a new abstraction hierarchy.
        
        Args:
            hierarchy_id: Unique identifier for the hierarchy
            hierarchy_data: Dictionary containing hierarchy information
            
        Returns:
            bool: True if the hierarchy was created successfully, False otherwise
        """
        if hierarchy_id in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} already exists")
            return False
        
        self._hierarchies[hierarchy_id] = hierarchy_data
        logger.info(f"Created hierarchy: {hierarchy_id}")
        return True
    
    def delete_hierarchy(self, hierarchy_id: str) -> bool:
        """
        Delete an abstraction hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy to delete
            
        Returns:
            bool: True if the hierarchy was deleted successfully, False otherwise
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return False
        
        # Remove the hierarchy and its associated data
        del self._hierarchies[hierarchy_id]
        
        if hierarchy_id in self._abstraction_levels:
            del self._abstraction_levels[hierarchy_id]
        
        if hierarchy_id in self._concept_abstractions:
            del self._concept_abstractions[hierarchy_id]
        
        if hierarchy_id in self._concept_specializations:
            del self._concept_specializations[hierarchy_id]
        
        logger.info(f"Deleted hierarchy: {hierarchy_id}")
        return True
    
    def get_hierarchy(self, hierarchy_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an abstraction hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            
        Returns:
            Optional[Dict[str, Any]]: The hierarchy data if found, None otherwise
        """
        return self._hierarchies.get(hierarchy_id)
    
    def get_all_hierarchies(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all abstraction hierarchies.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping hierarchy IDs to hierarchy data
        """
        return self._hierarchies.copy()
    
    # Abstraction level management methods
    
    def add_concept_to_level(self, 
                            hierarchy_id: str, 
                            concept_id: str, 
                            level: int) -> bool:
        """
        Add a concept to a specific abstraction level in a hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            concept_id: Identifier of the concept
            level: Abstraction level (higher is more abstract)
            
        Returns:
            bool: True if the concept was added successfully, False otherwise
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return False
        
        if not self._ontology_manager.get_concept(concept_id):
            logger.warning(f"Concept {concept_id} does not exist")
            return False
        
        # Add the concept to the specified level
        self._abstraction_levels[hierarchy_id].setdefault(level, set()).add(concept_id)
        
        logger.info(f"Added concept {concept_id} to level {level} in hierarchy {hierarchy_id}")
        return True
    
    def remove_concept_from_level(self, 
                                 hierarchy_id: str, 
                                 concept_id: str, 
                                 level: int) -> bool:
        """
        Remove a concept from a specific abstraction level in a hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            concept_id: Identifier of the concept
            level: Abstraction level
            
        Returns:
            bool: True if the concept was removed successfully, False otherwise
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return False
        
        if level not in self._abstraction_levels[hierarchy_id]:
            logger.warning(f"Level {level} does not exist in hierarchy {hierarchy_id}")
            return False
        
        if concept_id not in self._abstraction_levels[hierarchy_id][level]:
            logger.warning(f"Concept {concept_id} is not in level {level} of hierarchy {hierarchy_id}")
            return False
        
        # Remove the concept from the specified level
        self._abstraction_levels[hierarchy_id][level].remove(concept_id)
        
        # If the level is now empty, remove it
        if not self._abstraction_levels[hierarchy_id][level]:
            del self._abstraction_levels[hierarchy_id][level]
        
        logger.info(f"Removed concept {concept_id} from level {level} in hierarchy {hierarchy_id}")
        return True
    
    def get_concepts_at_level(self, 
                             hierarchy_id: str, 
                             level: int) -> Set[str]:
        """
        Get all concepts at a specific abstraction level in a hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            level: Abstraction level
            
        Returns:
            Set[str]: Set of concept IDs at the specified level
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return set()
        
        return self._abstraction_levels[hierarchy_id].get(level, set()).copy()
    
    def get_concept_level(self, 
                         hierarchy_id: str, 
                         concept_id: str) -> Optional[int]:
        """
        Get the abstraction level of a concept in a hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            concept_id: Identifier of the concept
            
        Returns:
            Optional[int]: The abstraction level if found, None otherwise
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return None
        
        for level, concepts in self._abstraction_levels[hierarchy_id].items():
            if concept_id in concepts:
                return level
        
        return None
    
    def get_all_levels(self, hierarchy_id: str) -> List[int]:
        """
        Get all abstraction levels in a hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            
        Returns:
            List[int]: List of abstraction levels, sorted from most specific to most abstract
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return []
        
        levels = list(self._abstraction_levels[hierarchy_id].keys())
        levels.sort()  # Sort from lowest to highest
        return levels
    
    # Abstraction-specialization relationship methods
    
    def add_abstraction_relation(self, 
                                hierarchy_id: str, 
                                specific_id: str, 
                                abstract_id: str,
                                relation_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an abstraction relation between two concepts.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            specific_id: Identifier of the more specific concept
            abstract_id: Identifier of the more abstract concept
            relation_data: Optional data about the abstraction relation
            
        Returns:
            bool: True if the relation was added successfully, False otherwise
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return False
        
        if not self._ontology_manager.get_concept(specific_id):
            logger.warning(f"Concept {specific_id} does not exist")
            return False
        
        if not self._ontology_manager.get_concept(abstract_id):
            logger.warning(f"Concept {abstract_id} does not exist")
            return False
        
        # Get the levels of the concepts
        specific_level = self.get_concept_level(hierarchy_id, specific_id)
        abstract_level = self.get_concept_level(hierarchy_id, abstract_id)
        
        # If levels are not set, assign them
        if specific_level is None and abstract_level is None:
            # Assign default levels
            specific_level = 0
            abstract_level = 1
            self.add_concept_to_level(hierarchy_id, specific_id, specific_level)
            self.add_concept_to_level(hierarchy_id, abstract_id, abstract_level)
        elif specific_level is None:
            # Assign specific level based on abstract level
            specific_level = abstract_level - 1
            self.add_concept_to_level(hierarchy_id, specific_id, specific_level)
        elif abstract_level is None:
            # Assign abstract level based on specific level
            abstract_level = specific_level + 1
            self.add_concept_to_level(hierarchy_id, abstract_id, abstract_level)
        elif specific_level >= abstract_level:
            # Ensure the abstract concept is at a higher level
            logger.warning(f"Invalid abstraction relation: {specific_id} (level {specific_level}) -> {abstract_id} (level {abstract_level})")
            return False
        
        # Add the abstraction relation
        self._concept_abstractions[hierarchy_id].setdefault(specific_id, {})[abstract_id] = relation_data or {}
        
        # Add the specialization relation
        self._concept_specializations[hierarchy_id].setdefault(abstract_id, {})[specific_id] = relation_data or {}
        
        logger.info(f"Added abstraction relation: {specific_id} -> {abstract_id} in hierarchy {hierarchy_id}")
        return True
    
    def remove_abstraction_relation(self, 
                                   hierarchy_id: str, 
                                   specific_id: str, 
                                   abstract_id: str) -> bool:
        """
        Remove an abstraction relation between two concepts.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            specific_id: Identifier of the more specific concept
            abstract_id: Identifier of the more abstract concept
            
        Returns:
            bool: True if the relation was removed successfully, False otherwise
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return False
        
        # Check if the relation exists
        if (specific_id not in self._concept_abstractions[hierarchy_id] or
            abstract_id not in self._concept_abstractions[hierarchy_id][specific_id]):
            logger.warning(f"Abstraction relation {specific_id} -> {abstract_id} does not exist in hierarchy {hierarchy_id}")
            return False
        
        # Remove the abstraction relation
        del self._concept_abstractions[hierarchy_id][specific_id][abstract_id]
        
        # If no more abstractions for this concept, remove the entry
        if not self._concept_abstractions[hierarchy_id][specific_id]:
            del self._concept_abstractions[hierarchy_id][specific_id]
        
        # Remove the specialization relation
        del self._concept_specializations[hierarchy_id][abstract_id][specific_id]
        
        # If no more specializations for this concept, remove the entry
        if not self._concept_specializations[hierarchy_id][abstract_id]:
            del self._concept_specializations[hierarchy_id][abstract_id]
        
        logger.info(f"Removed abstraction relation: {specific_id} -> {abstract_id} in hierarchy {hierarchy_id}")
        return True
    
    # Generalization methods
    
    def generalize_from_instances(self, 
                                 instance_ids: List[str], 
                                 hierarchy_id: Optional[str] = None,
                                 abstraction_level: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Generate an abstraction from a set of instances.
        
        Args:
            instance_ids: List of concept IDs to generalize from
            hierarchy_id: Optional identifier of the hierarchy to use
            abstraction_level: Optional abstraction level for the generalization
            
        Returns:
            Optional[Dict[str, Any]]: The generalized concept data if successful, None otherwise
        """
        if len(instance_ids) < 2:
            logger.warning("At least two instances are required for generalization")
            return None
        
        # Check if all instances exist
        for instance_id in instance_ids:
            if not self._ontology_manager.get_concept(instance_id):
                logger.warning(f"Instance {instance_id} does not exist")
                return None
        
        # Get instance data
        instances = [self._ontology_manager.get_concept(iid) for iid in instance_ids]
        
        # Generate a name for the abstraction
        abstraction_name = self._generate_abstraction_name(instances)
        
        # Create the abstraction concept
        abstraction_id = f"abstraction_{abstraction_name}_{random.randint(1000, 9999)}"
        
        # Extract common properties
        common_properties = self._extract_common_properties(instances)
        
        # Create the abstraction concept data
        abstraction_data = {
            "name": abstraction_name,
            "description": f"Abstraction of {', '.join(i.get('name', iid) for i, iid in zip(instances, instance_ids))}",
            "type": "abstraction",
            "instance_ids": instance_ids,
            "properties": common_properties
        }
        
        # Add the abstraction to the ontology
        if not self._ontology_manager.add_concept(abstraction_id, abstraction_data):
            logger.warning(f"Failed to add abstraction concept {abstraction_id} to ontology")
            return None
        
        # If a hierarchy is specified, add the abstraction to it
        if hierarchy_id:
            if hierarchy_id not in self._hierarchies:
                logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            else:
                # Determine the abstraction level
                if abstraction_level is None:
                    # Get the maximum level of the instances
                    instance_levels = [self.get_concept_level(hierarchy_id, iid) or 0 for iid in instance_ids]
                    abstraction_level = max(instance_levels) + 1
                
                # Add the abstraction to the hierarchy
                self.add_concept_to_level(hierarchy_id, abstraction_id, abstraction_level)
                
                # Add abstraction relations
                for instance_id in instance_ids:
                    self.add_abstraction_relation(hierarchy_id, instance_id, abstraction_id)
        
        logger.info(f"Generated abstraction {abstraction_id} from instances {instance_ids}")
        return abstraction_data
    
    def find_appropriate_abstraction_level(self, 
                                          hierarchy_id: str, 
                                          task_data: Dict[str, Any]) -> Optional[int]:
        """
        Find the appropriate abstraction level for a given task.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            task_data: Data about the task
            
        Returns:
            Optional[int]: The appropriate abstraction level if found, None otherwise
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return None
        
        # Get all levels in the hierarchy
        levels = self.get_all_levels(hierarchy_id)
        if not levels:
            logger.warning(f"No levels found in hierarchy {hierarchy_id}")
            return None
        
        # Determine the appropriate level based on task requirements
        task_type = task_data.get("type")
        
        if task_type == "detailed_analysis":
            # For detailed analysis, use a low abstraction level
            return levels[0]  # Lowest level
        elif task_type == "high_level_overview":
            # For high-level overview, use a high abstraction level
            return levels[-1]  # Highest level
        
        # Default: use the middle level
        return levels[len(levels) // 2]
    
    # Helper methods
    
    def _generate_abstraction_name(self, instances: List[Dict[str, Any]]) -> str:
        """Generate a name for an abstraction based on its instances."""
        # Simple implementation: combine parts of instance names
        name_parts = []
        for instance in instances:
            if "name" in instance:
                # Take the first part of the name (up to 3 characters)
                name_parts.append(instance["name"][:3])
        
        if name_parts:
            return "Abs_" + "_".join(name_parts)
        else:
            return f"Abstraction_{random.randint(1000, 9999)}"
    
    def _extract_common_properties(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract properties common to all instances."""
        if not instances:
            return {}
        
        # Get properties from the first instance
        common_properties = {}
        if "properties" in instances[0]:
            common_properties = instances[0]["properties"].copy()
        
        # Intersect with properties from other instances
        for instance in instances[1:]:
            instance_properties = instance.get("properties", {})
            
            # Keep only properties that exist in both and have the same value
            for prop_id in list(common_properties.keys()):
                if prop_id not in instance_properties or instance_properties[prop_id] != common_properties[prop_id]:
                    del common_properties[prop_id]
        
        return common_properties
        
    def get_abstractions(self,
                        hierarchy_id: str,
                        concept_id: str) -> Set[str]:
        """
        Get the direct abstractions of a concept in a hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of concept IDs that are direct abstractions of the given concept
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return set()
        
        if concept_id not in self._concept_abstractions.get(hierarchy_id, {}):
            return set()
        
        return set(self._concept_abstractions[hierarchy_id][concept_id].keys())
    
    def get_specializations(self,
                           hierarchy_id: str,
                           concept_id: str) -> Set[str]:
        """
        Get the direct specializations of a concept in a hierarchy.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of concept IDs that are direct specializations of the given concept
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return set()
        
        if concept_id not in self._concept_specializations.get(hierarchy_id, {}):
            return set()
        
        return set(self._concept_specializations[hierarchy_id][concept_id].keys())
    
    def get_all_abstractions(self,
                            hierarchy_id: str,
                            concept_id: str) -> Set[str]:
        """
        Get all abstractions of a concept in a hierarchy, including indirect ones.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of concept IDs that are abstractions of the given concept (direct or indirect)
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return set()
        
        # Get direct abstractions
        direct_abstractions = self.get_abstractions(hierarchy_id, concept_id)
        all_abstractions = set(direct_abstractions)
        
        # Recursively get abstractions of abstractions
        for abstraction_id in direct_abstractions:
            higher_abstractions = self.get_all_abstractions(hierarchy_id, abstraction_id)
            all_abstractions.update(higher_abstractions)
        
        return all_abstractions
    
    def get_all_specializations(self,
                               hierarchy_id: str,
                               concept_id: str) -> Set[str]:
        """
        Get all specializations of a concept in a hierarchy, including indirect ones.
        
        Args:
            hierarchy_id: Identifier of the hierarchy
            concept_id: Identifier of the concept
            
        Returns:
            Set[str]: Set of concept IDs that are specializations of the given concept (direct or indirect)
        """
        if hierarchy_id not in self._hierarchies:
            logger.warning(f"Hierarchy {hierarchy_id} does not exist")
            return set()
        
        # Get direct specializations
        direct_specializations = self.get_specializations(hierarchy_id, concept_id)
        all_specializations = set(direct_specializations)
        
        # Recursively get specializations of specializations
        for specialization_id in direct_specializations:
            lower_specializations = self.get_all_specializations(hierarchy_id, specialization_id)
            all_specializations.update(lower_specializations)
        
        return all_specializations

    # Consistency checking methods

    def check_hierarchy_consistency(self, hierarchy_id: str) -> List[Dict[str, Any]]:
        """
        Check the consistency of an abstraction hierarchy.

        Verifies that:
        - All referenced concepts exist in the ontology.
        - Abstraction relations satisfy level ordering (specific < abstract).

        Args:
            hierarchy_id: Identifier of the hierarchy.

        Returns:
            A list of inconsistency descriptions.  Empty list means consistent.
        """
        inconsistencies: List[Dict[str, Any]] = []

        if hierarchy_id not in self._hierarchies:
            inconsistencies.append({
                "type": "missing_hierarchy",
                "message": f"Hierarchy {hierarchy_id} does not exist",
            })
            return inconsistencies

        # Check concept existence (cache once to avoid repeated copies)
        all_concepts = self._ontology_manager.get_all_concepts()
        for level, concept_ids in self._abstraction_levels.get(hierarchy_id, {}).items():
            for cid in concept_ids:
                if cid not in all_concepts:
                    inconsistencies.append({
                        "type": "missing_concept",
                        "concept_id": cid,
                        "level": level,
                        "message": f"Concept {cid} at level {level} not found in ontology",
                    })

        # Check level ordering of abstraction relations
        abstractions = self._concept_abstractions.get(hierarchy_id, {})
        for specific_id, abstract_map in abstractions.items():
            specific_level = self.get_concept_level(hierarchy_id, specific_id)
            for abstract_id in abstract_map:
                abstract_level = self.get_concept_level(hierarchy_id, abstract_id)
                if specific_level is not None and abstract_level is not None:
                    if specific_level >= abstract_level:
                        inconsistencies.append({
                            "type": "level_ordering",
                            "specific": specific_id,
                            "abstract": abstract_id,
                            "specific_level": specific_level,
                            "abstract_level": abstract_level,
                            "message": (
                                f"Specific concept {specific_id} (level {specific_level}) "
                                f"must be below abstract concept {abstract_id} (level {abstract_level})"
                            ),
                        })

        return inconsistencies

    def repair_hierarchy_consistency(self, hierarchy_id: str) -> int:
        """
        Attempt to repair inconsistencies in a hierarchy.

        Returns:
            Number of repairs performed.
        """
        repairs = 0
        inconsistencies = self.check_hierarchy_consistency(hierarchy_id)
        for issue in inconsistencies:
            if issue["type"] == "missing_concept":
                cid = issue["concept_id"]
                level = issue["level"]
                self.remove_concept_from_level(hierarchy_id, cid, level)
                repairs += 1
        return repairs