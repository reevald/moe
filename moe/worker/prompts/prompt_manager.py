"""
Langfuse Prompt Manager with Caching.

This module handles fetching prompts from Langfuse with periodic refresh.
Prompts are cached in memory and refreshed every hour.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Optional

from langfuse import Langfuse

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Manages Langfuse prompts with in-memory caching.
    
    Features:
    - Fetches prompts from Langfuse on first use
    - Caches prompts in memory
    - Automatically refreshes cache every hour
    - Thread-safe access to cached prompts
    """
    
    REFRESH_INTERVAL = 3600  # 1 hour in seconds
    
    def __init__(
        self,
        langfuse_secret_key: str,
        langfuse_public_key: str,
        langfuse_base_url: str
    ):
        """
        Initialize Prompt Manager.
        
        Args:
            langfuse_secret_key: Langfuse secret key
            langfuse_public_key: Langfuse public key
            langfuse_base_url: Langfuse base URL
        """
        self.langfuse = Langfuse(
            secret_key=langfuse_secret_key,
            public_key=langfuse_public_key,
            host=langfuse_base_url
        )
        
        self._cache: dict[str, Any] = {}
        self._last_refresh: Optional[datetime] = None
        self._lock = threading.Lock()
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        
        logger.info("PromptManager initialized")
    
    def start_auto_refresh(self) -> None:
        """
        Start background thread for automatic prompt refresh.
        """
        if self._refresh_thread and self._refresh_thread.is_alive():
            logger.warning("Auto-refresh already running")
            return
        
        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_loop,
            daemon=True
        )
        self._refresh_thread.start()
        logger.info("Started auto-refresh thread")
    
    def stop_auto_refresh(self) -> None:
        """
        Stop background auto-refresh thread.
        """
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._stop_refresh.set()
            self._refresh_thread.join(timeout=5)
            logger.info("Stopped auto-refresh thread")
    
    def _auto_refresh_loop(self) -> None:
        """
        Background loop that refreshes prompts periodically.
        """
        while not self._stop_refresh.is_set():
            try:
                # Check if refresh is needed
                if self._should_refresh():
                    logger.info("Auto-refreshing prompts...")
                    self._fetch_all_prompts()
                    logger.info("Auto-refresh completed")
            except Exception as e:
                logger.error(f"Error in auto-refresh: {e}")
            
            # Wait for refresh interval or stop signal
            self._stop_refresh.wait(timeout=self.REFRESH_INTERVAL)
    
    def _should_refresh(self) -> bool:
        """
        Check if cache should be refreshed.
        
        Returns:
            bool: True if refresh is needed
        """
        if not self._cache:
            return True
        
        if self._last_refresh is None:
            return True
        
        elapsed = datetime.utcnow() - self._last_refresh
        return elapsed > timedelta(seconds=self.REFRESH_INTERVAL)
    
    def _fetch_all_prompts(self) -> None:
        """
        Fetch all required prompts from Langfuse.
        
        Required prompts:
        - guardrail_check
        - latex_to_lean
        - feedback_generation
        """
        prompt_names = [
            "guardrail_check",
            "latex_to_lean",
            "feedback_generation"
        ]
        
        with self._lock:
            new_cache = {}
            
            for prompt_name in prompt_names:
                try:
                    prompt = self.langfuse.get_prompt(prompt_name)
                    new_cache[prompt_name] = prompt
                    logger.debug(f"Fetched prompt: {prompt_name}")
                except Exception as e:
                    logger.error(
                        f"Failed to fetch prompt {prompt_name}: {e}"
                    )
                    # Keep old version if fetch fails
                    if prompt_name in self._cache:
                        new_cache[prompt_name] = self._cache[prompt_name]
                        logger.info(
                            f"Using cached version of {prompt_name}"
                        )
            
            # Update cache
            self._cache = new_cache
            self._last_refresh = datetime.utcnow()
            
            logger.info(
                f"Prompt cache updated: {len(self._cache)} prompts"
            )
    
    def get_prompt(self, prompt_name: str) -> Any:
        """
        Get a prompt from cache.
        
        Args:
            prompt_name: Name of the prompt
        
        Returns:
            Langfuse prompt object
        
        Raises:
            ValueError: If prompt not found
        """
        # Ensure cache is populated
        if not self._cache:
            logger.info("Cache empty, fetching prompts...")
            self._fetch_all_prompts()
        
        with self._lock:
            if prompt_name not in self._cache:
                raise ValueError(
                    f"Prompt '{prompt_name}' not found in cache. "
                    f"Available: {list(self._cache.keys())}"
                )
            
            return self._cache[prompt_name]
    
    def get_prompt_template(self, prompt_name: str) -> str:
        """
        Get prompt template string.
        
        Args:
            prompt_name: Name of the prompt
        
        Returns:
            str: Prompt template
        """
        prompt = self.get_prompt(prompt_name)
        return prompt.prompt
    
    def compile_prompt(
        self,
        prompt_name: str,
        **variables
    ) -> str:
        """
        Get and compile a prompt with variables.
        
        Args:
            prompt_name: Name of the prompt
            **variables: Variables to interpolate
        
        Returns:
            str: Compiled prompt
        """
        prompt = self.get_prompt(prompt_name)
        return prompt.compile(**variables)
    
    def refresh_now(self) -> None:
        """
        Force immediate refresh of prompt cache.
        """
        logger.info("Forcing prompt cache refresh...")
        self._fetch_all_prompts()
    
    def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about cache state.
        
        Returns:
            dict: Cache information
        """
        with self._lock:
            return {
                "cached_prompts": list(self._cache.keys()),
                "prompt_count": len(self._cache),
                "last_refresh": self._last_refresh.isoformat() if (
                    self._last_refresh
                ) else None,
                "refresh_interval_seconds": self.REFRESH_INTERVAL
            }


# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None
_manager_lock = threading.Lock()


def init_prompt_manager(
    langfuse_secret_key: str,
    langfuse_public_key: str,
    langfuse_base_url: str,
    auto_refresh: bool = True
) -> PromptManager:
    """
    Initialize global prompt manager.
    
    Args:
        langfuse_secret_key: Langfuse secret key
        langfuse_public_key: Langfuse public key
        langfuse_base_url: Langfuse base URL
        auto_refresh: Start auto-refresh thread
    
    Returns:
        PromptManager: Initialized prompt manager
    """
    global _prompt_manager
    
    with _manager_lock:
        if _prompt_manager is None:
            _prompt_manager = PromptManager(
                langfuse_secret_key,
                langfuse_public_key,
                langfuse_base_url
            )
            
            if auto_refresh:
                _prompt_manager.start_auto_refresh()
            
            logger.info("Global PromptManager initialized")
        
        return _prompt_manager


def get_prompt_manager() -> PromptManager:
    """
    Get global prompt manager instance.
    
    Returns:
        PromptManager: Global prompt manager
    
    Raises:
        RuntimeError: If prompt manager not initialized
    """
    if _prompt_manager is None:
        raise RuntimeError(
            "PromptManager not initialized. "
            "Call init_prompt_manager() first."
        )
    
    return _prompt_manager
