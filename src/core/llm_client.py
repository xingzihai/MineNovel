# core/llm_client.py
"""
LLM Client Module - Multi-provider support with stream fallback

Supports:
- OpenAI (via openai library)
- Anthropic (via anthropic library)
- Custom endpoints

Features:
- Automatic stream-to-sync fallback
- Chinese error messages
- Token usage tracking
"""

from typing import Optional, Callable, List, Dict, Any, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """LLM Provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class LLMUsage:
    """Token usage statistics"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """LLM response with content and usage"""
    content: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    finish_reason: str = "stop"


@dataclass
class LLMMessage:
    """Chat message"""
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMError(Exception):
    """LLM error with friendly Chinese message"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class PartialResponseError(LLMError):
    """Stream interrupted but partial content is usable"""
    def __init__(self, partial_content: str, cause: Exception):
        self.partial_content = partial_content
        super().__init__(
            f"Stream interrupted after {len(partial_content)} chars: {cause}",
            cause
        )


# Minimum chars to consider a partial response salvageable
MIN_SALVAGEABLE_CHARS = 500


def _wrap_error(error: Exception, context: Optional[Dict[str, str]] = None) -> LLMError:
    """Convert API error to friendly Chinese message"""
    msg = str(error).lower()
    ctx = f"\n  (baseUrl: {context.get('base_url', 'unknown')}, model: {context.get('model', 'unknown')})" if context else ""
    
    if "400" in msg:
        return LLMError(
            f"API 返回 400 (请求参数错误)。可能原因：\n"
            f"  1. 模型名称不正确\n"
            f"  2. 提供方不支持某些参数（如 max_tokens、stream）\n"
            f"  3. 消息格式不兼容\n"
            f"  建议：检查模型名称或尝试关闭流式调用{ctx}",
            error
        )
    if "401" in msg:
        return LLMError(
            f"API 返回 401 (未授权)。请检查 API Key 是否正确。{ctx}",
            error
        )
    if "403" in msg:
        return LLMError(
            f"API 返回 403 (请求被拒绝)。可能原因：\n"
            f"  1. API Key 无效或过期\n"
            f"  2. 内容审查拦截\n"
            f"  3. 账户余额不足{ctx}",
            error
        )
    if "429" in msg:
        return LLMError(
            f"API 返回 429 (请求过多)。请稍后重试，或检查 API 配额。{ctx}",
            error
        )
    if "connection" in msg or "econnrefused" in msg or "enotfound" in msg:
        return LLMError(
            f"无法连接到 API 服务。可能原因：\n"
            f"  1. baseUrl 地址不正确\n"
            f"  2. 网络不通或被防火墙拦截\n"
            f"  3. API 服务暂时不可用{ctx}",
            error
        )
    
    return LLMError(str(error), error)


def _is_stream_error(error: Exception) -> bool:
    """Check if error is likely stream-related"""
    msg = str(error).lower()
    return (
        "stream" in msg or
        "text/event-stream" in msg or
        "chunked" in msg or
        "unexpected end" in msg or
        "premature close" in msg or
        "terminated" in msg or
        "econnreset" in msg or
        ("400" in msg and "content" not in msg)
    )


