"""Tests for MCP logging configuration.

This module contains tests for the structured logging functionality.
"""

import json
import logging
import unittest
from io import StringIO
from unittest.mock import patch

# Import the modules we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.mcp.mcp_logging import (
    StructuredFormatter,
    MCPLoggerAdapter,
    configure_logging,
    get_mcp_logger,
    log_transport_operation,
    log_message_exchange,
    log_handshake_event
)


class TestStructuredFormatter(unittest.TestCase):
    """Test the StructuredFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = StructuredFormatter()
    
    def test_basic_formatting(self):
        """Test basic log record formatting."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "file"
        record.funcName = "test_function"
        
        formatted = self.formatter.format(record)
        
        # Parse the JSON to verify structure
        parsed = json.loads(formatted)
        
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["logger"], "test.logger")
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["module"], "file")
        self.assertEqual(parsed["function"], "test_function")
        self.assertEqual(parsed["line"], 42)
        self.assertIn("timestamp", parsed)
    
    def test_formatting_with_extra_fields(self):
        """Test formatting with extra fields."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "file"
        record.funcName = "test_function"
        
        # Add extra fields
        record.correlation_id = "test-123"
        record.transport_type = "stdio"
        
        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)
        
        self.assertIn("extra", parsed)
        self.assertEqual(parsed["extra"]["correlation_id"], "test-123")
        self.assertEqual(parsed["extra"]["transport_type"], "stdio")
    
    def test_exception_formatting(self):
        """Test formatting with exception info."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/file.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        record.module = "file"
        record.funcName = "test_function"
        
        formatted = self.formatter.format(record)
        parsed = json.loads(formatted)
        
        self.assertIn("exception", parsed)
        self.assertIn("ValueError", parsed["exception"])
        self.assertIn("Test exception", parsed["exception"])


class TestMCPLoggerAdapter(unittest.TestCase):
    """Test the MCPLoggerAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger("test.logger")
        self.logger.setLevel(logging.DEBUG)
        
        # Create string stream to capture output
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(self.handler)
        self.logger.propagate = False
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.logger.removeHandler(self.handler)
    
    def test_basic_adapter(self):
        """Test basic logger adapter functionality."""
        extra = {"correlation_id": "test-123"}
        adapter = MCPLoggerAdapter(self.logger, extra)
        
        adapter.info("Test message")
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["extra"]["correlation_id"], "test-123")
    
    def test_with_context(self):
        """Test creating adapter with additional context."""
        adapter = MCPLoggerAdapter(self.logger, {"base": "value"})
        new_adapter = adapter.with_context(additional="context")
        
        new_adapter.info("Test message")
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["extra"]["base"], "value")
        self.assertEqual(parsed["extra"]["additional"], "context")
    
    def test_process_merges_extra(self):
        """Test that process method merges extra fields correctly."""
        adapter = MCPLoggerAdapter(self.logger, {"base": "value"})
        
        adapter.info("Test message", extra={"call_specific": "data"})
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["extra"]["base"], "value")
        self.assertEqual(parsed["extra"]["call_specific"], "data")


class TestConfigureLogging(unittest.TestCase):
    """Test the configure_logging function."""
    
    def test_basic_configuration(self):
        """Test basic logging configuration."""
        logger = configure_logging("INFO", structured=True, logger_name="test.mcp")
        
        self.assertEqual(logger.name, "test.mcp")
        self.assertEqual(logger.level, logging.INFO)
        self.assertFalse(logger.propagate)
        self.assertEqual(len(logger.handlers), 1)
    
    def test_different_log_levels(self):
        """Test configuration with different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in levels:
            with self.subTest(level=level):
                logger = configure_logging(level, logger_name=f"test.{level.lower()}")
                expected_level = getattr(logging, level)
                self.assertEqual(logger.level, expected_level)
    
    def test_non_structured_logging(self):
        """Test configuration with non-structured logging."""
        logger = configure_logging("INFO", structured=False, logger_name="test.plain")
        
        # Check that handler has a different formatter
        handler = logger.handlers[0]
        self.assertNotIsInstance(handler.formatter, StructuredFormatter)
    
    def test_handler_cleanup(self):
        """Test that existing handlers are removed."""
        logger_name = "test.cleanup"
        
        # Create logger with initial handler
        logger1 = configure_logging("INFO", logger_name=logger_name)
        initial_handler_count = len(logger1.handlers)
        
        # Reconfigure the same logger
        logger2 = configure_logging("DEBUG", logger_name=logger_name)
        
        # Should still have the same number of handlers
        self.assertEqual(len(logger2.handlers), initial_handler_count)
        self.assertEqual(logger2.level, logging.DEBUG)


