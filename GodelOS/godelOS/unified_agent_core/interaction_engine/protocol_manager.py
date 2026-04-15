"""
Protocol Manager Implementation for GodelOS

This module implements the ProtocolManager class, which is responsible for
managing communication protocols for different types of interactions in the system.
It supports dynamic protocol registration, version compatibility checking,
protocol transformation, validation with detailed error reporting, and
protocol optimization based on interaction patterns.
"""

import logging
import asyncio
import time
from typing import Dict, Optional, Any, List, Tuple, Set, Callable
import json
import jsonschema
import re
import copy
from collections import defaultdict, Counter

from godelOS.unified_agent_core.interaction_engine.interfaces import (
    Protocol, Interaction, InteractionType, InteractionStatus, ProtocolManagerInterface
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when an interaction fails validation against its protocol."""
    pass


class ProtocolCompatibilityError(Exception):
    """Exception raised when protocols are incompatible."""
    pass


class ProtocolTransformationError(Exception):
    """Exception raised when protocol transformation fails."""
    pass


class ProtocolManager(ProtocolManagerInterface):
    """
    ProtocolManager implementation for GodelOS.
    
    The ProtocolManager is responsible for managing communication protocols for
    different types of interactions in the system. It supports dynamic protocol
    registration, version compatibility checking, protocol transformation,
    validation with detailed error reporting, and protocol optimization based
    on interaction patterns.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the protocol manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize protocol registries
        self.protocols: Dict[InteractionType, Protocol] = {}
        self.protocol_versions: Dict[str, Dict[str, Protocol]] = {}  # name -> version -> protocol
        
        # Initialize protocol compatibility registry
        self.compatible_versions: Dict[str, Dict[str, Set[str]]] = {}  # name -> version -> compatible versions
        
        # Initialize protocol transformers
        self.protocol_transformers: Dict[Tuple[str, str], Callable] = {}  # (from_proto, to_proto) -> transformer
        
        # Initialize interaction pattern tracking
        self.interaction_patterns: Dict[str, Counter] = defaultdict(Counter)  # protocol_name -> pattern counter
        self.pattern_timestamps: Dict[str, Dict[str, float]] = defaultdict(dict)  # protocol_name -> pattern -> timestamp
        
        # Initialize validation error patterns
        self.validation_errors: Counter = Counter()
        
        # Initialize lock
        self.lock = asyncio.Lock()
    
    async def register_protocol(self, protocol: Protocol) -> bool:
        """
        Register a communication protocol.
        
        Args:
            protocol: The protocol to register
            
        Returns:
            True if the protocol was registered successfully, False otherwise
        """
        if not protocol.name:
            logger.error("Cannot register protocol with empty name")
            return False
        
        if not protocol.version:
            logger.error("Cannot register protocol with empty version")
            return False
        
        async with self.lock:
            # Register by interaction type
            self.protocols[protocol.interaction_type] = protocol
            
            # Register by name and version
            if protocol.name not in self.protocol_versions:
                self.protocol_versions[protocol.name] = {}
                self.compatible_versions[protocol.name] = {}
            
            self.protocol_versions[protocol.name][protocol.version] = protocol
            
            # Initialize compatibility for this version
            if protocol.version not in self.compatible_versions[protocol.name]:
                self.compatible_versions[protocol.name][protocol.version] = set()
            
            # Self-compatibility
            self.compatible_versions[protocol.name][protocol.version].add(protocol.version)
            
            # Check for declared compatible versions in metadata
            if "compatible_versions" in protocol.metadata:
                compatible_versions = protocol.metadata["compatible_versions"]
                if isinstance(compatible_versions, list):
                    for version in compatible_versions:
                        if version in self.protocol_versions[protocol.name]:
                            # Add bidirectional compatibility
                            self.compatible_versions[protocol.name][protocol.version].add(version)
                            self.compatible_versions[protocol.name][version].add(protocol.version)
            
            logger.info(f"Registered protocol {protocol.name} v{protocol.version} for {protocol.interaction_type.value}")
            return True
    
    async def get_protocol(self, interaction_type: InteractionType) -> Optional[Protocol]:
        """
        Get a protocol for an interaction type.
        
        Args:
            interaction_type: The interaction type
            
        Returns:
            The protocol, or None if no protocol is registered for the interaction type
        """
        async with self.lock:
            protocol = self.protocols.get(interaction_type)
            
            # If protocol exists and optimization is enabled, check for optimized version
            if protocol and self.config.get("enable_protocol_optimization", True):
                optimized_protocol = await self._get_optimized_protocol(protocol)
                if optimized_protocol:
                    return optimized_protocol
            
            return protocol
    
    async def get_protocol_by_name_version(self, name: str, version: str) -> Optional[Protocol]:
        """
        Get a protocol by name and version.
        
        Args:
            name: The protocol name
            version: The protocol version
            
        Returns:
            The protocol, or None if not found
        """
        async with self.lock:
            versions = self.protocol_versions.get(name, {})
            return versions.get(version)
    
    async def validate(self, interaction: Interaction) -> Interaction:
        """
        Validate an interaction against its protocol.
        
        Args:
            interaction: The interaction to validate
            
        Returns:
            The validated interaction
        
        Raises:
            ValidationError: If the interaction is invalid
        """
        # Get protocol for interaction type
        protocol = await self.get_protocol(interaction.type)
        
        if not protocol:
            # If no protocol is registered, consider the interaction valid
            logger.warning(f"No protocol registered for interaction type {interaction.type.value}")
            return interaction
        
        # Check if interaction has a specific protocol version in metadata
        if "protocol_name" in interaction.metadata and "protocol_version" in interaction.metadata:
            protocol_name = interaction.metadata["protocol_name"]
            protocol_version = interaction.metadata["protocol_version"]
            
            specific_protocol = await self.get_protocol_by_name_version(protocol_name, protocol_version)
            
            if specific_protocol:
                protocol = specific_protocol
                
                # Track interaction pattern for this protocol
                await self._track_interaction_pattern(protocol_name, interaction)
            else:
                # Try to find a compatible protocol version
                compatible_protocol = await self._find_compatible_protocol(
                    protocol_name, protocol_version
                )
                
                if compatible_protocol:
                    logger.info(
                        f"Using compatible protocol {protocol_name} v{compatible_protocol.version} "
                        f"instead of requested v{protocol_version}"
                    )
                    protocol = compatible_protocol
                    
                    # Update interaction metadata with actual protocol version
                    interaction.metadata["actual_protocol_version"] = compatible_protocol.version
                    interaction.metadata["protocol_compatibility"] = "version_compatible"
                else:
                    # Try to transform the interaction to match the current protocol
                    try:
                        transformed_interaction = await self._transform_interaction(
                            interaction, protocol_name, protocol_version, protocol.name, protocol.version
                        )
                        interaction = transformed_interaction
                        interaction.metadata["protocol_transformation"] = "transformed"
                    except ProtocolTransformationError:
                        # Continue with original interaction and protocol
                        pass
        
        # Validate against protocol schema
        try:
            # Convert interaction content to a format that can be validated against the schema
            content_to_validate = interaction.content
            
            # Validate against schema
            jsonschema.validate(instance=content_to_validate, schema=protocol.schema)
            
            # Store protocol info in interaction metadata
            interaction.metadata["validated_protocol"] = protocol.name
            interaction.metadata["validated_protocol_version"] = protocol.version
            
            return interaction
        except jsonschema.exceptions.ValidationError as e:
            # Track validation error
            error_path = ".".join([str(path) for path in e.path]) if e.path else "root"
            error_key = f"{protocol.name}:{error_path}"
            
            async with self.lock:
                self.validation_errors[error_key] += 1
            
            # Create detailed error report
            error_details = self._create_validation_error_details(e, protocol, content_to_validate)
            
            error_message = (
                f"Interaction {interaction.id} failed validation against protocol {protocol.name}: {str(e)}\n"
                f"Error details: {json.dumps(error_details, indent=2)}"
            )
            
            logger.error(error_message)
            
            # Create ValidationError with detailed information
            validation_error = ValidationError(error_message)
            validation_error.details = error_details
            validation_error.protocol = protocol.name
            validation_error.protocol_version = protocol.version
            
            raise validation_error
    
    async def get_protocol_schema(self, protocol_name: str, protocol_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a protocol.
        
        Args:
            protocol_name: The protocol name
            protocol_version: Optional protocol version (latest if not specified)
            
        Returns:
            The protocol schema, or None if not found
        """
        async with self.lock:
            versions = self.protocol_versions.get(protocol_name, {})
            
            if not versions:
                return None
            
            if protocol_version:
                # Get specific version
                protocol = versions.get(protocol_version)
                return protocol.schema if protocol else None
            else:
                # Get latest version
                latest_version = max(versions.keys())
                return versions[latest_version].schema
    
    async def list_protocols(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered protocols.
        
        Returns:
            Dictionary mapping protocol names to information about available versions
        """
        async with self.lock:
            result = {}
            
            for name, versions in self.protocol_versions.items():
                result[name] = {
                    "versions": list(versions.keys()),
                    "interaction_types": [
                        protocol.interaction_type.value
                        for protocol in versions.values()
                    ]
                }
            
            return result
    
    async def register_protocol_compatibility(self, protocol_name: str, version1: str, version2: str) -> bool:
        """
        Register compatibility between two protocol versions.
        
        Args:
            protocol_name: The protocol name
            version1: First version
            version2: Second version
            
        Returns:
            True if compatibility was registered successfully, False otherwise
        """
        async with self.lock:
            if protocol_name not in self.protocol_versions:
                logger.error(f"Protocol {protocol_name} not registered")
                return False
            
            if version1 not in self.protocol_versions[protocol_name]:
                logger.error(f"Protocol {protocol_name} v{version1} not registered")
                return False
            
            if version2 not in self.protocol_versions[protocol_name]:
                logger.error(f"Protocol {protocol_name} v{version2} not registered")
                return False
            
            # Initialize compatibility sets if needed
            if version1 not in self.compatible_versions[protocol_name]:
                self.compatible_versions[protocol_name][version1] = set()
            
            if version2 not in self.compatible_versions[protocol_name]:
                self.compatible_versions[protocol_name][version2] = set()
            
            # Register bidirectional compatibility
            self.compatible_versions[protocol_name][version1].add(version2)
            self.compatible_versions[protocol_name][version2].add(version1)
            
            logger.info(f"Registered compatibility between {protocol_name} v{version1} and v{version2}")
            return True
    
    async def register_protocol_transformer(
        self, from_protocol: str, from_version: str, to_protocol: str, to_version: str, 
        transformer: Callable[[Interaction], Interaction]
    ) -> bool:
        """
        Register a transformer function between protocols.
        
        Args:
            from_protocol: Source protocol name
            from_version: Source protocol version
            to_protocol: Target protocol name
            to_version: Target protocol version
            transformer: Function to transform interactions
            
        Returns:
            True if transformer was registered successfully, False otherwise
        """
        async with self.lock:
            # Check if source protocol exists
            if from_protocol not in self.protocol_versions:
                logger.error(f"Source protocol {from_protocol} not registered")
                return False
            
            if from_version not in self.protocol_versions[from_protocol]:
                logger.error(f"Source protocol {from_protocol} v{from_version} not registered")
                return False
            
            # Check if target protocol exists
            if to_protocol not in self.protocol_versions:
                logger.error(f"Target protocol {to_protocol} not registered")
                return False
            
            if to_version not in self.protocol_versions[to_protocol]:
                logger.error(f"Target protocol {to_protocol} v{to_version} not registered")
                return False
            
            # Register transformer
            key = (f"{from_protocol}:{from_version}", f"{to_protocol}:{to_version}")
            self.protocol_transformers[key] = transformer
            
            logger.info(
                f"Registered transformer from {from_protocol} v{from_version} "
                f"to {to_protocol} v{to_version}"
            )
            return True
    
    async def check_protocol_compatibility(
        self, protocol_name: str, version1: str, version2: str
    ) -> Dict[str, Any]:
        """
        Check compatibility between two protocol versions.
        
        Args:
            protocol_name: The protocol name
            version1: First version
            version2: Second version
            
        Returns:
            Dictionary with compatibility information
        """
        async with self.lock:
            if protocol_name not in self.protocol_versions:
                return {"compatible": False, "error": f"Protocol {protocol_name} not registered"}
            
            if version1 not in self.protocol_versions[protocol_name]:
                return {"compatible": False, "error": f"Protocol {protocol_name} v{version1} not registered"}
            
            if version2 not in self.protocol_versions[protocol_name]:
                return {"compatible": False, "error": f"Protocol {protocol_name} v{version2} not registered"}
            
            # Check if versions are explicitly marked as compatible
            if (version1 in self.compatible_versions[protocol_name] and 
                version2 in self.compatible_versions[protocol_name][version1]):
                return {"compatible": True, "type": "explicit"}
            
            # Get protocols
            protocol1 = self.protocol_versions[protocol_name][version1]
            protocol2 = self.protocol_versions[protocol_name][version2]
            
            # Compare schemas
            schema1 = protocol1.schema
            schema2 = protocol2.schema
            
            # Check if schemas are identical
            if schema1 == schema2:
                return {"compatible": True, "type": "identical_schema"}
            
            # Check if schemas are compatible (basic check)
            required1 = set(schema1.get("required", []))
            required2 = set(schema2.get("required", []))
            
            # If schema2 requires properties not in schema1, they're incompatible
            if not required2.issubset(required1):
                missing_properties = required2 - required1
                return {
                    "compatible": False, 
                    "error": f"Version {version2} requires properties not in {version1}: {missing_properties}"
                }
            
            # If schemas have compatible required properties, consider them compatible
            return {"compatible": True, "type": "compatible_schema"}
    
    async def get_validation_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about validation errors.
        
        Returns:
            Dictionary with validation error statistics
        """
        async with self.lock:
            total_errors = sum(self.validation_errors.values())
            
            # Get top 10 error types
            top_errors = self.validation_errors.most_common(10)
            
            return {
                "total_errors": total_errors,
                "top_errors": [
                    {"error": error, "count": count}
                    for error, count in top_errors
                ]
            }
    
    async def create_optimized_protocol(self, protocol_name: str, version: str) -> Optional[Protocol]:
        """
        Create an optimized version of a protocol based on interaction patterns.
        
        Args:
            protocol_name: The protocol name
            version: The protocol version
            
        Returns:
            The optimized protocol, or None if optimization failed
        """
        async with self.lock:
            if protocol_name not in self.protocol_versions:
                logger.error(f"Protocol {protocol_name} not registered")
                return None
            
            if version not in self.protocol_versions[protocol_name]:
                logger.error(f"Protocol {protocol_name} v{version} not registered")
                return None
            
            # Get original protocol
            original_protocol = self.protocol_versions[protocol_name][version]
            
            # Check if we have enough interaction patterns
            if protocol_name not in self.interaction_patterns or len(self.interaction_patterns[protocol_name]) < 10:
                logger.info(f"Not enough interaction patterns for {protocol_name} to optimize")
                return None
            
            # Create optimized schema based on common patterns
            optimized_schema = await self._create_optimized_schema(protocol_name, original_protocol.schema)
            
            # Create optimized protocol
            optimized_protocol = Protocol(
                name=f"{protocol_name}_optimized",
                version=f"{version}_opt",
                interaction_type=original_protocol.interaction_type,
                schema=optimized_schema,
                metadata={
                    "optimized_from": protocol_name,
                    "optimized_from_version": version,
                    "optimized_at": time.time(),
                    "compatible_versions": [version]
                }
            )
            
            # Register optimized protocol
            await self.register_protocol(optimized_protocol)
            
            # Register compatibility
            await self.register_protocol_compatibility(
                protocol_name, version, optimized_protocol.version
            )
            
            logger.info(f"Created optimized protocol {optimized_protocol.name} v{optimized_protocol.version}")
            return optimized_protocol
    
    async def _find_compatible_protocol(self, protocol_name: str, version: str) -> Optional[Protocol]:
        """
        Find a compatible protocol version.
        
        Args:
            protocol_name: The protocol name
            version: The requested version
            
        Returns:
            A compatible protocol, or None if not found
        """
        if protocol_name not in self.protocol_versions:
            return None
        
        if version in self.protocol_versions[protocol_name]:
            return self.protocol_versions[protocol_name][version]
        
        # Check for compatible versions
        if protocol_name in self.compatible_versions:
            for registered_version, compatible_versions in self.compatible_versions[protocol_name].items():
                if version in compatible_versions:
                    return self.protocol_versions[protocol_name][registered_version]
        
        # Try to find the closest version (simple version number comparison)
        try:
            requested_parts = [int(part) for part in version.split(".")]
            closest_version = None
            closest_distance = float("inf")
            
            for available_version in self.protocol_versions[protocol_name].keys():
                try:
                    available_parts = [int(part) for part in available_version.split(".")]
                    
                    # Calculate version distance (simple algorithm)
                    distance = 0
                    for i in range(min(len(requested_parts), len(available_parts))):
                        distance += abs(requested_parts[i] - available_parts[i]) * (10 ** (10 - i))
                    
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_version = available_version
                except ValueError:
                    continue
            
            if closest_version and closest_distance < 100:  # Threshold for "close enough"
                return self.protocol_versions[protocol_name][closest_version]
        except ValueError:
            pass
        
        return None
    
    async def _transform_interaction(
        self, interaction: Interaction, from_protocol: str, from_version: str,
        to_protocol: str, to_version: str
    ) -> Interaction:
        """
        Transform an interaction from one protocol to another.
        
        Args:
            interaction: The interaction to transform
            from_protocol: Source protocol name
            from_version: Source protocol version
            to_protocol: Target protocol name
            to_version: Target protocol version
            
        Returns:
            The transformed interaction
            
        Raises:
            ProtocolTransformationError: If transformation fails
        """
        # Check if we have a direct transformer
        key = (f"{from_protocol}:{from_version}", f"{to_protocol}:{to_version}")
        
        if key in self.protocol_transformers:
            transformer = self.protocol_transformers[key]
            
            try:
                # Create a copy of the interaction to transform
                transformed = copy.deepcopy(interaction)
                
                # Apply transformer
                transformed = transformer(transformed)
                
                # Update metadata
                transformed.metadata["transformed_from"] = from_protocol
                transformed.metadata["transformed_from_version"] = from_version
                transformed.metadata["protocol_name"] = to_protocol
                transformed.metadata["protocol_version"] = to_version
                
                return transformed
            except Exception as e:
                logger.error(f"Error transforming interaction: {e}")
                raise ProtocolTransformationError(f"Transformation error: {str(e)}")
        
        # Check if we have the protocols
        if from_protocol not in self.protocol_versions or from_version not in self.protocol_versions[from_protocol]:
            raise ProtocolTransformationError(f"Source protocol {from_protocol} v{from_version} not registered")
        
        if to_protocol not in self.protocol_versions or to_version not in self.protocol_versions[to_protocol]:
            raise ProtocolTransformationError(f"Target protocol {to_protocol} v{to_version} not registered")
        
        # Get protocol schemas
        from_schema = self.protocol_versions[from_protocol][from_version].schema
        to_schema = self.protocol_versions[to_protocol][to_version].schema
        
        # Perform basic transformation (copy matching properties)
        try:
            # Create a copy of the interaction to transform
            transformed = copy.deepcopy(interaction)
            transformed_content = {}
            
            # Get property definitions
            from_properties = from_schema.get("properties", {})
            to_properties = to_schema.get("properties", {})
            
            # Copy matching properties
            for prop_name, prop_schema in to_properties.items():
                if prop_name in interaction.content:
                    transformed_content[prop_name] = interaction.content[prop_name]
                elif prop_name in from_properties and prop_name in interaction.content:
                    transformed_content[prop_name] = interaction.content[prop_name]
            
            # Check required properties
            required_props = to_schema.get("required", [])
            missing_props = [prop for prop in required_props if prop not in transformed_content]
            
            if missing_props:
                raise ProtocolTransformationError(
                    f"Missing required properties for target protocol: {missing_props}"
                )
            
            # Update interaction content
            transformed.content = transformed_content
            
            # Update metadata
            transformed.metadata["transformed_from"] = from_protocol
            transformed.metadata["transformed_from_version"] = from_version
            transformed.metadata["protocol_name"] = to_protocol
            transformed.metadata["protocol_version"] = to_version
            
            return transformed
        except Exception as e:
            logger.error(f"Error transforming interaction: {e}")
            raise ProtocolTransformationError(f"Transformation error: {str(e)}")
    
    async def _track_interaction_pattern(self, protocol_name: str, interaction: Interaction) -> None:
        """
        Track interaction pattern for a protocol.
        
        Args:
            protocol_name: The protocol name
            interaction: The interaction to track
        """
        # Create a pattern string based on interaction content keys
        content_keys = sorted(interaction.content.keys())
        pattern = ":".join(content_keys)
        
        async with self.lock:
            # Update pattern counter
            self.interaction_patterns[protocol_name][pattern] += 1
            
            # Update timestamp
            self.pattern_timestamps[protocol_name][pattern] = time.time()
    
    async def _create_optimized_schema(self, protocol_name: str, original_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an optimized schema based on interaction patterns.
        
        Args:
            protocol_name: The protocol name
            original_schema: The original schema
            
        Returns:
            The optimized schema
        """
        # Start with a copy of the original schema
        optimized_schema = copy.deepcopy(original_schema)
        
        # Get common patterns
        patterns = self.interaction_patterns[protocol_name]
        common_patterns = patterns.most_common(5)
        
        if not common_patterns:
            return original_schema
        
        # Extract common properties
        common_properties = set()
        for pattern, _ in common_patterns:
            properties = pattern.split(":")
            common_properties.update(properties)
        
        # Optimize required properties
        original_required = set(original_schema.get("required", []))
        optimized_required = list(original_required.intersection(common_properties))
        
        # Update schema
        optimized_schema["required"] = optimized_required
        
        # Add optimization metadata
        if "metadata" not in optimized_schema:
            optimized_schema["metadata"] = {}
        
        optimized_schema["metadata"]["optimized"] = True
        optimized_schema["metadata"]["optimized_from_patterns"] = [
            {"pattern": pattern, "count": count}
            for pattern, count in common_patterns
        ]
        
        return optimized_schema
    
    async def _get_optimized_protocol(self, protocol: Protocol) -> Optional[Protocol]:
        """
        Get an optimized version of a protocol if available.
        
        Args:
            protocol: The original protocol
            
        Returns:
            The optimized protocol, or None if not available
        """
        protocol_name = protocol.name
        version = protocol.version
        
        # Check if optimized version exists
        optimized_name = f"{protocol_name}_optimized"
        optimized_version = f"{version}_opt"
        
        if optimized_name in self.protocol_versions and optimized_version in self.protocol_versions[optimized_name]:
            return self.protocol_versions[optimized_name][optimized_version]
        
        # Check if we should create an optimized version
        if (protocol_name in self.interaction_patterns and 
            len(self.interaction_patterns[protocol_name]) >= 50 and
            self.config.get("auto_optimize_protocols", False)):
            
            # Create optimized protocol
            return await self.create_optimized_protocol(protocol_name, version)
        
        return None
    
    def _create_validation_error_details(
        self, error: jsonschema.exceptions.ValidationError, 
        protocol: Protocol, 
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create detailed error report for validation error.
        
        Args:
            error: The validation error
            protocol: The protocol
            content: The content that failed validation
            
        Returns:
            Detailed error report
        """
        # Create error path string
        error_path = ".".join([str(path) for path in error.path]) if error.path else "root"
        
        # Get relevant schema part
        schema_context = None
        if error.path:
            schema_context = protocol.schema
            for path_item in error.path[:-1]:
                if isinstance(schema_context, dict):
                    if path_item in schema_context:
                        schema_context = schema_context[path_item]
                    elif "properties" in schema_context and path_item in schema_context["properties"]:
                        schema_context = schema_context["properties"][path_item]
                    else:
                        schema_context = None
                        break
                else:
                    schema_context = None
                    break
        
        # Get content value at error path
        content_value = None
        if error.path:
            content_value = content
            try:
                for path_item in error.path:
                    if isinstance(content_value, dict) and path_item in content_value:
                        content_value = content_value[path_item]
                    else:
                        content_value = None
                        break
            except Exception:
                content_value = None
        
        # Create detailed error report
        error_details = {
            "error_type": error.validator,
            "error_message": error.message,
            "error_path": error_path,
            "schema_context": schema_context,
            "content_value": content_value,
            "expected": error.validator_value if hasattr(error, "validator_value") else None,
            "protocol": protocol.name,
            "protocol_version": protocol.version,
            "suggestions": []
        }
        
        # Add suggestions based on error type
        if error.validator == "required":
            error_details["suggestions"].append(
                f"Add the required property '{error.validator_value}' to the interaction content"
            )
        elif error.validator == "type":
            error_details["suggestions"].append(
                f"Change the type of '{error_path}' to {error.validator_value}"
            )
        elif error.validator == "enum":
            error_details["suggestions"].append(
                f"Use one of the allowed values for '{error_path}': {error.validator_value}"
            )
        
        return error_details