"""Tests for MCP message models.

This module contains tests for JSON-RPC message models and serialization.
"""

import json
import unittest
from dataclasses import FrozenInstanceError

# Import the modules we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.mcp.mcp_models import (
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcError,
    InitializeRequest,
    InitializeResponse,
    MCPCapabilities,
    ClientInfo,
    JsonRpcErrorCodes,
    create_error_response,
    create_success_response
)


class TestJsonRpcRequest(unittest.TestCase):
    """Test JsonRpcRequest model."""
    
    def test_basic_creation(self):
        """Test basic request creation."""
        request = JsonRpcRequest(method="test", id=1)
        
        self.assertEqual(request.method, "test")
        self.assertEqual(request.id, 1)
        self.assertEqual(request.jsonrpc, "2.0")
        self.assertIsNone(request.params)
    
    def test_creation_with_params(self):
        """Test request creation with parameters."""
        params = {"key": "value", "number": 42}
        request = JsonRpcRequest(method="test", id=1, params=params)
        
        self.assertEqual(request.params, params)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        request = JsonRpcRequest(method="test", id=1)
        result = request.to_dict()
        
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test"
        }
        self.assertEqual(result, expected)
    
    def test_to_dict_with_params(self):
        """Test conversion to dictionary with parameters."""
        params = {"key": "value"}
        request = JsonRpcRequest(method="test", id=1, params=params)
        result = request.to_dict()
        
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test",
            "params": params
        }
        self.assertEqual(result, expected)
    
    def test_to_json(self):
        """Test JSON serialization."""
        request = JsonRpcRequest(method="test", id=1)
        json_str = request.to_json()
        
        # Parse back to verify
        parsed = json.loads(json_str)
        self.assertEqual(parsed["method"], "test")
        self.assertEqual(parsed["id"], 1)
        self.assertEqual(parsed["jsonrpc"], "2.0")
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "test",
            "params": {"key": "value"}
        }
        request = JsonRpcRequest.from_dict(data)
        
        self.assertEqual(request.method, "test")
        self.assertEqual(request.id, 1)
        self.assertEqual(request.jsonrpc, "2.0")
        self.assertEqual(request.params, {"key": "value"})
    
    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = '{"jsonrpc": "2.0", "id": 1, "method": "test"}'
        request = JsonRpcRequest.from_json(json_str)
        
        self.assertEqual(request.method, "test")
        self.assertEqual(request.id, 1)
        self.assertEqual(request.jsonrpc, "2.0")


class TestJsonRpcError(unittest.TestCase):
    """Test JsonRpcError model."""
    
    def test_basic_creation(self):
        """Test basic error creation."""
        error = JsonRpcError(code=-32600, message="Invalid Request")
        
        self.assertEqual(error.code, -32600)
        self.assertEqual(error.message, "Invalid Request")
        self.assertIsNone(error.data)
    
    def test_creation_with_data(self):
        """Test error creation with data."""
        data = {"detail": "Missing method field"}
        error = JsonRpcError(code=-32600, message="Invalid Request", data=data)
        
        self.assertEqual(error.data, data)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        error = JsonRpcError(code=-32600, message="Invalid Request")
        result = error.to_dict()
        
        expected = {
            "code": -32600,
            "message": "Invalid Request"
        }
        self.assertEqual(result, expected)
    
    def test_to_dict_with_data(self):
        """Test conversion to dictionary with data."""
        data = {"detail": "Missing method field"}
        error = JsonRpcError(code=-32600, message="Invalid Request", data=data)
        result = error.to_dict()
        
        expected = {
            "code": -32600,
            "message": "Invalid Request",
            "data": data
        }
        self.assertEqual(result, expected)


