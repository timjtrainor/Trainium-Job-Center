"""MCP Message Models.

This module defines the data models for JSON-RPC messages used in the
Model Context Protocol (MCP) communication layer.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
import json


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 request message model."""
    
    method: str
    id: int
    jsonrpc: str = "2.0"
    params: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JsonRpcRequest':
        """Create from dictionary."""
        return cls(
            method=data["method"],
            id=data["id"],
            jsonrpc=data.get("jsonrpc", "2.0"),
            params=data.get("params")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JsonRpcRequest':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class JsonRpcError:
    """JSON-RPC 2.0 error object."""
    
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class JsonRpcResponse:
    """JSON-RPC 2.0 response message model."""
    
    id: int
    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[JsonRpcError] = None
    
    def __post_init__(self):
        """Validate that either result or error is present, but not both."""
        if self.result is not None and self.error is not None:
            raise ValueError("Response cannot have both result and error")
        if self.result is None and self.error is None:
            raise ValueError("Response must have either result or error")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        
        if self.result is not None:
            result["result"] = self.result
        elif self.error is not None:
            result["error"] = self.error.to_dict()
            
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JsonRpcResponse':
        """Create from dictionary."""
        error = None
        if "error" in data:
            error_data = data["error"]
            error = JsonRpcError(
                code=error_data["code"],
                message=error_data["message"],
                data=error_data.get("data")
            )
        
        return cls(
            id=data["id"],
            jsonrpc=data.get("jsonrpc", "2.0"),
            result=data.get("result"),
            error=error
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'JsonRpcResponse':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class ClientInfo:
    """Client information for MCP initialization."""
    
    name: str
    version: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "version": self.version
        }


@dataclass
class MCPCapabilities:
    """MCP capabilities declaration."""
    
    roots: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        
        if self.roots is not None:
            result["roots"] = self.roots
        if self.sampling is not None:
            result["sampling"] = self.sampling
        if self.tools is not None:
            result["tools"] = self.tools
        if self.resources is not None:
            result["resources"] = self.resources
        if self.prompts is not None:
            result["prompts"] = self.prompts
        if self.logging is not None:
            result["logging"] = self.logging
            
        return result


@dataclass
class InitializeRequest:
    """MCP initialize request parameters."""
    
    protocolVersion: str = "2025-03-26"
    capabilities: MCPCapabilities = field(default_factory=MCPCapabilities)
    clientInfo: ClientInfo = field(default_factory=lambda: ClientInfo("trainium-job-center", "1.0.0"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "protocolVersion": self.protocolVersion,
            "capabilities": self.capabilities.to_dict(),
            "clientInfo": self.clientInfo.to_dict()
        }
    
    def to_jsonrpc_request(self, request_id: int = 1) -> JsonRpcRequest:
        """Convert to a JSON-RPC request."""
        return JsonRpcRequest(
            method="initialize",
            id=request_id,
            params=self.to_dict()
        )


@dataclass
class ServerCapabilities:
    """Server capabilities for MCP initialization response."""
    
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    roots: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        
        if self.tools is not None:
            result["tools"] = self.tools
        if self.resources is not None:
            result["resources"] = self.resources
        if self.prompts is not None:
            result["prompts"] = self.prompts
        if self.roots is not None:
            result["roots"] = self.roots
        if self.sampling is not None:
            result["sampling"] = self.sampling
        if self.logging is not None:
            result["logging"] = self.logging
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerCapabilities':
        """Create from dictionary."""
        return cls(
            tools=data.get("tools"),
            resources=data.get("resources"),
            prompts=data.get("prompts"),
            roots=data.get("roots"),
            sampling=data.get("sampling"),
            logging=data.get("logging")
        )


@dataclass
class InitializeResponse:
    """MCP initialize response data."""
    
    protocolVersion: str
    capabilities: ServerCapabilities
    serverInfo: Dict[str, str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InitializeResponse':
        """Create from dictionary."""
        capabilities_data = data.get("capabilities", {})
        capabilities = ServerCapabilities.from_dict(capabilities_data)
        
        return cls(
            protocolVersion=data["protocolVersion"],
            capabilities=capabilities,
            serverInfo=data["serverInfo"]
        )


# Common JSON-RPC error codes
class JsonRpcErrorCodes:
    """Standard JSON-RPC error codes."""
    
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific error codes (following JSON-RPC custom error convention)
    HANDSHAKE_ERROR = -32000
    TRANSPORT_ERROR = -32001
    PROTOCOL_ERROR = -32002


def create_error_response(request_id: int, code: int, message: str, data: Optional[Any] = None) -> JsonRpcResponse:
    """Helper function to create error responses."""
    error = JsonRpcError(code=code, message=message, data=data)
    return JsonRpcResponse(id=request_id, error=error)


def create_success_response(request_id: int, result: Dict[str, Any]) -> JsonRpcResponse:
    """Helper function to create success responses."""
    return JsonRpcResponse(id=request_id, result=result)