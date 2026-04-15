"""
Configuration Manager for the GödelOS Test Runner.

This module provides functionality to load and manage configuration settings
from various sources (command line arguments, config files, and defaults).
"""

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


@dataclass
class TestRunnerConfig:
    """Data class representing the configuration for the test runner."""
    
    # Test discovery patterns
    test_patterns: List[str] = field(default_factory=lambda: ["test_*.py"])
    test_dirs: List[str] = field(default_factory=lambda: ["tests"])
    
    # Test categorization
    categories: Dict[str, List[str]] = field(default_factory=dict)
    
    # Test execution options
    parallel: bool = False
    max_workers: int = 1
    timeout: int = 300  # seconds
    
    # Output options
    verbose: bool = False
    output_dir: Optional[str] = None
    output_level: str = "NORMAL"  # MINIMAL, NORMAL, VERBOSE, DEBUG
    use_colors: bool = True
    use_emoji: bool = True
    
    # Results collection options
    results_dir: Optional[str] = None  # Directory to store test results
    store_results: bool = False  # Whether to store results for later analysis
    
    # Timing options
    detailed_timing: bool = False  # Whether to track detailed timing information
    timing_history_limit: int = 10  # Maximum number of historical timing entries to keep
    
    # Statistics options
    num_slowest_tests: int = 10  # Number of slowest tests to track
    num_most_failing_tests: int = 10  # Number of most failing tests to track
    statistics_history_limit: int = 10  # Maximum number of historical statistics to keep
    
    # Report options (new)
    generate_html_report: bool = False  # Whether to generate HTML reports
    html_report_path: Optional[str] = None  # Path to save HTML reports
    generate_json_report: bool = False  # Whether to generate JSON reports
    json_report_path: Optional[str] = None  # Path to save JSON reports
    
    # Display options (new)
    show_docstrings: bool = True  # Whether to show docstrings in output
    show_phase_separation: bool = True  # Whether to show phase separation in output
    terminal_width: int = 80  # Terminal width for formatting
    
    # Additional pytest arguments
    pytest_args: List[str] = field(default_factory=list)
    
    # Custom options
    custom_options: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """
    Manages configuration for the GödelOS Test Runner.
    
    This class is responsible for loading configuration from various sources
    (command line arguments, config files, environment variables) and providing
    a unified configuration object to the test runner components.
    """
    
    DEFAULT_CONFIG_PATHS = [
        "./godeltest.json",
        "./godeltest.config.json",
        "./.godeltest",
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigurationManager.
        
        Args:
            config_path: Optional path to a configuration file. If not provided,
                         the manager will look for configuration in default locations.
        """
        self.config = TestRunnerConfig()
        self.config_path = config_path
    
    def load_config(self, cli_args: Optional[List[str]] = None) -> TestRunnerConfig:
        """
        Load configuration from all sources and return a unified configuration.
        
        The configuration is loaded in the following order, with later sources
        overriding earlier ones:
        1. Default values
        2. Configuration file
        3. Environment variables
        4. Command line arguments
        
        Args:
            cli_args: Optional list of command line arguments. If not provided,
                      sys.argv will be used.
        
        Returns:
            A TestRunnerConfig object with the unified configuration.
        """
        # Start with default configuration
        config = TestRunnerConfig()
        
        # Load from config file
        file_config = self._load_from_file()
        if file_config:
            self._update_config(config, file_config)
        
        # Load from environment variables
        env_config = self._load_from_env()
        if env_config:
            self._update_config(config, env_config)
        
        # Load from command line arguments
        if cli_args is not None:
            cli_config = self._load_from_cli(cli_args)
            if cli_config:
                self._update_config(config, cli_config)
        
        self.config = config
        return config
    
    def _load_from_file(self) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.
        
        Returns:
            A dictionary with the configuration loaded from the file, or an empty
            dictionary if no file was found or the file couldn't be parsed.
        """
        # Check specified config path first
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config from {self.config_path}: {e}")
        
        # Check default paths
        for path in self.DEFAULT_CONFIG_PATHS:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading config from {path}: {e}")
        
        return {}
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Environment variables should be prefixed with GODELTEST_.
        For example, GODELTEST_VERBOSE=1 would set verbose=True.
        
        Returns:
            A dictionary with the configuration loaded from environment variables.
        """
        config = {}
        prefix = "GODELTEST_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                
                # Convert some values to appropriate types
                if value.lower() in ('true', '1', 'yes'):
                    config[config_key] = True
                elif value.lower() in ('false', '0', 'no'):
                    config[config_key] = False
                elif value.isdigit():
                    config[config_key] = int(value)
                else:
                    config[config_key] = value
        
        return config
    
    def _load_from_cli(self, args: List[str]) -> Dict[str, Any]:
        """
        Load configuration from command line arguments.
        
        Args:
            args: List of command line arguments.
        
        Returns:
            A dictionary with the configuration loaded from command line arguments.
        """
        parser = argparse.ArgumentParser(description="GödelOS Test Runner")
        
        # Test discovery options
        parser.add_argument("--test-pattern", action="append", dest="test_patterns",
                          help="Pattern to match test files (can be specified multiple times)")
        parser.add_argument("--test-dir", action="append", dest="test_dirs",
                          help="Directory to search for tests (can be specified multiple times)")
        
        # Test execution options
        parser.add_argument("--parallel", action="store_true",
                          help="Run tests in parallel")
        parser.add_argument("--max-workers", type=int,
                          help="Maximum number of parallel workers")
        parser.add_argument("--timeout", type=int,
                          help="Timeout for test execution in seconds")
        
        # Output options
        parser.add_argument("--verbose", "-v", action="store_true",
                          help="Enable verbose output")
        parser.add_argument("--output-dir",
                          help="Directory for test output files")
        parser.add_argument("--output-level", choices=["MINIMAL", "NORMAL", "VERBOSE", "DEBUG"],
                          help="Set output verbosity level")
        parser.add_argument("--no-color", action="store_true",
                          help="Disable colored output")
        parser.add_argument("--no-emoji", action="store_true",
                          help="Disable emoji in output")
        
        # Results collection options
        parser.add_argument("--results-dir",
                          help="Directory to store test results")
        parser.add_argument("--store-results", action="store_true",
                          help="Store results for later analysis")
                          
        # Report options
        parser.add_argument("--generate-html-report", action="store_true",
                          help="Generate HTML report")
        parser.add_argument("--html-report-path",
                          help="Path to save HTML report")
        parser.add_argument("--generate-json-report", action="store_true",
                          help="Generate JSON report")
        parser.add_argument("--json-report-path",
                          help="Path to save JSON report")
                          
        # Display options
        parser.add_argument("--no-docstrings", action="store_true",
                          help="Disable docstring display")
        parser.add_argument("--no-phase-separation", action="store_true",
                          help="Disable test phase separation")
        parser.add_argument("--terminal-width", type=int,
                          help="Terminal width for formatting")
        
        # Timing options
        parser.add_argument("--detailed-timing", action="store_true",
                          help="Track detailed timing information")
        parser.add_argument("--timing-history-limit", type=int,
                          help="Maximum number of historical timing entries to keep")
        
        # Statistics options
        parser.add_argument("--num-slowest-tests", type=int,
                          help="Number of slowest tests to track")
        parser.add_argument("--num-most-failing-tests", type=int,
                          help="Number of most failing tests to track")
        
        # Config file option
        parser.add_argument("--config",
                          help="Path to configuration file")
        
        # Parse arguments
        parsed_args, remaining = parser.parse_known_args(args)
        
        # Convert parsed arguments to dictionary, excluding None values
        config = {k: v for k, v in vars(parsed_args).items() if v is not None}
        
        # Handle negated boolean flags
        if "no_docstrings" in config:
            config["show_docstrings"] = not config.pop("no_docstrings")
            
        if "no_phase_separation" in config:
            config["show_phase_separation"] = not config.pop("no_phase_separation")
        
        # Store remaining arguments as pytest_args
        if remaining:
            config["pytest_args"] = remaining
        
        # If config file specified, update config_path
        if "config" in config:
            self.config_path = config.pop("config")
        
        return config
    
    def _update_config(self, config: TestRunnerConfig, updates: Dict[str, Any]) -> None:
        """
        Update configuration object with values from a dictionary.
        
        Args:
            config: The TestRunnerConfig object to update.
            updates: Dictionary with values to update in the config.
        """
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                # Store unknown options in custom_options
                config.custom_options[key] = value
    
    def get_config(self) -> TestRunnerConfig:
        """
        Get the current configuration.
        
        Returns:
            The current TestRunnerConfig object.
        """
        return self.config
    
    def save_config(self, path: Optional[str] = None) -> None:
        """
        Save the current configuration to a file.
        
        Args:
            path: Path to save the configuration to. If not provided, the
                  current config_path will be used, or the first default path.
        """
        save_path = path or self.config_path or self.DEFAULT_CONFIG_PATHS[0]
        
        # Convert config to dictionary
        config_dict = {k: v for k, v in self.config.__dict__.items()}
        
        try:
            with open(save_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except IOError as e:
            print(f"Error saving config to {save_path}: {e}")