class LLMClient:
    """LLM Client with multi-provider support"""
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        base_url: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
    ):
        """
        Initialize LLM client
        
        Args:
            provider: "openai" | "anthropic" | "custom"
            api_key: API key
            base_url: Custom endpoint (optional)
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            stream: Use streaming by default
        """
        self.provider = Provider(provider.lower())
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream
        
        # Lazy load clients
        self._openai_client = None
        self._anthropic_client = None
        
        logger.info(f"LLMClient initialized: provider={provider}, model={model}")
    
    def _get_openai_client(self):
        """Get or create OpenAI client"""
        if self._openai_client is None:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise LLMError("请安装 openai 库: pip install openai")
        return self._openai_client
    
    def _get_anthropic_client(self):
        """Get or create Anthropic client"""
        if self._anthropic_client is None:
            try:
                from anthropic import AsyncAnthropic
                # Anthropic SDK appends /v1/ internally
                base_url = self.base_url.replace("/v1/", "").replace("/v1", "") if self.base_url else None
                self._anthropic_client = AsyncAnthropic(
                    api_key=self.api_key,
                    base_url=base_url
                )
            except ImportError:
                raise LLMError("请安装 anthropic 库: pip install anthropic")
        return self._anthropic_client
    
    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Sync chat completion
        
        Args:
            messages: List of chat messages
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            LLMResponse with content and usage
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            if self.provider == Provider.ANTHROPIC:
                return await self._chat_anthropic_sync(messages, temp, tokens)
            else:
                return await self._chat_openai_sync(messages, temp, tokens)
        except Exception as e:
            raise _wrap_error(e, {"base_url": self.base_url or "default", "model": self.model})
    
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        on_chunk: Optional[Callable[[str], None]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Stream chat completion with auto-fallback
        
        Args:
            messages: List of chat messages
            on_chunk: Callback for each chunk
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            LLMResponse with content and usage
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            if self.provider == Provider.ANTHROPIC:
                return await self._chat_anthropic_stream(messages, on_chunk, temp, tokens)
            else:
                return await self._chat_openai_stream(messages, on_chunk, temp, tokens)
        except PartialResponseError as e:
            # Return partial content
            return LLMResponse(
                content=e.partial_content,
                usage=LLMUsage(),
                finish_reason="partial"
            )
        except Exception as e:
            # Auto-fallback to sync if stream-related error
            if self.stream and _is_stream_error(e):
                logger.warning(f"Stream failed, falling back to sync: {e}")
                try:
                    if self.provider == Provider.ANTHROPIC:
                        return await self._chat_anthropic_sync(messages, temp, tokens)
                    else:
                        return await self._chat_openai_sync(messages, temp, tokens)
                except Exception as sync_error:
                    raise _wrap_error(sync_error, {"base_url": self.base_url or "default", "model": self.model})
            raise _wrap_error(e, {"base_url": self.base_url or "default", "model": self.model})
    
    async def _chat_openai_sync(
        self,
        messages: List[LLMMessage],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """OpenAI sync completion"""
        client = self._get_openai_client()
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        content = response.choices[0].message.content or ""
        if not content:
            raise LLMError("LLM 返回空响应")
        
        return LLMResponse(
            content=content,
            usage=LLMUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0
            ),
            finish_reason=response.choices[0].finish_reason or "stop"
        )
    
    async def _chat_openai_stream(
        self,
        messages: List[LLMMessage],
        on_chunk: Optional[Callable[[str], None]],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """OpenAI streaming completion"""
        client = self._get_openai_client()
        
        stream = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        chunks: List[str] = []
        prompt_tokens = 0
        completion_tokens = 0
        
        try:
            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                if delta:
                    chunks.append(delta)
                    if on_chunk:
                        on_chunk(delta)
                if chunk.usage:
                    prompt_tokens = chunk.usage.prompt_tokens
                    completion_tokens = chunk.usage.completion_tokens
        except Exception as e:
            partial = "".join(chunks)
            if len(partial) >= MIN_SALVAGEABLE_CHARS:
                raise PartialResponseError(partial, e)
            raise
        
        content = "".join(chunks)
        if not content:
            raise LLMError("LLM 返回空响应")
        
        return LLMResponse(
            content=content,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )
    
    async def _chat_anthropic_sync(
        self,
        messages: List[LLMMessage],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Anthropic sync completion"""
        client = self._get_anthropic_client()
        
        # Separate system message
        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        non_system = [m for m in messages if m.role != "system"]
        
        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_text if system_text else None,
            messages=[{"role": m.role, "content": m.content} for m in non_system],
            temperature=temperature
        )
        
        content = "".join(
            block.text for block in response.content
            if hasattr(block, "text")
        )
        if not content:
            raise LLMError("LLM 返回空响应")
        
        return LLMResponse(
            content=content,
            usage=LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            )
        )
    
    async def _chat_anthropic_stream(
        self,
        messages: List[LLMMessage],
        on_chunk: Optional[Callable[[str], None]],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Anthropic streaming completion"""
        client = self._get_anthropic_client()
        
        # Separate system message
        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        non_system = [m for m in messages if m.role != "system"]
        
        stream = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_text if system_text else None,
            messages=[{"role": m.role, "content": m.content} for m in non_system],
            temperature=temperature,
            stream=True
        )
        
        chunks: List[str] = []
        prompt_tokens = 0
        completion_tokens = 0
        
        try:
            async for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        text = event.delta.text
                        chunks.append(text)
                        if on_chunk:
                            on_chunk(text)
                elif event.type == "message_start":
                    prompt_tokens = event.message.usage.input_tokens
                elif event.type == "message_delta":
                    if hasattr(event.usage, "output_tokens"):
                        completion_tokens = event.usage.output_tokens
        except Exception as e:
            partial = "".join(chunks)
            if len(partial) >= MIN_SALVAGEABLE_CHARS:
                raise PartialResponseError(partial, e)
            raise
        
        content = "".join(chunks)
        if not content:
            raise LLMError("LLM 返回空响应")
        
        return LLMResponse(
            content=content,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings (OpenAI only)
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if self.provider == Provider.ANTHROPIC:
            raise LLMError("Anthropic does not support embeddings")
        
        client = self._get_openai_client()
        
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        return response.data[0].embedding


# Convenience function
def get_llm_client(
    provider: str = "openai",
    api_key: str = "",
    base_url: Optional[str] = None,
    model: str = "gpt-4",
    **kwargs
) -> LLMClient:
    """Create LLM client instance"""
    return LLMClient(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        **kwargs
    )