"""
Console Formatter Module for the GödelOS Test Runner.

This module provides the ConsoleFormatter class that handles color-coding
and emoji for console output.
"""

import os
import sys
import time
from typing import Dict, List, Optional, Any, Tuple

from godelOS.test_runner.output_manager import OutputLevel


class ConsoleFormatter:
    """
    Handles color-coding and emoji for console output with improved readability.
    
    This class provides methods for formatting text with ANSI colors and
    emoji characters, with graceful fallback for environments that don't
    support these features. It also provides methods for formatting test
    phase headers and test details to improve readability.
    """
    
    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'italic': '\033[3m',
        'underline': '\033[4m',
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bg_black': '\033[40m',
        'bg_red': '\033[41m',
        'bg_green': '\033[42m',
        'bg_yellow': '\033[43m',
        'bg_blue': '\033[44m',
        'bg_magenta': '\033[45m',
        'bg_cyan': '\033[46m',
        'bg_white': '\033[47m',
    }
    
    # Emoji for test statuses - enhanced for better visual distinction
    EMOJI = {
        'passed': '✅',
        'failed': '❌',
        'skipped': '⏭️',
        'xpassed': '⚠️',
        'xfailed': '⚠️',
        'error': '💥',
        'running': '🔄',
        'info': 'ℹ️',
        'header': '📋',
        'warning': '⚠️',
        'setup': '🔧',
        'execution': '⚙️',
        'teardown': '🧹',
        'summary': '📊',
        'slow': '🐢',
        'fast': '🚀',
        'flaky': '🔀',
    }
    
    # Status to color mapping - enhanced with more distinct colors
    STATUS_COLORS = {
        'passed': 'green',
        'failed': 'red',
        'skipped': 'yellow',
        'xpassed': 'yellow',
        'xfailed': 'yellow',
        'error': 'red',
        'running': 'blue',
        'info': 'cyan',
        'header': 'bold',
        'warning': 'yellow',
        'setup': 'blue',
        'execution': 'magenta',
        'teardown': 'cyan',
        'summary': 'bold',
        'slow': 'red',
        'fast': 'green',
        'flaky': 'magenta',
    }
    
    def __init__(self, config: Any):
        """
        Initialize the ConsoleFormatter.
        
        Args:
            config: Configuration object containing formatting settings.
        """
        self.config = config
        self.use_colors = self._should_use_colors()
        self.use_emoji = self._should_use_emoji()
        self.spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_index = 0
        self.progress_total = 0
        self.progress_current = 0
        self.last_update_time = 0
        self.progress_active = False
    
    def _should_use_colors(self) -> bool:
        """
        Determine if color output should be used.
        
        Returns:
            True if colors should be used, False otherwise.
        """
        # Check if colors are explicitly disabled in config
        if hasattr(self.config, 'custom_options') and 'no_color' in self.config.custom_options:
            return not self.config.custom_options['no_color']
        
        # Check if output is redirected to a file
        if not sys.stdout.isatty():
            return False
        
        # Check for NO_COLOR environment variable (standard for disabling color)
        if os.environ.get('NO_COLOR') is not None:
            return False
        
        # Check for TERM environment variable
        term = os.environ.get('TERM', '')
        if term == 'dumb':
            return False
        
        return True
    
    def _should_use_emoji(self) -> bool:
        """
        Determine if emoji should be used.
        
        Returns:
            True if emoji should be used, False otherwise.
        """
        # Check if emoji are explicitly disabled in config
        if hasattr(self.config, 'custom_options') and 'no_emoji' in self.config.custom_options:
            return not self.config.custom_options['no_emoji']
        
        # Default to same as color support
        return self.use_colors
    
    def colorize(self, text: str, color: str) -> str:
        """
        Apply color to text if colors are enabled.
        
        Args:
            text: The text to colorize.
            color: The color to apply.
            
        Returns:
            The colorized text, or the original text if colors are disabled.
        """
        if not self.use_colors or color not in self.COLORS:
            return text
        
        return f"{self.COLORS[color]}{text}{self.COLORS['reset']}"
    
    def emojify(self, status: str) -> str:
        """
        Get emoji for a status if emoji are enabled.
        
        Args:
            status: The status to get emoji for.
            
        Returns:
            The emoji string, or an empty string if emoji are disabled.
        """
        if not self.use_emoji or status not in self.EMOJI:
            return ''
        
        return f"{self.EMOJI[status]} "
    
    def format_text(self, text: str, status: str = 'info', error: bool = False, phase: Optional[str] = None, **kwargs) -> str:
        """
        Format text with color and emoji based on status.
        
        Args:
            text: The text to format.
            status: The status to use for formatting.
            error: Whether this is an error message.
            phase: Optional test phase (setup, execution, teardown).
            **kwargs: Additional formatting options.
            
        Returns:
            The formatted text.
        """
        # Determine color based on status or phase
        if phase and phase in self.STATUS_COLORS:
            color = self.STATUS_COLORS[phase]
        else:
            color = self.STATUS_COLORS.get(status, 'reset')
            
        if error:
            color = 'red'
        
        # Add emoji if appropriate
        emoji_prefix = self.emojify(status)
        
        # Apply color
        return f"{emoji_prefix}{self.colorize(text, color)}"
    
    def start_progress(self, total: int) -> None:
        """
        Start a progress indicator for test execution.
        
        Args:
            total: The total number of tests to be executed.
        """
        self.progress_total = total
        self.progress_current = 0
        self.last_update_time = time.time()
        self.progress_active = True
        
        # Initial progress display
        self._update_progress_display()
    
    def update_progress(self, current: int, status: Optional[str] = None) -> None:
        """
        Update the progress indicator.
        
        Args:
            current: The current number of completed tests.
            status: Optional status to display (e.g., 'passed', 'failed').
        """
        if not self.progress_active:
            return
        
        self.progress_current = current
        
        # Only update display if enough time has passed (to avoid flickering)
        current_time = time.time()
        if current_time - self.last_update_time > 0.1:  # Update at most 10 times per second
            self.last_update_time = current_time
            self._update_progress_display(status)
    
    def _update_progress_display(self, status: Optional[str] = None) -> None:
        """
        Update the progress display on the console.
        
        Args:
            status: Optional status to display.
        """
        if not self.use_colors:
            # Simple progress for non-color terminals
            percent = int(100 * self.progress_current / max(1, self.progress_total))
            progress_text = f"Progress: {self.progress_current}/{self.progress_total} ({percent}%)"
            if status:
                progress_text += f" - Last test: {status}"
            
            sys.stdout.write(f"\r{progress_text}")
            sys.stdout.flush()
            return
        
        # Fancy progress bar for color terminals
        bar_width = 40
        filled_width = int(bar_width * self.progress_current / max(1, self.progress_total))
        
        # Spinner animation
        spinner = self.spinner_frames[self.spinner_index]
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
        
        # Progress bar
        bar = '█' * filled_width + '░' * (bar_width - filled_width)
        
        # Percentage
        percent = int(100 * self.progress_current / max(1, self.progress_total))
        
        # Status indicator
        status_text = ""
        if status:
            emoji = self.emojify(status)
            color = self.STATUS_COLORS.get(status, 'reset')
            status_text = f" - Last: {emoji}{self.colorize(status, color)}"
        
        # Combine all parts
        progress_text = f"{spinner} [{bar}] {self.progress_current}/{self.progress_total} ({percent}%){status_text}"
        
        # Write to stdout
        sys.stdout.write(f"\r{progress_text}")
        sys.stdout.flush()
    
    def finish_progress(self) -> None:
        """Finish and clear the progress indicator."""
        if self.progress_active:
            # Clear the progress line
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
            self.progress_active = False
            
    def format_phase_header(self, phase_name: str) -> str:
        """
        Format a test phase header with enhanced visual separation.
        
        Args:
            phase_name: The name of the phase (setup, execution, teardown).
            
        Returns:
            The formatted phase header.
        """
        phase_color = self.STATUS_COLORS.get(phase_name.lower(), 'bold')
        phase_emoji = self.EMOJI.get(phase_name.lower(), '')
        separator = "─" * 50
        
        # Create a more visually distinct header with emoji
        header = f"{phase_emoji} {phase_name.upper()} PHASE"
        
        return f"\n{self.colorize(separator, 'dim')}\n{self.colorize(f'▶ {header}', phase_color)}\n{self.colorize(separator, 'dim')}\n"
    
    def format_test_details(self, result: Any) -> str:
        """
        Format test details including docstring information with enhanced readability.
        
        Args:
            result: The test result object.
            
        Returns:
            The formatted test details.
        """
        details = []
        
        # Add docstring information if available with improved formatting
        if hasattr(result, 'parsed_docstring') and result.parsed_docstring:
            parsed = result.parsed_docstring
            if parsed.get('purpose'):
                details.append(f"  {self.colorize('Purpose:', 'bold')} {self.colorize(parsed['purpose'], 'cyan')}")
            if parsed.get('expected_behavior'):
                details.append(f"  {self.colorize('Expected:', 'bold')} {self.colorize(parsed['expected_behavior'], 'cyan')}")
            if parsed.get('edge_cases'):
                details.append(f"  {self.colorize('Edge Cases:', 'bold')} {self.colorize(parsed['edge_cases'], 'cyan')}")
        
        # Add timing information if available with emoji indicators
        if hasattr(result, 'setup_time') and result.setup_time is not None:
            setup_emoji = self.EMOJI.get('setup', '')
            details.append(f"  {setup_emoji} {self.colorize('Setup:', 'bold')} {self.colorize(f'{result.setup_time:.3f}s', 'blue')}")
        
        if hasattr(result, 'execution_time') and result.execution_time is not None:
            execution_emoji = self.EMOJI.get('execution', '')
            # Add slow/fast indicator based on execution time
            speed_indicator = ''
            if result.execution_time > 1.0:  # More than 1 second is considered slow
                speed_indicator = f" {self.EMOJI.get('slow', '')}"
            elif result.execution_time < 0.1:  # Less than 0.1 second is considered fast
                speed_indicator = f" {self.EMOJI.get('fast', '')}"
                
            details.append(f"  {execution_emoji} {self.colorize('Execution:', 'bold')} {self.colorize(f'{result.execution_time:.3f}s', 'magenta')}{speed_indicator}")
        
        if hasattr(result, 'teardown_time') and result.teardown_time is not None:
            teardown_emoji = self.EMOJI.get('teardown', '')
            details.append(f"  {teardown_emoji} {self.colorize('Teardown:', 'bold')} {self.colorize(f'{result.teardown_time:.3f}s', 'cyan')}")
        
        # Add historical data if available
        if hasattr(result, 'previous_durations') and result.previous_durations:
            avg_duration = sum(result.previous_durations) / len(result.previous_durations) if result.previous_durations else 0
            if avg_duration > 0:
                details.append(f"  {self.colorize('Avg Duration:', 'bold')} {self.colorize(f'{avg_duration:.3f}s', 'yellow')}")
        
        # Add flaky test indicator if the test has both passed and failed in history
        if hasattr(result, 'previous_outcomes') and result.previous_outcomes:
            if 'passed' in result.previous_outcomes and ('failed' in result.previous_outcomes or 'error' in result.previous_outcomes):
                flaky_emoji = self.EMOJI.get('flaky', '')
                details.append(f"  {flaky_emoji} {self.colorize('Flaky Test', 'magenta')}")
        
        return "\n".join(details) if details else ""