class TestJsonRpcResponse(unittest.TestCase):
    """Test JsonRpcResponse model."""
    
    def test_success_response(self):
        """Test successful response creation."""
        result = {"status": "ok"}
        response = JsonRpcResponse(id=1, result=result)
        
        self.assertEqual(response.id, 1)
        self.assertEqual(response.result, result)
        self.assertIsNone(response.error)
        self.assertEqual(response.jsonrpc, "2.0")
    
    def test_error_response(self):
        """Test error response creation."""
        error = JsonRpcError(code=-32600, message="Invalid Request")
        response = JsonRpcResponse(id=1, error=error)
        
        self.assertEqual(response.id, 1)
        self.assertEqual(response.error, error)
        self.assertIsNone(response.result)
    
    def test_invalid_response_both_result_and_error(self):
        """Test that response cannot have both result and error."""
        result = {"status": "ok"}
        error = JsonRpcError(code=-32600, message="Invalid Request")
        
        with self.assertRaises(ValueError):
            JsonRpcResponse(id=1, result=result, error=error)
    
    def test_invalid_response_neither_result_nor_error(self):
        """Test that response must have either result or error."""
        with self.assertRaises(ValueError):
            JsonRpcResponse(id=1)
    
    def test_to_dict_success(self):
        """Test conversion to dictionary for success response."""
        result = {"status": "ok"}
        response = JsonRpcResponse(id=1, result=result)
        dict_result = response.to_dict()
        
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": result
        }
        self.assertEqual(dict_result, expected)
    
    def test_to_dict_error(self):
        """Test conversion to dictionary for error response."""
        error = JsonRpcError(code=-32600, message="Invalid Request")
        response = JsonRpcResponse(id=1, error=error)
        dict_result = response.to_dict()
        
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        self.assertEqual(dict_result, expected)
    
    def test_from_dict_success(self):
        """Test creation from dictionary for success response."""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok"}
        }
        response = JsonRpcResponse.from_dict(data)
        
        self.assertEqual(response.id, 1)
        self.assertEqual(response.result, {"status": "ok"})
        self.assertIsNone(response.error)
    
    def test_from_dict_error(self):
        """Test creation from dictionary for error response."""
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        response = JsonRpcResponse.from_dict(data)
        
        self.assertEqual(response.id, 1)
        self.assertIsNone(response.result)
        self.assertIsNotNone(response.error)
        self.assertEqual(response.error.code, -32600)
        self.assertEqual(response.error.message, "Invalid Request")


class TestClientInfo(unittest.TestCase):
    """Test ClientInfo model."""
    
    def test_creation(self):
        """Test client info creation."""
        client_info = ClientInfo(name="test-client", version="1.0.0")
        
        self.assertEqual(client_info.name, "test-client")
        self.assertEqual(client_info.version, "1.0.0")
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        client_info = ClientInfo(name="test-client", version="1.0.0")
        result = client_info.to_dict()
        
        expected = {
            "name": "test-client",
            "version": "1.0.0"
        }
        self.assertEqual(result, expected)


class TestMCPCapabilities(unittest.TestCase):
    """Test MCPCapabilities model."""
    
    def test_empty_capabilities(self):
        """Test empty capabilities creation."""
        capabilities = MCPCapabilities()
        
        self.assertIsNone(capabilities.roots)
        self.assertIsNone(capabilities.sampling)
        self.assertIsNone(capabilities.tools)
        self.assertIsNone(capabilities.resources)
        self.assertIsNone(capabilities.prompts)
        self.assertIsNone(capabilities.logging)
    
    def test_capabilities_with_values(self):
        """Test capabilities creation with values."""
        capabilities = MCPCapabilities(
            tools={"list_tools": {}},
            resources={"list_resources": {}}
        )
        
        self.assertEqual(capabilities.tools, {"list_tools": {}})
        self.assertEqual(capabilities.resources, {"list_resources": {}})
        self.assertIsNone(capabilities.roots)
    
    def test_to_dict_empty(self):
        """Test conversion to dictionary when empty."""
        capabilities = MCPCapabilities()
        result = capabilities.to_dict()
        
        self.assertEqual(result, {})
    
    def test_to_dict_with_values(self):
        """Test conversion to dictionary with values."""
        capabilities = MCPCapabilities(
            tools={"list_tools": {}},
            resources={"list_resources": {}}
        )
        result = capabilities.to_dict()
        
        expected = {
            "tools": {"list_tools": {}},
            "resources": {"list_resources": {}}
        }
        self.assertEqual(result, expected)


