"""
Shared utilities for CrewAI multi-crew architecture.

This module provides common utilities for implementing 
scalable CrewAI crews following best practices.
"""
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from loguru import logger
import yaml
import os
import asyncio
from functools import lru_cache

from ..mcp_adapter import get_mcp_adapter, create_sync_tool_wrapper
from ...core.config import get_settings
from crewai.tools import BaseTool


class MCPDynamicTool(BaseTool):
    """Lightweight wrapper around MCP tools for CrewAI compatibility.

    MCP tools expect arguments in the form ``{"args": ..., "kwargs": {}}``.
    This wrapper translates CrewAI's positional arguments into that structure
    before delegating execution to the underlying MCP executor.
    """

    name: str
    description: str = ""
    executor: Callable[..., Any]
    parameters: Dict[str, Any] | None = None

    def _run(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        if args:
            arg_payload = args[0] if len(args) == 1 else list(args)
            return self.executor(args=arg_payload, kwargs={})
        return self.executor(**kwargs)

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        raise NotImplementedError("MCPDynamicTool does not support async execution")


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


async def load_mcp_tools(tool_names: List[str]) -> List[BaseTool]:
    """
    Load tools from MCP servers through the Docker MCP Gateway.
    
    Args:
        tool_names: List of tool names to load
        
    Returns:
        List of loaded tool implementations
    """
    settings = get_settings()
    
    # Check if MCP Gateway is enabled
    if not getattr(settings, 'mcp_gateway_enabled', True):
        logger.info("MCP Gateway disabled, skipping tool loading")
        return []
        
    gateway_url = getattr(settings, 'mcp_gateway_url', 'http://localhost:8811')
    loaded_tools = []
    
    try:
        async with get_mcp_adapter(gateway_url) as adapter:
            available_tools = adapter.get_available_tools()
            
            if not available_tools:
                logger.warning("No tools available from MCP Gateway")
                return []
            
            for tool_name in tool_names:
                # Handle different tool name formats
                if tool_name in available_tools:
                    # Direct match
                    tool_config = available_tools[tool_name]
                elif f"duckduckgo_{tool_name}" in available_tools:
                    # Try with duckduckgo prefix
                    tool_config = available_tools[f"duckduckgo_{tool_name}"]
                    tool_name = f"duckduckgo_{tool_name}"
                else:
                    # Check for partial matches
                    matches = [t for t in available_tools.keys() if tool_name in t]
                    if matches:
                        tool_name = matches[0]
                        tool_config = available_tools[tool_name]
                    else:
                        logger.warning(f"Tool '{tool_name}' not found in MCP servers")
                        continue
                
                # Convert async tool to sync for CrewAI compatibility
                async_executor = adapter._create_tool_executor(tool_name, tool_config)
                sync_executor = create_sync_tool_wrapper(async_executor)

                tool = MCPDynamicTool(
                    name=tool_name,
                    description=tool_config.get("description", ""),
                    executor=sync_executor,
                    parameters=tool_config.get("parameters", {}),
                )

                loaded_tools.append(tool)
                logger.info(f"Loaded MCP tool: {tool_name}")
                
        return loaded_tools
        
    except Exception as e:
        logger.error(f"Failed to load MCP tools: {e}")
        logger.info("MCP tools unavailable - continuing without them")
        return []


def load_mcp_tools_sync(tool_names: List[str]) -> List[BaseTool]:
    """
    Synchronous wrapper for loading MCP tools.
    
    Args:
        tool_names: List of tool names to load
        
    Returns:
        List of loaded tool implementations
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one in a thread
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(load_mcp_tools(tool_names))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(load_mcp_tools(tool_names))
    except Exception as e:
        logger.error(f"Error in sync MCP tool loading: {e}")
        return []


@lru_cache(maxsize=1)
def get_duckduckgo_tools() -> List[BaseTool]:
    """Load DuckDuckGo tools once and cache the result."""
    return load_mcp_tools_sync(["web_search", "search"])


def clear_mcp_tool_cache() -> None:
    """Clear cached MCP tools.

    Should be called at application startup or when MCP tool configuration
    changes to ensure stale tools aren't reused.
    """
    get_duckduckgo_tools.cache_clear()


# Clear any cached tools on import to avoid stale configuration
clear_mcp_tool_cache()
