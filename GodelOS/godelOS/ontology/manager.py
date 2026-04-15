"""
Ontology Creativity Manager for GödelOS.

This module provides the central manager for the Ontological Creativity & Abstraction System,
coordinating the different components and providing a unified API.
"""

from typing import Dict, List, Set, Optional, Any, Tuple, Callable
import logging
import json
import os

from godelOS.ontology.ontology_manager import OntologyManager
from godelOS.ontology.conceptual_blender import ConceptualBlender
from godelOS.ontology.hypothesis_generator import HypothesisGenerator
from godelOS.ontology.abstraction_hierarchy import AbstractionHierarchyModule

# Setup logging
logger = logging.getLogger(__name__)

class OntologyCreativityManager:
    """
    Central manager for the Ontological Creativity & Abstraction System.
    
    The OntologyCreativityManager is responsible for:
    - Coordinating the different ontological creativity components
    - Providing a unified API for the rest of GödelOS to interact with
    - Managing configuration of the ontological creativity components
    - Handling initialization and shutdown of components
    - Implementing workflows for concept creation, hypothesis generation, and abstraction management
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the OntologyCreativityManager.
        
        Args:
            config_path: Optional path to a configuration file
        """
        # Load configuration
        self._config = self._load_config(config_path)
        
        # Initialize components
        self._ontology_manager = OntologyManager()
        self._conceptual_blender = ConceptualBlender(self._ontology_manager)
        self._hypothesis_generator = HypothesisGenerator(self._ontology_manager)
        self._abstraction_hierarchy = AbstractionHierarchyModule(self._ontology_manager)
        
        # Component registry
        self._components = {
            "ontology_manager": self._ontology_manager,
            "conceptual_blender": self._conceptual_blender,
            "hypothesis_generator": self._hypothesis_generator,
            "abstraction_hierarchy": self._abstraction_hierarchy
        }
        
        # Workflow registry
        self._workflows = {
            "concept_creation": self._workflow_concept_creation,
            "hypothesis_generation": self._workflow_hypothesis_generation,
            "abstraction_management": self._workflow_abstraction_management
        }
        
        logger.info("OntologyCreativityManager initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from a file or use default configuration.
        
        Args:
            config_path: Path to a configuration file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        default_config = {
            "ontology_manager": {
                "consistency_check_interval": 100  # Check consistency every 100 operations
            },
            "conceptual_blender": {
                "default_strategy": "property_merge",
                "cache_size": 1000  # Maximum number of cached blends
            },
            "hypothesis_generator": {
                "default_strategy": "abductive",
                "max_hypotheses": 10  # Maximum number of hypotheses to generate
            },
            "abstraction_hierarchy": {
                "default_hierarchy": "main",
                "auto_generalize": True  # Automatically generalize from instances
            },
            "workflows": {
                "concept_creation": {
                    "enabled": True,
                    "auto_evaluate": True  # Automatically evaluate created concepts
                },
                "hypothesis_generation": {
                    "enabled": True,
                    "auto_test": False  # Don't automatically test hypotheses
                },
                "abstraction_management": {
                    "enabled": True,
                    "consistency_check": True  # Check consistency of abstraction hierarchies
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Merge user configuration with default configuration
                self._merge_configs(default_config, user_config)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load configuration from {config_path}: {e}")
                logger.info("Using default configuration")
        else:
            logger.info("Using default configuration")
        
        return default_config
    
    def _merge_configs(self, default_config: Dict[str, Any], user_config: Dict[str, Any]) -> None:
        """
        Merge user configuration into default configuration.
        
        Args:
            default_config: Default configuration dictionary
            user_config: User configuration dictionary
        """
        for key, value in user_config.items():
            if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                self._merge_configs(default_config[key], value)
            else:
                default_config[key] = value
    
    # Component access methods
    
    def get_component(self, component_name: str) -> Any:
        """
        Get a specific component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Any: The component if found, None otherwise
        """
        return self._components.get(component_name)
    
    def get_ontology_manager(self) -> OntologyManager:
        """
        Get the OntologyManager component.
        
        Returns:
            OntologyManager: The OntologyManager component
        """
        return self._ontology_manager
    
    def get_conceptual_blender(self) -> ConceptualBlender:
        """
        Get the ConceptualBlender component.
        
        Returns:
            ConceptualBlender: The ConceptualBlender component
        """
        return self._conceptual_blender
    
    def get_hypothesis_generator(self) -> HypothesisGenerator:
        """
        Get the HypothesisGenerator component.
        
        Returns:
            HypothesisGenerator: The HypothesisGenerator component
        """
        return self._hypothesis_generator
    
    def get_abstraction_hierarchy(self) -> AbstractionHierarchyModule:
        """
        Get the AbstractionHierarchyModule component.
        
        Returns:
            AbstractionHierarchyModule: The AbstractionHierarchyModule component
        """
        return self._abstraction_hierarchy
    
    # Configuration methods
    
    def get_config(self, component: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific component or the entire system.
        
        Args:
            component: Optional name of the component
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if component:
            return self._config.get(component, {})
        else:
            return self._config
    
    def update_config(self, component: str, config_updates: Dict[str, Any]) -> bool:
        """
        Update configuration for a specific component.
        
        Args:
            component: Name of the component
            config_updates: Dictionary of configuration updates
            
        Returns:
            bool: True if the configuration was updated successfully, False otherwise
        """
        if component not in self._config:
            logger.warning(f"Component {component} not found in configuration")
            return False
        
        # Update the configuration
        self._merge_configs(self._config[component], config_updates)
        logger.info(f"Updated configuration for {component}")
        return True
    
    # Workflow methods
    
    def execute_workflow(self, 
                        workflow_name: str, 
                        workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific workflow.
        
        Args:
            workflow_name: Name of the workflow
            workflow_data: Data for the workflow
            
        Returns:
            Dict[str, Any]: Workflow results
        """
        if workflow_name not in self._workflows:
            logger.warning(f"Workflow {workflow_name} not found")
            return {"success": False, "error": f"Workflow {workflow_name} not found"}
        
        # Check if the workflow is enabled
        if not self._config.get("workflows", {}).get(workflow_name, {}).get("enabled", True):
            logger.warning(f"Workflow {workflow_name} is disabled")
            return {"success": False, "error": f"Workflow {workflow_name} is disabled"}
        
        # Execute the workflow
        try:
            result = self._workflows[workflow_name](workflow_data)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def _workflow_concept_creation(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the concept creation workflow.
        
        Args:
            workflow_data: Data for the workflow
            
        Returns:
            Dict[str, Any]: Workflow results
        """
        # Extract workflow parameters
        concept_type = workflow_data.get("concept_type", "blend")
        
        if concept_type == "blend":
            # Create a concept by blending
            source_concepts = workflow_data.get("source_concepts", [])
            strategy = workflow_data.get("strategy", self._config["conceptual_blender"]["default_strategy"])
            constraints = workflow_data.get("constraints", {})
            
            # Blend the concepts
            blended_concept = self._conceptual_blender.blend_concepts(source_concepts, strategy, constraints)
            
            if not blended_concept:
                return {"status": "error", "message": "Failed to blend concepts"}
            
            # Generate a concept ID
            concept_id = workflow_data.get("concept_id", f"blend_{strategy}_{len(source_concepts)}")
            
            # Add the concept to the ontology
            if not self._ontology_manager.add_concept(concept_id, blended_concept):
                return {"status": "error", "message": f"Failed to add concept {concept_id} to ontology"}
            
            # Evaluate the concept if auto_evaluate is enabled
            if self._config["workflows"]["concept_creation"]["auto_evaluate"]:
                utility = self._conceptual_blender.evaluate_concept_utility(blended_concept)
                novelty = self._conceptual_blender.detect_novelty(blended_concept)
                
                return {
                    "status": "success",
                    "concept_id": concept_id,
                    "concept_data": blended_concept,
                    "evaluation": {
                        "utility": utility,
                        "novelty": novelty
                    }
                }
            else:
                return {
                    "status": "success",
                    "concept_id": concept_id,
                    "concept_data": blended_concept
                }
        
        elif concept_type == "novel":
            # Create a novel concept
            seed_concepts = workflow_data.get("seed_concepts", [])
            novelty_threshold = workflow_data.get("novelty_threshold", 0.5)
            
            # Generate a novel concept
            novel_concept = self._conceptual_blender.generate_novel_concept(seed_concepts, novelty_threshold)
            
            if not novel_concept:
                return {"status": "error", "message": "Failed to generate novel concept"}
            
            # Generate a concept ID
            concept_id = workflow_data.get("concept_id", f"novel_{len(seed_concepts)}")
            
            # Add the concept to the ontology
            if not self._ontology_manager.add_concept(concept_id, novel_concept):
                return {"status": "error", "message": f"Failed to add concept {concept_id} to ontology"}
            
            return {
                "status": "success",
                "concept_id": concept_id,
                "concept_data": novel_concept,
                "novelty_score": novel_concept.get("novelty_score", 0.0)
            }
        
        else:
            return {"status": "error", "message": f"Unknown concept type: {concept_type}"}
    
    def _workflow_hypothesis_generation(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the hypothesis generation workflow.
        
        Args:
            workflow_data: Data for the workflow
            
        Returns:
            Dict[str, Any]: Workflow results
        """
        # Extract workflow parameters
        observations = workflow_data.get("observations", [])
        context = workflow_data.get("context", {})
        strategy = workflow_data.get("strategy", self._config["hypothesis_generator"]["default_strategy"])
        constraints = workflow_data.get("constraints", {})
        max_hypotheses = workflow_data.get("max_hypotheses", self._config["hypothesis_generator"]["max_hypotheses"])
        
        # Generate hypotheses
        hypotheses = self._hypothesis_generator.generate_hypotheses(
            observations, context, strategy, constraints, max_hypotheses
        )
        
        if not hypotheses:
            return {"status": "error", "message": "Failed to generate hypotheses"}
        
        # Test hypotheses if auto_test is enabled and new_observations are provided
        if (self._config["workflows"]["hypothesis_generation"]["auto_test"] and
            "new_observations" in workflow_data):
            
            new_observations = workflow_data["new_observations"]
            test_results = []
            
            for hypothesis in hypotheses:
                result = self._hypothesis_generator.test_hypothesis(hypothesis, new_observations)
                test_results.append({
                    "hypothesis": hypothesis,
                    "test_result": result
                })
            
            return {
                "status": "success",
                "hypotheses": hypotheses,
                "test_results": test_results
            }
        else:
            return {
                "status": "success",
                "hypotheses": hypotheses
            }
    
    def _workflow_abstraction_management(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the abstraction management workflow.
        
        Args:
            workflow_data: Data for the workflow
            
        Returns:
            Dict[str, Any]: Workflow results
        """
        # Extract workflow parameters
        operation = workflow_data.get("operation")
        
        if not operation:
            return {"status": "error", "message": "No operation specified"}
        
        if operation == "create_hierarchy":
            # Create a new abstraction hierarchy
            hierarchy_id = workflow_data.get("hierarchy_id")
            hierarchy_data = workflow_data.get("hierarchy_data", {})
            
            if not hierarchy_id:
                return {"status": "error", "message": "No hierarchy_id specified"}
            
            if not self._abstraction_hierarchy.create_hierarchy(hierarchy_id, hierarchy_data):
                return {"status": "error", "message": f"Failed to create hierarchy {hierarchy_id}"}
            
            return {
                "status": "success",
                "hierarchy_id": hierarchy_id,
                "message": f"Created hierarchy {hierarchy_id}"
            }
        
        elif operation == "generalize":
            # Generalize from instances
            instance_ids = workflow_data.get("instance_ids", [])
            hierarchy_id = workflow_data.get("hierarchy_id", self._config["abstraction_hierarchy"]["default_hierarchy"])
            abstraction_level = workflow_data.get("abstraction_level")
            
            if not instance_ids:
                return {"status": "error", "message": "No instance_ids specified"}
            
            # Generalize from instances
            abstraction_data = self._abstraction_hierarchy.generalize_from_instances(
                instance_ids, hierarchy_id, abstraction_level
            )
            
            if not abstraction_data:
                return {"status": "error", "message": "Failed to generalize from instances"}
            
            return {
                "status": "success",
                "abstraction_data": abstraction_data,
                "message": f"Generated abstraction from {len(instance_ids)} instances"
            }
        
        elif operation == "find_level":
            # Find appropriate abstraction level for a task
            hierarchy_id = workflow_data.get("hierarchy_id", self._config["abstraction_hierarchy"]["default_hierarchy"])
            task_data = workflow_data.get("task_data", {})
            
            if not task_data:
                return {"status": "error", "message": "No task_data specified"}
            
            # Find appropriate level
            level = self._abstraction_hierarchy.find_appropriate_abstraction_level(hierarchy_id, task_data)
            
            if level is None:
                return {"status": "error", "message": f"Failed to find appropriate level for task in hierarchy {hierarchy_id}"}
            
            # Get concepts at the level
            concepts = self._abstraction_hierarchy.get_concepts_at_level(hierarchy_id, level)
            
            return {
                "status": "success",
                "level": level,
                "concepts": list(concepts),
                "message": f"Found appropriate level {level} with {len(concepts)} concepts"
            }
        
        elif operation == "check_consistency":
            # Check consistency of abstraction hierarchies
            hierarchy_id = workflow_data.get("hierarchy_id")
            
            if hierarchy_id:
                # Check a specific hierarchy
                inconsistencies = self._abstraction_hierarchy.check_hierarchy_consistency(hierarchy_id)
                
                if inconsistencies:
                    # Try to repair if consistency_check is enabled
                    if self._config["workflows"]["abstraction_management"]["consistency_check"]:
                        repairs = self._abstraction_hierarchy.repair_hierarchy_consistency(hierarchy_id)
                        
                        return {
                            "status": "warning",
                            "hierarchy_id": hierarchy_id,
                            "inconsistencies": inconsistencies,
                            "repairs": repairs,
                            "message": f"Found and repaired {repairs} inconsistencies in hierarchy {hierarchy_id}"
                        }
                    else:
                        return {
                            "status": "warning",
                            "hierarchy_id": hierarchy_id,
                            "inconsistencies": inconsistencies,
                            "message": f"Found {len(inconsistencies)} inconsistencies in hierarchy {hierarchy_id}"
                        }
                else:
                    return {
                        "status": "success",
                        "hierarchy_id": hierarchy_id,
                        "message": f"Hierarchy {hierarchy_id} is consistent"
                    }
            else:
                # Check all hierarchies
                all_inconsistencies = {}
                all_repairs = {}
                
                for h_id in self._abstraction_hierarchy.get_all_hierarchies():
                    inconsistencies = self._abstraction_hierarchy.check_hierarchy_consistency(h_id)
                    
                    if inconsistencies:
                        all_inconsistencies[h_id] = inconsistencies
                        
                        # Try to repair if consistency_check is enabled
                        if self._config["workflows"]["abstraction_management"]["consistency_check"]:
                            repairs = self._abstraction_hierarchy.repair_hierarchy_consistency(h_id)
                            all_repairs[h_id] = repairs
                
                if all_inconsistencies:
                    if self._config["workflows"]["abstraction_management"]["consistency_check"]:
                        return {
                            "status": "warning",
                            "inconsistencies": all_inconsistencies,
                            "repairs": all_repairs,
                            "message": f"Found and repaired inconsistencies in {len(all_inconsistencies)} hierarchies"
                        }
                    else:
                        return {
                            "status": "warning",
                            "inconsistencies": all_inconsistencies,
                            "message": f"Found inconsistencies in {len(all_inconsistencies)} hierarchies"
                        }
                else:
                    return {
                        "status": "success",
                        "message": "All hierarchies are consistent"
                    }
        
        else:
            return {"status": "error", "message": f"Unknown operation: {operation}"}
    
    # Lifecycle methods
    
    def initialize(self) -> bool:
        """
        Initialize the Ontological Creativity & Abstraction System.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        logger.info("Initializing Ontological Creativity & Abstraction System")
        
        # Initialize components
        # (Currently no additional initialization is needed)
        
        # Create default hierarchy if auto_generalize is enabled
        if self._config["abstraction_hierarchy"]["auto_generalize"]:
            default_hierarchy = self._config["abstraction_hierarchy"]["default_hierarchy"]
            
            if default_hierarchy not in self._abstraction_hierarchy.get_all_hierarchies():
                self._abstraction_hierarchy.create_hierarchy(default_hierarchy, {
                    "name": "Default Hierarchy",
                    "description": "Default abstraction hierarchy"
                })
                logger.info(f"Created default hierarchy: {default_hierarchy}")
        
        logger.info("Ontological Creativity & Abstraction System initialized")
        return True
    
    def shutdown(self) -> bool:
        """
        Shut down the Ontological Creativity & Abstraction System.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        logger.info("Shutting down Ontological Creativity & Abstraction System")
        
        # Perform any necessary cleanup
        # (Currently no additional cleanup is needed)
        
        logger.info("Ontological Creativity & Abstraction System shut down")
        return True