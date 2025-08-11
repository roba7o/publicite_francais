"""
Shared ConsolidatedOutput instance for the application.

Provides a single, shared output instance to eliminate duplicate creation patterns.
"""

from utils.terminal_output import ConsolidatedOutput

# Shared instance for the entire application
output = ConsolidatedOutput("database_pipeline")