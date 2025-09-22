"""MCP Logging Configuration.

This module provides structured logging configuration for MCP adapter operations.
It uses Python's built-in logging with structured JSON formatting when available.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def __init__(self):
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'message'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry)


class MCPLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds MCP-specific context to log records."""
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process log message and add MCP context."""
        # Add MCP context to extra fields
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # Merge adapter extra with call-specific extra
        kwargs['extra'].update(self.extra)
        
        return msg, kwargs
    
    def with_context(self, **context: Any) -> 'MCPLoggerAdapter':
        """Create a new adapter with additional context."""
        new_extra = {**self.extra, **context}
        return MCPLoggerAdapter(self.logger, new_extra)


def configure_logging(
    log_level: str = "INFO",
    structured: bool = True,
    logger_name: str = "mcp"
) -> logging.Logger:
    """Configure structured logging for MCP adapter.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use structured JSON logging
        logger_name: Name of the logger to configure
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    logger.info(f"MCP logging configured with level: {log_level}")
    return logger


def get_mcp_logger(
    name: str = "mcp",
    correlation_id: Optional[str] = None,
    transport_type: Optional[str] = None,
    **context: Any
) -> MCPLoggerAdapter:
    """Get an MCP logger with optional context.
    
    Args:
        name: Logger name
        correlation_id: Optional correlation ID for request tracking
        transport_type: Optional transport type (stdio, streaming)
        **context: Additional context fields
    
    Returns:
        MCPLoggerAdapter with context
    """
    logger = logging.getLogger(name)
    
    # Build context
    extra = {}
    if correlation_id:
        extra["correlation_id"] = correlation_id
    if transport_type:
        extra["transport_type"] = transport_type
    
    extra.update(context)
    
    return MCPLoggerAdapter(logger, extra)


# Module-level logger for MCP operations
mcp_logger = get_mcp_logger()


# Convenience functions for common logging patterns

def log_transport_operation(
    logger: MCPLoggerAdapter,
    operation: str,
    transport_type: str,
    success: bool = True,
    duration_ms: Optional[float] = None,
    **details: Any
) -> None:
    """Log a transport operation with standardized fields."""
    log_data = {
        "operation": operation,
        "transport_type": transport_type,
        "success": success
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    log_data.update(details)
    
    if success:
        logger.info(f"Transport operation completed: {operation}", extra=log_data)
    else:
        logger.error(f"Transport operation failed: {operation}", extra=log_data)


def log_message_exchange(
    logger: MCPLoggerAdapter,
    direction: str,  # 'sent' or 'received'
    message_type: str,
    message_id: Optional[int] = None,
    method: Optional[str] = None,
    success: bool = True,
    **details: Any
) -> None:
    """Log a message exchange with standardized fields."""
    log_data = {
        "direction": direction,
        "message_type": message_type,
        "success": success
    }
    
    if message_id is not None:
        log_data["message_id"] = message_id
    if method:
        log_data["method"] = method
    
    log_data.update(details)
    
    if success:
        logger.debug(f"Message {direction}: {message_type}", extra=log_data)
    else:
        logger.warning(f"Message {direction} failed: {message_type}", extra=log_data)


def log_handshake_event(
    logger: MCPLoggerAdapter,
    event: str,  # 'started', 'completed', 'failed'
    protocol_version: str = "2025-03-26",
    success: bool = True,
    **details: Any
) -> None:
    """Log a handshake event with standardized fields."""
    log_data = {
        "event": event,
        "protocol_version": protocol_version,
        "success": success
    }
    
    log_data.update(details)
    
    if success:
        logger.info(f"Handshake {event}", extra=log_data)
    else:
        logger.error(f"Handshake {event}", extra=log_data)


# Example usage and initialization
if __name__ == "__main__":
    # Configure logging
    logger = configure_logging("DEBUG", structured=True)
    
    # Create adapter with context
    adapter = get_mcp_logger(correlation_id="test-123", transport_type="stdio")
    
    # Example log messages
    adapter.info("MCP adapter initialized")
    
    log_transport_operation(
        adapter, 
        "connect", 
        "stdio", 
        success=True, 
        duration_ms=45.2
    )
    
    log_message_exchange(
        adapter,
        "sent",
        "request",
        message_id=1,
        method="initialize"
    )
    
    log_handshake_event(
        adapter,
        "completed",
        client_name="trainium-job-center"
    )