"""Centralized LLM inference service using direct OpenAI API.

This module provides a single interface for all LLM inference calls,
using the OpenAI API directly instead of OpenSearch ML connector.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from opensearchpy import OpenSearch
import openai

from config.config import Config


class LLMInferenceService:
    """
    Centralized service for LLM inference using direct OpenAI API.
    
    This service:
    - Uses OpenAI API directly (no OpenSearch ML connector needed)
    - Provides a unified interface for LLM calls
    - Handles errors and retries
    - Logs all LLM interactions
    """
    
    def __init__(
        self,
        config: Config,
        opensearch_client: OpenSearch,
        logger: logging.Logger,
        model_id: Optional[str] = None
    ):
        """
        Initialize the LLM inference service.
        
        Args:
            config: Configuration object
            opensearch_client: OpenSearch client (kept for compatibility)
            logger: Logger instance
            model_id: Optional model ID (not used, kept for compatibility)
        """
        self.config = config
        self.client = opensearch_client
        self.logger = logger
        
        # Initialize OpenAI client
        openai.api_key = config.llm_api_key
        self.model_name = config.llm_model
        self.logger.info(f"📋 Initialized OpenAI client with model: {self.model_name}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using the LLM via OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (default: helpful assistant)
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            
        Returns:
            Generated text
        """
        if system_prompt is None:
            system_prompt = "You are a helpful assistant."
        
        if temperature is None:
            temperature = self.config.llm_temperature
        
        if max_tokens is None:
            max_tokens = self.config.llm_max_tokens
        
        self.logger.info("=" * 80)
        self.logger.info(f"🤖 Using OpenAI Model: {self.model_name}")
        self.logger.info(f"🌡️  Temperature: {temperature} | 📊 Max tokens: {max_tokens}")
        self.logger.info("=" * 80)
        
        # Log the exact input - CLEAR AND VISIBLE
        self.logger.info("\n" + "🔵" * 40)
        self.logger.info("📥 EXACT LLM INPUT (SYSTEM + USER PROMPT)")
        self.logger.info("🔵" * 40)
        self.logger.info(f"\n[SYSTEM PROMPT]\n{system_prompt}\n")
        self.logger.info(f"[USER PROMPT]\n{prompt}\n")
        self.logger.info("🔵" * 40 + "\n")
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            self.logger.info("⏳ Calling OpenAI API...")
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract text from response
            text = response.choices[0].message.content.strip()
            
            # Log the exact output - CLEAR AND VISIBLE
            self.logger.info("\n" + "🟢" * 40)
            self.logger.info("📤 EXACT LLM OUTPUT")
            self.logger.info("🟢" * 40)
            self.logger.info(f"\n{text}\n")
            self.logger.info("🟢" * 40 + "\n")
            
            return text
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI API call failed: {str(e)}")
            raise
def generate_with_context(
    self,
    query: str,
    document_context: str,
    drawing_objects_json: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:

    if system_prompt is None:
        system_prompt = (
            "You are an AI agent that answers questions by combining "
            "persistent document knowledge with session-specific drawing data. "
            "You must always consider the drawing objects when provided. "
            "Reason internally step by step, but do not reveal your chain-of-thought. "
            "Provide a clear answer with justification."
        )

    prompt = f"""
--- PERSISTENT DOCUMENT CONTEXT ---
{document_context}

--- CURRENT DRAWING OBJECTS (JSON) ---
{drawing_objects_json}

--- USER QUESTION ---
{query}

INSTRUCTIONS:
- Use BOTH the document context and the drawing objects
- Perform any necessary measurements or comparisons
- Cite relevant rules when applicable
- If insufficient information is available, state that clearly

FINAL ANSWER:
"""

    return self.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens
    )

    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            
        Returns:
            Parsed JSON dictionary
        """
        if system_prompt is None:
            system_prompt = "You are a helpful assistant that always responds with valid JSON."
        
        text = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract JSON from markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        import json
        return json.loads(text)
    
    def is_available(self) -> bool:
        """
        Check if LLM inference is available and ready.
        
        Returns:
            True if OpenAI API key is configured, False otherwise
        """
        try:
            return bool(self.config.llm_api_key)
        except Exception as e:
            self.logger.debug(f"LLM inference not available: {e}")
            return False
