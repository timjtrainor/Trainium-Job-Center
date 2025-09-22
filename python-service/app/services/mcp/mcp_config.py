"""MCP Configuration Management.

This module provides configuration management for MCP adapter operations,
including environment variable loading and transport creation.
"""

import os
from typing import Optional, Dict, Any
import logging

from .mcp_adapter import MCPGatewayAdapter
from .mcp_exceptions import ConfigurationError
from .mcp_transport import StreamingTransport, StdioTransport

logger = logging.getLogger(__name__)


class MCPConfig:
    """Configuration management for MCP adapter."""
    
    # Default configuration values
    DEFAULT_GATEWAY_URL = "http://mcp-gateway:8811"
    DEFAULT_TRANSPORT_TYPE = "streaming"
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_LOG_LEVEL = "INFO"
    
    # Supported transport types
    SUPPORTED_TRANSPORTS = {"streaming", "stdio"}
    
    @classmethod
    def from_environment(cls) -> MCPGatewayAdapter:
        """Create adapter from environment variables.
        
        Environment Variables:
            MCP_GATEWAY_URL: Gateway URL for streaming transport (default: http://mcp-gateway:8811)
            MCP_GATEWAY_TRANSPORT: Transport type - 'streaming' or 'stdio' (default: streaming)
            MCP_GATEWAY_TIMEOUT: Operation timeout in seconds (default: 30)
            MCP_GATEWAY_MAX_RETRIES: Maximum retry attempts (default: 3)
            MCP_LOG_LEVEL: Logging level (default: INFO)
            
        Returns:
            Configured MCPGatewayAdapter instance
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        logger.info("Loading MCP configuration from environment variables")
        
        # Load configuration from environment
        config = cls._load_config_from_env()
        
        # Validate configuration
        cls._validate_config(config)
        
        # Create transport based on type
        transport = cls._create_transport(config)
        
        # Create and return adapter
        adapter = MCPGatewayAdapter(
            transport=transport,
            timeout=config["timeout"],
            max_retries=config["max_retries"],
            log_level=config["log_level"]
        )
        
        logger.info(
            "MCP adapter created from environment configuration",
            extra={
                "transport_type": config["transport_type"],
                "timeout": config["timeout"],
                "max_retries": config["max_retries"],
                "log_level": config["log_level"]
            }
        )
        
        return adapter
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> MCPGatewayAdapter:
        """Create adapter from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary with keys:
                - gateway_url: Gateway URL (optional for stdio transport)
                - transport_type: 'streaming' or 'stdio'
                - timeout: Operation timeout in seconds
                - max_retries: Maximum retry attempts  
                - log_level: Logging level
                
        Returns:
            Configured MCPGatewayAdapter instance
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        logger.info("Loading MCP configuration from dictionary")
        
        # Apply defaults for missing values
        config = cls._apply_defaults(config_dict)
        
        # Validate configuration
        cls._validate_config(config)
        
        # Create transport
        transport = cls._create_transport(config)
        
        # Create and return adapter
        return MCPGatewayAdapter(
            transport=transport,
            timeout=config["timeout"],
            max_retries=config["max_retries"],
            log_level=config["log_level"]
        )
        
    @classmethod
    def _load_config_from_env(cls) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            "gateway_url": os.getenv("MCP_GATEWAY_URL", cls.DEFAULT_GATEWAY_URL),
            "transport_type": os.getenv("MCP_GATEWAY_TRANSPORT", cls.DEFAULT_TRANSPORT_TYPE).lower(),
            "timeout": cls._parse_int_env("MCP_GATEWAY_TIMEOUT", cls.DEFAULT_TIMEOUT),
            "max_retries": cls._parse_int_env("MCP_GATEWAY_MAX_RETRIES", cls.DEFAULT_MAX_RETRIES),
            "log_level": os.getenv("MCP_LOG_LEVEL", cls.DEFAULT_LOG_LEVEL).upper()
        }
        
    @classmethod
    def _apply_defaults(cls, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values to configuration dictionary."""
        return {
            "gateway_url": config_dict.get("gateway_url", cls.DEFAULT_GATEWAY_URL),
            "transport_type": config_dict.get("transport_type", cls.DEFAULT_TRANSPORT_TYPE).lower(),
            "timeout": config_dict.get("timeout", cls.DEFAULT_TIMEOUT),
            "max_retries": config_dict.get("max_retries", cls.DEFAULT_MAX_RETRIES),
            "log_level": config_dict.get("log_level", cls.DEFAULT_LOG_LEVEL).upper()
        }
        
    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> None:
        """Validate configuration values.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = []
        
        # Validate transport type
        if config["transport_type"] not in cls.SUPPORTED_TRANSPORTS:
            errors.append(
                f"Unsupported transport type: {config['transport_type']}. "
                f"Supported types: {', '.join(cls.SUPPORTED_TRANSPORTS)}"
            )
            
        # Validate timeout
        if not isinstance(config["timeout"], int) or config["timeout"] <= 0:
            errors.append(f"Invalid timeout: {config['timeout']}. Must be a positive integer.")
            
        # Validate max_retries
        if not isinstance(config["max_retries"], int) or config["max_retries"] < 0:
            errors.append(f"Invalid max_retries: {config['max_retries']}. Must be a non-negative integer.")
            
        # Validate log_level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if config["log_level"] not in valid_log_levels:
            errors.append(
                f"Invalid log_level: {config['log_level']}. "
                f"Valid levels: {', '.join(valid_log_levels)}"
            )
            
        # Validate gateway_url for streaming transport
        if config["transport_type"] == "streaming":
            gateway_url = config.get("gateway_url")
            if not gateway_url or not isinstance(gateway_url, str):
                errors.append("gateway_url is required for streaming transport")
            elif not (gateway_url.startswith("http://") or gateway_url.startswith("https://")):
                errors.append(f"Invalid gateway_url format: {gateway_url}. Must start with http:// or https://")
                
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ConfigurationError(error_msg)
            
    @classmethod
    def _create_transport(cls, config: Dict[str, Any]):
        """Create transport instance based on configuration.
        
        Args:
            config: Validated configuration dictionary
            
        Returns:
            Transport instance
            
        Raises:
            ConfigurationError: If transport creation fails
        """
        transport_type = config["transport_type"]
        
        try:
            if transport_type == "streaming":
                transport = StreamingTransport(config["gateway_url"])
                logger.debug(f"Created StreamingTransport with URL: {config['gateway_url']}")
                
            elif transport_type == "stdio":
                transport = StdioTransport()
                logger.debug("Created StdioTransport")
                
            else:
                # This should not happen after validation, but just in case
                raise ConfigurationError(f"Unknown transport type: {transport_type}")
                
            return transport
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            else:
                raise ConfigurationError(f"Failed to create transport: {e}")
                
    @classmethod
    def _parse_int_env(cls, env_var: str, default: int) -> int:
        """Parse integer environment variable with fallback.
        
        Args:
            env_var: Environment variable name
            default: Default value if parsing fails
            
        Returns:
            Parsed integer value or default
        """
        value = os.getenv(env_var)
        if value is None:
            return default
            
        try:
            return int(value)
        except ValueError:
            logger.warning(
                f"Invalid integer value for {env_var}: {value}. Using default: {default}"
            )
            return default
            
    @classmethod
    def get_config_info(cls) -> Dict[str, Any]:
        """Get information about current configuration.
        
        Returns:
            Dictionary with configuration details and sources
        """
        env_config = cls._load_config_from_env()
        
        return {
            "defaults": {
                "gateway_url": cls.DEFAULT_GATEWAY_URL,
                "transport_type": cls.DEFAULT_TRANSPORT_TYPE,
                "timeout": cls.DEFAULT_TIMEOUT,
                "max_retries": cls.DEFAULT_MAX_RETRIES,
                "log_level": cls.DEFAULT_LOG_LEVEL
            },
            "current_env": env_config,
            "supported_transports": list(cls.SUPPORTED_TRANSPORTS),
            "environment_variables": {
                "MCP_GATEWAY_URL": os.getenv("MCP_GATEWAY_URL"),
                "MCP_GATEWAY_TRANSPORT": os.getenv("MCP_GATEWAY_TRANSPORT"), 
                "MCP_GATEWAY_TIMEOUT": os.getenv("MCP_GATEWAY_TIMEOUT"),
                "MCP_GATEWAY_MAX_RETRIES": os.getenv("MCP_GATEWAY_MAX_RETRIES"),
                "MCP_LOG_LEVEL": os.getenv("MCP_LOG_LEVEL")
            }
        }
        
    @classmethod
    def create_test_config(
        cls,
        transport_type: str = "stdio",
        timeout: int = 5,
        max_retries: int = 1,
        log_level: str = "DEBUG"
    ) -> Dict[str, Any]:
        """Create configuration suitable for testing.
        
        Args:
            transport_type: Transport type for testing
            timeout: Short timeout for tests
            max_retries: Minimal retries for tests
            log_level: Debug level for detailed test logs
            
        Returns:
            Test configuration dictionary
        """
        config = {
            "transport_type": transport_type,
            "timeout": timeout,
            "max_retries": max_retries,
            "log_level": log_level
        }
        
        if transport_type == "streaming":
            config["gateway_url"] = "http://localhost:8811"
            
        return config