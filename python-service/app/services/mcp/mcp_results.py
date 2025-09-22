"""MCP Result Normalizer.

This module provides utilities for normalizing MCP tool execution results
to consistent formats for easier processing and error handling.
"""

from typing import Dict, Any, Union, Optional, List
import json
import logging

logger = logging.getLogger(__name__)


class ResultNormalizer:
    """Normalizes tool execution results to consistent format."""
    
    @staticmethod
    def normalize_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MCP tool result to consistent format.
        
        Args:
            raw_result: Raw MCP tool call response
            
        Returns:
            Normalized result with consistent structure:
            {
                "success": bool,
                "content": str,
                "raw_content": List[Dict],
                "error": Optional[str],
                "metadata": Dict[str, Any]
            }
        """
        try:
            # Extract content array
            content_items = raw_result.get("content", [])
            if not isinstance(content_items, list):
                content_items = [content_items] if content_items else []
            
            # Check if this is an error response
            is_error = raw_result.get("isError", False)
            
            # Extract text content
            text_content = ResultNormalizer.extract_text_content(raw_result)
            
            # Extract error details if present
            error_message = None
            if is_error:
                error_message = ResultNormalizer.extract_error_details(raw_result)
                if not error_message and text_content:
                    error_message = text_content
            
            # Build normalized result
            normalized = {
                "success": not is_error,
                "content": text_content,
                "raw_content": content_items,
                "error": error_message,
                "metadata": {
                    "content_count": len(content_items),
                    "content_types": [item.get("type", "unknown") for item in content_items],
                    "has_annotations": any("annotations" in item for item in content_items),
                    "original_keys": list(raw_result.keys())
                }
            }
            
            # Add any additional metadata from the response
            for key, value in raw_result.items():
                if key not in ["content", "isError"]:
                    normalized["metadata"][f"original_{key}"] = value
            
            logger.debug(f"Normalized result: success={normalized['success']}, content_length={len(text_content)}")
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing result: {e}")
            return {
                "success": False,
                "content": "",
                "raw_content": [],
                "error": f"Failed to normalize result: {e}",
                "metadata": {
                    "normalization_error": str(e),
                    "original_result": raw_result
                }
            }
    
    @staticmethod
    def extract_text_content(result: Dict[str, Any]) -> str:
        """Extract text content from MCP result.
        
        Args:
            result: MCP tool call response
            
        Returns:
            Concatenated text content from all text-type content items
        """
        try:
            content_items = result.get("content", [])
            if not isinstance(content_items, list):
                content_items = [content_items] if content_items else []
            
            text_parts = []
            for item in content_items:
                if not isinstance(item, dict):
                    continue
                    
                content_type = item.get("type", "")
                
                if content_type == "text":
                    text = item.get("text", "")
                    if text:
                        text_parts.append(str(text))
                elif content_type == "resource":
                    # Handle resource references
                    resource_text = item.get("resource", {}).get("text", "")
                    if resource_text:
                        text_parts.append(str(resource_text))
                elif content_type == "tool_result":
                    # Handle nested tool results
                    tool_text = item.get("text", "")
                    if tool_text:
                        text_parts.append(str(tool_text))
                else:
                    # Try to extract text from unknown content types
                    for text_key in ["text", "content", "message", "value"]:
                        if text_key in item:
                            text_value = item[text_key]
                            if text_value and isinstance(text_value, (str, int, float)):
                                text_parts.append(str(text_value))
                                break
            
            result_text = "\n".join(text_parts).strip()
            logger.debug(f"Extracted text content: {len(result_text)} characters from {len(content_items)} items")
            
            return result_text
            
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return ""
    
    @staticmethod
    def extract_error_details(result: Dict[str, Any]) -> Optional[str]:
        """Extract error information if present.
        
        Args:
            result: MCP tool call response
            
        Returns:
            Error message if found, None otherwise
        """
        try:
            # Check if explicitly marked as error
            if not result.get("isError", False):
                return None
            
            # Try to extract error message from content
            content_items = result.get("content", [])
            if not isinstance(content_items, list):
                content_items = [content_items] if content_items else []
            
            error_messages = []
            
            for item in content_items:
                if not isinstance(item, dict):
                    continue
                
                # Look for error-specific content
                if item.get("type") == "error":
                    error_msg = item.get("message", item.get("text", ""))
                    if error_msg:
                        error_messages.append(str(error_msg))
                elif item.get("type") == "text":
                    # For text content in error responses, consider it an error message
                    text = item.get("text", "")
                    if text:
                        error_messages.append(str(text))
            
            # Also check for top-level error fields
            for error_key in ["error", "errorMessage", "message"]:
                if error_key in result:
                    error_value = result[error_key]
                    if error_value and isinstance(error_value, (str, dict)):
                        if isinstance(error_value, dict):
                            # Try to extract message from error object
                            error_msg = error_value.get("message", str(error_value))
                        else:
                            error_msg = str(error_value)
                        error_messages.append(error_msg)
            
            if error_messages:
                combined_error = "; ".join(error_messages)
                logger.debug(f"Extracted error details: {combined_error}")
                return combined_error
            
            # If no specific error found but marked as error, return generic message
            return "Tool execution failed (no specific error details available)"
            
        except Exception as e:
            logger.error(f"Error extracting error details: {e}")
            return f"Error processing failed result: {e}"
    
    @staticmethod
    def validate_tool_response(response: Dict[str, Any]) -> bool:
        """Validate that a response follows MCP tool call format.
        
        Args:
            response: Response to validate
            
        Returns:
            True if response is valid MCP tool call response
        """
        try:
            # Must have content field
            if "content" not in response:
                return False
            
            content = response["content"]
            
            # Content must be a list
            if not isinstance(content, list):
                return False
            
            # Each content item should be a dict with type
            for item in content:
                if not isinstance(item, dict):
                    return False
                if "type" not in item:
                    return False
            
            # isError field, if present, must be boolean
            if "isError" in response and not isinstance(response["isError"], bool):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating tool response: {e}")
            return False
    
    @staticmethod
    def create_error_result(error_message: str, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a normalized error result.
        
        Args:
            error_message: Error message to include
            tool_name: Optional tool name for context
            
        Returns:
            Normalized error result
        """
        return {
            "success": False,
            "content": error_message,
            "raw_content": [
                {
                    "type": "text",
                    "text": error_message
                }
            ],
            "error": error_message,
            "metadata": {
                "content_count": 1,
                "content_types": ["text"],
                "has_annotations": False,
                "tool_name": tool_name,
                "error_created": True
            }
        }
    
    @staticmethod
    def create_success_result(content: str, raw_content: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a normalized success result.
        
        Args:
            content: Text content
            raw_content: Optional raw content items
            
        Returns:
            Normalized success result
        """
        if raw_content is None:
            raw_content = [{"type": "text", "text": content}]
        
        return {
            "success": True,
            "content": content,
            "raw_content": raw_content,
            "error": None,
            "metadata": {
                "content_count": len(raw_content),
                "content_types": [item.get("type", "unknown") for item in raw_content],
                "has_annotations": any("annotations" in item for item in raw_content),
                "success_created": True
            }
        }