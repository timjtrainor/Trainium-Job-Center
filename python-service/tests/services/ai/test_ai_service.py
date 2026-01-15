
import sys
from unittest.mock import MagicMock

# MOCK CONFIG BEFORE IMPORTS
# This prevents app.core.config from loading and raising errors about missing env vars
mock_config = MagicMock()
mock_settings = MagicMock()
mock_config.get_settings.return_value = mock_settings
mock_config.Settings = MagicMock
sys.modules["app.core.config"] = mock_config

# Now safe to import app modules
import pytest
from unittest.mock import patch
# Import directly from the file to avoid some __init__ side effects if possible, 
# though patching sys.modules should protect us from gemini.py importing config.
from app.services.ai.ai_service import AIService, MODEL_ALIASES, ai_service

# Test Data
MOCK_PROMPT_NAME = "test-persona"
MOCK_CONFIG = {"model": "high-reasoning", "temperature": 0.5}

@pytest.fixture
def mock_langfuse():
    with patch("app.services.ai.ai_service.get_langfuse") as mock_get:
        mock_lf_client = MagicMock()
        mock_get.return_value = mock_lf_client
        yield mock_lf_client

@pytest.fixture
def mock_litellm():
    with patch("app.services.ai.ai_service.litellm") as mock:
        yield mock

def test_execute_prompt_success(mock_langfuse, mock_litellm):
    # Setup Mock Prompt object
    mock_prompt = MagicMock()
    mock_prompt.compile.return_value = [{"role": "system", "content": "You are a test persona. Hello"}]
    mock_prompt.config = MOCK_CONFIG
    
    mock_langfuse.get_prompt.return_value = mock_prompt
    
    # Setup Mock LiteLLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="AI Response"))]
    mock_litellm.completion.return_value = mock_response

    # Execute
    result = ai_service.execute_prompt(
        prompt_name=MOCK_PROMPT_NAME,
        variables={"user_input": "Hello"},
        user_id="user123",
        metadata={"job_id": "1"}
    )

    # Verifications
    mock_langfuse.get_prompt.assert_called_with(MOCK_PROMPT_NAME, label="production")
    mock_prompt.compile.assert_called_with(user_input="Hello")
    
    # Resolved model from alias in MOCK_CONFIG ('high-reasoning')
    expected_model = MODEL_ALIASES["high-reasoning"]
    
    mock_litellm.completion.assert_called_once()
    call_kwargs = mock_litellm.completion.call_args[1]
    
    assert call_kwargs["model"] == expected_model
    assert call_kwargs["user"] == "user123"
    assert "prompt_name" in call_kwargs["metadata"]
    assert result == "AI Response"

def test_execute_prompt_json_enforcement(mock_langfuse, mock_litellm):
    mock_prompt = MagicMock()
    mock_prompt.compile.return_value = []
    mock_prompt.config = {"response_format": "json_object"}
    mock_langfuse.get_prompt.return_value = mock_prompt
    
    mock_response = MagicMock()
    # Return valid JSON string
    mock_response.choices = [MagicMock(message=MagicMock(content='{"key": "value"}'))]
    mock_litellm.completion.return_value = mock_response

    result = ai_service.execute_prompt(
        prompt_name="test-json",
        variables={}
    )
    
    assert isinstance(result, dict)
    assert result["key"] == "value"
    
    # Verify response_format was passed
    call_kwargs = mock_litellm.completion.call_args[1]
    assert call_kwargs["response_format"] == {"type": "json_object"}

def test_execute_prompt_bedrock_absk_token(mock_langfuse, mock_litellm):
    """Verify that ABSK token is moved to api_key for bedrock models."""
    mock_prompt = MagicMock()
    mock_prompt.compile.return_value = [{"role": "user", "content": "Hi"}]
    mock_prompt.config = {"model": "bedrock/us.amazon.nova-2-lite-v1:0"}
    mock_langfuse.get_prompt.return_value = mock_prompt
    
    # Mock OS environ to have ABSK secret
    with patch.dict("os.environ", {"AWS_SECRET_ACCESS_KEY": "ABSK_TEST_TOKEN"}, clear=False):
        ai_service.execute_prompt(
            prompt_name="test-bedrock",
            variables={}
        )
        
        call_kwargs = mock_litellm.completion.call_args[1]
        assert call_kwargs["model"] == "bedrock/us.amazon.nova-2-lite-v1:0"
        assert call_kwargs["api_key"] == "ABSK_TEST_TOKEN"
        # Ensure SigV4 keys are NOT passed in params if they were present
        assert "aws_access_key_id" not in call_kwargs
        assert "aws_secret_access_key" not in call_kwargs

def test_execute_prompt_bedrock_parameter_sanitation(mock_langfuse, mock_litellm):
    """Verify that extraneous keys like friendly_name are stripped for Bedrock."""
    mock_prompt = MagicMock()
    mock_prompt.compile.return_value = [{"role": "user", "content": "Hi"}]
    # Config includes metadata that Bedrock rejects
    mock_prompt.config = {
        "model": "bedrock/us.amazon.nova-2-lite-v1:0",
        "friendly_name": "My Prompt",
        "description": "A test prompt"
    }
    mock_langfuse.get_prompt.return_value = mock_prompt
    
    ai_service.execute_prompt(
        prompt_name="test-bedrock-sanitation",
        variables={}
    )
    
    call_kwargs = mock_litellm.completion.call_args[1]
    assert call_kwargs["model"] == "bedrock/us.amazon.nova-2-lite-v1:0"
    # Metadata keys should be stripped from top level
    assert "friendly_name" not in call_kwargs
    assert "description" not in call_kwargs
    
def test_execute_prompt_bedrock_json_schema_sanitation(mock_langfuse, mock_litellm):
    """Verify that top-level json_schema is stripped and moved to response_format for Bedrock."""
    mock_prompt = MagicMock()
    mock_prompt.compile.return_value = [{"role": "user", "content": "Hi"}]
    # Config includes top-level json_schema
    mock_prompt.config = {
        "model": "bedrock/us.amazon.nova-2-lite-v1:0",
        "json_schema": {"type": "object", "properties": {"foo": {"type": "string"}}}
    }
    mock_langfuse.get_prompt.return_value = mock_prompt
    
    # Mock successful JSON response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"foo": "bar"}'))]
    mock_litellm.completion.return_value = mock_response
    
    result = ai_service.execute_prompt(
        prompt_name="test-bedrock-json-sanitation",
        variables={}
    )
    
    assert result == {"foo": "bar"}
    call_kwargs = mock_litellm.completion.call_args[1]
    # Should be stripped from top level
    assert "json_schema" not in call_kwargs
    # Should be present in response_format as a Pydantic Class
    res_format = call_kwargs["response_format"]
    assert hasattr(res_format, "__pydantic_model__") or "Model" in str(res_format)
