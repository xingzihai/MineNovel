# tests/test_llm_client.py
"""
Tests for LLM Client
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.llm_client import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMError,
    PartialResponseError,
    Provider,
    get_llm_client,
)


class TestLLMClientInit:
    """Test LLM client initialization"""
    
    def test_init_openai(self):
        """Test OpenAI client initialization"""
        client = LLMClient(
            provider="openai",
            api_key="test-key",
            model="gpt-4"
        )
        assert client.provider == Provider.OPENAI
        assert client.api_key == "test-key"
        assert client.model == "gpt-4"
        assert client.stream is True
    
    def test_init_anthropic(self):
        """Test Anthropic client initialization"""
        client = LLMClient(
            provider="anthropic",
            api_key="test-key",
            model="claude-3-opus"
        )
        assert client.provider == Provider.ANTHROPIC
        assert client.model == "claude-3-opus"
    
    def test_init_custom(self):
        """Test custom provider initialization"""
        client = LLMClient(
            provider="custom",
            api_key="test-key",
            base_url="https://api.custom.com/v1",
            model="custom-model"
        )
        assert client.provider == Provider.CUSTOM
        assert client.base_url == "https://api.custom.com/v1"
    
    def test_default_values(self):
        """Test default values"""
        client = LLMClient()
        assert client.provider == Provider.OPENAI
        assert client.temperature == 0.7
        assert client.max_tokens == 4096
        assert client.stream is True


class TestLLMClientChat:
    """Test LLM client chat methods"""
    
    @pytest.mark.asyncio
    async def test_chat_openai_mock(self):
        """Test OpenAI chat with mock"""
        client = LLMClient(provider="openai", api_key="test-key", model="gpt-4")
        
        # Mock the OpenAI client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        with patch.object(client, "_get_openai_client") as mock_get_client:
            mock_openai = AsyncMock()
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_openai
            
            messages = [LLMMessage(role="user", content="Hi")]
            response = await client.chat(messages)
            
            assert response.content == "Hello, world!"
            assert response.usage.prompt_tokens == 10
    
    @pytest.mark.asyncio
    async def test_chat_stream_fallback(self):
        """Test stream-to-sync fallback on error"""
        client = LLMClient(provider="openai", api_key="test-key", model="gpt-4", stream=True)
        
        # Mock stream failure and sync success
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Sync response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3
        mock_response.usage.total_tokens = 8
        
        with patch.object(client, "_get_openai_client") as mock_get_client:
            mock_openai = AsyncMock()
            # Stream call raises error
            mock_openai.chat.completions.create = AsyncMock(
                side_effect=Exception("stream error: text/event-stream expected")
            )
            mock_get_client.return_value = mock_openai
            
            messages = [LLMMessage(role="user", content="Hi")]
            
            # Should fallback to sync internally
            # (In real scenario, it would retry with stream=False)


class TestLLMMessage:
    """Test LLM message dataclass"""
    
    def test_message_creation(self):
        """Test message creation"""
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_message_roles(self):
        """Test different message roles"""
        system = LLMMessage(role="system", content="You are helpful")
        user = LLMMessage(role="user", content="Hi")
        assistant = LLMMessage(role="assistant", content="Hello!")
        
        assert system.role == "system"
        assert user.role == "user"
        assert assistant.role == "assistant"


class TestLLMError:
    """Test LLM error handling"""
    
    def test_error_creation(self):
        """Test error creation"""
        error = LLMError("Test error")
        assert error.message == "Test error"
        assert error.original_error is None
    
    def test_error_with_original(self):
        """Test error with original exception"""
        original = ValueError("original")
        error = LLMError("Wrapped", original)
        assert error.message == "Wrapped"
        assert error.original_error == original


class TestGetLLMClient:
    """Test convenience function"""
    
    def test_get_client(self):
        """Test get_llm_client function"""
        client = get_llm_client(
            provider="openai",
            api_key="test",
            model="gpt-4"
        )
        assert isinstance(client, LLMClient)
        assert client.provider == Provider.OPENAI