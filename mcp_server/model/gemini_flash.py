import google.generativeai as genai
from typing import Dict, Any, Optional, List, Literal, Union, TypeVar, Callable
import os
from functools import wraps
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T')

class ModelError(Exception):
    """Custom exception for model-related errors"""
    pass

def fallback_to_15_flash(method: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to automatically fall back to 1.5 if 2.0 fails.
    Only applies when the instance's version is '2.0'.
    """
    @wraps(method)
    async def wrapper(self: 'GeminiFlash', *args: Any, **kwargs: Any) -> T:
        if self.version != '2.0' or not self._should_fallback:
            return await method(self, *args, **kwargs)
            
        try:
            return await method(self, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Error with Gemini 2.0 Flash: {str(e)}")
            
            # Only fallback if we haven't already tried 1.5
            if self.version == '2.0':
                logger.info("Falling back to Gemini 1.5 Flash...")
                fallback = GeminiFlash(version='1.5', api_key=self.api_key, _is_fallback=True)
                return await getattr(fallback, method.__name__)(*args, **kwargs)
            raise ModelError(f"Error with Gemini 1.5 Flash: {str(e)}")
    return wrapper

class GeminiFlash:
    """
    Google Gemini Flash model implementation with automatic fallback from 2.0 to 1.5.
    """
    
    SUPPORTED_VERSIONS = ['2.0', '1.5']
    
    def __init__(self, version: str = '2.0', api_key: Optional[str] = None, _is_fallback: bool = False):
        """
        Initialize the Gemini Flash model.
        
        Args:
            version: Model version ('2.0' or '1.5')
            api_key: Google AI API key. If not provided, will look for GOOGLE_API_KEY env var.
            _is_fallback: Internal flag to indicate if this is a fallback instance.
        """
        if version not in self.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version: {version}. Supported versions: {self.SUPPORTED_VERSIONS}")
            
        self.version = version
        api_key="AIzaSyC3TpRUinxSCASXncgqhD1FJ6yqAq3j9rY"
        self.api_key = api_key 
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set and no API key provided")
        
        self._should_fallback = version == '2.0' and not _is_fallback
        genai.configure(api_key=self.api_key)
        self.model_name = f'gemini-{version}-flash'
        self.model = genai.GenerativeModel(self.model_name)
    
    @fallback_to_15_flash
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        top_k: int = 40,
        **kwargs
    ) -> str:
        """
        Generate text using Gemini Flash.
        
        Args:
            prompt: The input prompt
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
            
        Raises:
            ModelError: If both 2.0 and 1.5 models fail
        """
        response = await self.model.generate_content_async(
            prompt,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens,
                'top_p': top_p,
                'top_k': top_k,
                **kwargs
            }
        )
        return response.text
    
    @fallback_to_15_flash
    async def chat(
        self,
        messages: List[Dict[Literal['role', 'content'], str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Chat completion using Gemini Flash.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Model's response
            
        Raises:
            ModelError: If both 2.0 and 1.5 models fail
        """
        chat = self.model.start_chat(history=[])
        # Process all but the last message as history
        for message in messages[:-1]:
            if message['role'] == 'user':
                chat.send_message(message['content'])
        
        # Get response for the last message
        response = await chat.send_message_async(
            messages[-1]['content'],
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens,
                **kwargs
            }
        )
        return response.text