class TestGetMCPLogger(unittest.TestCase):
    """Test the get_mcp_logger function."""
    
    def test_basic_logger_creation(self):
        """Test basic MCP logger creation."""
        logger = get_mcp_logger("test.mcp")
        
        self.assertIsInstance(logger, MCPLoggerAdapter)
        self.assertEqual(logger.logger.name, "test.mcp")
    
    def test_logger_with_context(self):
        """Test MCP logger creation with context."""
        logger = get_mcp_logger(
            "test.mcp",
            correlation_id="test-123",
            transport_type="stdio",
            custom_field="value"
        )
        
        expected_extra = {
            "correlation_id": "test-123",
            "transport_type": "stdio",
            "custom_field": "value"
        }
        
        self.assertEqual(logger.extra, expected_extra)


class TestLoggingHelpers(unittest.TestCase):
    """Test logging helper functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger("test.helper")
        self.logger.setLevel(logging.DEBUG)
        
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(self.handler)
        self.logger.propagate = False
        
        self.adapter = MCPLoggerAdapter(self.logger, {"base": "context"})
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.logger.removeHandler(self.handler)
        self.stream.close()
    
    def test_log_transport_operation_success(self):
        """Test logging successful transport operation."""
        log_transport_operation(
            self.adapter,
            "connect",
            "stdio",
            success=True,
            duration_ms=45.2
        )
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["level"], "INFO")
        self.assertIn("Transport operation completed", parsed["message"])
        self.assertEqual(parsed["extra"]["operation"], "connect")
        self.assertEqual(parsed["extra"]["transport_type"], "stdio")
        self.assertEqual(parsed["extra"]["success"], True)
        self.assertEqual(parsed["extra"]["duration_ms"], 45.2)
    
    def test_log_transport_operation_failure(self):
        """Test logging failed transport operation."""
        log_transport_operation(
            self.adapter,
            "send",
            "stdio",
            success=False,
            error="Connection lost"
        )
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["level"], "ERROR")
        self.assertIn("Transport operation failed", parsed["message"])
        self.assertEqual(parsed["extra"]["success"], False)
        self.assertEqual(parsed["extra"]["error"], "Connection lost")
    
    def test_log_message_exchange_success(self):
        """Test logging successful message exchange."""
        log_message_exchange(
            self.adapter,
            "sent",
            "request",
            message_id=1,
            method="initialize",
            success=True
        )
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["level"], "DEBUG")
        self.assertIn("Message sent", parsed["message"])
        self.assertEqual(parsed["extra"]["direction"], "sent")
        self.assertEqual(parsed["extra"]["message_type"], "request")
        self.assertEqual(parsed["extra"]["message_id"], 1)
        self.assertEqual(parsed["extra"]["method"], "initialize")
    
    def test_log_message_exchange_failure(self):
        """Test logging failed message exchange."""
        log_message_exchange(
            self.adapter,
            "received",
            "response",
            success=False,
            error="Parse error"
        )
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["level"], "WARNING")
        self.assertIn("Message received failed", parsed["message"])
        self.assertEqual(parsed["extra"]["success"], False)
        self.assertEqual(parsed["extra"]["error"], "Parse error")
    
    def test_log_handshake_event_success(self):
        """Test logging successful handshake event."""
        log_handshake_event(
            self.adapter,
            "completed",
            protocol_version="2025-03-26",
            success=True,
            client_name="test-client"
        )
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["level"], "INFO")
        self.assertIn("Handshake completed", parsed["message"])
        self.assertEqual(parsed["extra"]["event"], "completed")
        self.assertEqual(parsed["extra"]["protocol_version"], "2025-03-26")
        self.assertEqual(parsed["extra"]["client_name"], "test-client")
    
    def test_log_handshake_event_failure(self):
        """Test logging failed handshake event."""
        log_handshake_event(
            self.adapter,
            "failed",
            success=False,
            reason="Version mismatch"
        )
        
        output = self.stream.getvalue()
        parsed = json.loads(output.strip())
        
        self.assertEqual(parsed["level"], "ERROR")
        self.assertIn("Handshake failed", parsed["message"])
        self.assertEqual(parsed["extra"]["success"], False)
        self.assertEqual(parsed["extra"]["reason"], "Version mismatch")


if __name__ == '__main__':
    unittest.main()