class TestInitializeRequest(unittest.TestCase):
    """Test InitializeRequest model."""
    
    def test_default_creation(self):
        """Test default initialize request creation."""
        request = InitializeRequest()
        
        self.assertEqual(request.protocolVersion, "2025-03-26")
        self.assertIsInstance(request.capabilities, MCPCapabilities)
        self.assertIsInstance(request.clientInfo, ClientInfo)
        self.assertEqual(request.clientInfo.name, "trainium-job-center")
    
    def test_custom_creation(self):
        """Test custom initialize request creation."""
        capabilities = MCPCapabilities(tools={"list_tools": {}})
        client_info = ClientInfo(name="custom-client", version="2.0.0")
        
        request = InitializeRequest(
            protocolVersion="2024-01-01",
            capabilities=capabilities,
            clientInfo=client_info
        )
        
        self.assertEqual(request.protocolVersion, "2024-01-01")
        self.assertEqual(request.capabilities, capabilities)
        self.assertEqual(request.clientInfo, client_info)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        request = InitializeRequest()
        result = request.to_dict()
        
        self.assertIn("protocolVersion", result)
        self.assertIn("capabilities", result)
        self.assertIn("clientInfo", result)
        self.assertEqual(result["protocolVersion"], "2025-03-26")
    
    def test_to_jsonrpc_request(self):
        """Test conversion to JSON-RPC request."""
        request = InitializeRequest()
        jsonrpc_request = request.to_jsonrpc_request(123)
        
        self.assertEqual(jsonrpc_request.method, "initialize")
        self.assertEqual(jsonrpc_request.id, 123)
        self.assertIsNotNone(jsonrpc_request.params)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""
    
    def test_create_error_response(self):
        """Test error response creation helper."""
        response = create_error_response(1, -32600, "Invalid Request")
        
        self.assertEqual(response.id, 1)
        self.assertIsNone(response.result)
        self.assertIsNotNone(response.error)
        self.assertEqual(response.error.code, -32600)
        self.assertEqual(response.error.message, "Invalid Request")
    
    def test_create_error_response_with_data(self):
        """Test error response creation helper with data."""
        data = {"detail": "Missing field"}
        response = create_error_response(1, -32600, "Invalid Request", data)
        
        self.assertEqual(response.error.data, data)
    
    def test_create_success_response(self):
        """Test success response creation helper."""
        result = {"status": "ok"}
        response = create_success_response(1, result)
        
        self.assertEqual(response.id, 1)
        self.assertEqual(response.result, result)
        self.assertIsNone(response.error)


class TestErrorCodes(unittest.TestCase):
    """Test JSON-RPC error codes."""
    
    def test_standard_error_codes(self):
        """Test standard JSON-RPC error codes."""
        self.assertEqual(JsonRpcErrorCodes.PARSE_ERROR, -32700)
        self.assertEqual(JsonRpcErrorCodes.INVALID_REQUEST, -32600)
        self.assertEqual(JsonRpcErrorCodes.METHOD_NOT_FOUND, -32601)
        self.assertEqual(JsonRpcErrorCodes.INVALID_PARAMS, -32602)
        self.assertEqual(JsonRpcErrorCodes.INTERNAL_ERROR, -32603)
    
    def test_mcp_error_codes(self):
        """Test MCP-specific error codes."""
        self.assertEqual(JsonRpcErrorCodes.HANDSHAKE_ERROR, -32000)
        self.assertEqual(JsonRpcErrorCodes.TRANSPORT_ERROR, -32001)
        self.assertEqual(JsonRpcErrorCodes.PROTOCOL_ERROR, -32002)


if __name__ == '__main__':
    unittest.main()