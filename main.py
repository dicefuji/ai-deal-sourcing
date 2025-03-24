#!/usr/bin/env python3
"""
AI Deal Sourcing - Main Entry Point
This script serves as the main entry point for the AI Deal Sourcing application.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main script
if __name__ == "__main__":
    import importlib.util
    
    # Import the module from src
    spec = importlib.util.spec_from_file_location(
        "ai_deal_sourcing", 
        os.path.join(os.path.dirname(__file__), 'src', 'ai_deal_sourcing.py')
    )
    ai_deal_sourcing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ai_deal_sourcing) 