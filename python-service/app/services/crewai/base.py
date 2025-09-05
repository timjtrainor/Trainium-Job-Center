"""
Shared utilities for CrewAI multi-crew architecture.

This module provides common utilities for implementing 
scalable CrewAI crews following best practices.
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger
import yaml
import os


def load_agent_config(base_dir: Path, agent_name: str) -> Dict[str, Any]:
    """Load agent configuration from YAML file."""
    agents_dir = base_dir / "agents"
    agent_file = agents_dir / f"{agent_name}.yaml"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent configuration not found: {agent_file}")
    
    try:
        with open(agent_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Add version field if not present
        if 'version' not in config:
            config['version'] = '1.0'
            
        logger.debug(f"Loaded agent config for {agent_name}: {config.get('id')}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load agent config {agent_file}: {str(e)}")
        raise


def load_tasks_config(base_dir: Path, crew_name: str) -> Dict[str, Any]:
    """Load tasks configuration for a specific crew."""
    tasks_file = base_dir / crew_name / "tasks.yaml"
    if not tasks_file.exists():
        raise FileNotFoundError(f"Tasks configuration not found: {tasks_file}")
    
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Add version field if not present
        if 'version' not in config:
            config['version'] = '1.0'
            
        logger.debug(f"Loaded tasks config for {crew_name}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load tasks config {tasks_file}: {str(e)}")
        raise


def get_mock_mode() -> bool:
    """Check if CrewAI should run in mock mode."""
    return os.getenv("CREWAI_MOCK_MODE", "false").lower() == "true"


def log_crew_execution(crew_name: str, inputs: Dict[str, Any], result: Any):
    """Log crew execution for debugging and monitoring."""
    if get_mock_mode():
        logger.info(f"[MOCK] {crew_name} crew executed with inputs: {list(inputs.keys())}")
    else:
        logger.info(f"{crew_name} crew executed successfully")