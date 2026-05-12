"""
Operational Failure Hardening for MemLayer.
Provides circuit breakers, retries, and backpressure handling.
"""

import time
import logging
import asyncio
from typing import Callable, Any, Dict, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Simple circuit breaker for provider and database calls."""
    
    def __init__(self, name: str, threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.threshold = threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def record_failure(self):
        """Record a call failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.state = "OPEN"
            logger.error(f"Circuit Breaker {self.name} is now OPEN")

    def record_success(self):
        """Record a successful call."""
        self.failure_count = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                return True
            return False
            
        return True  # HALF-OPEN allows one trial call

class FailureHardening:
    """
    Standard failure hardening policies for the MemLayer runtime.
    """

    # --- Provider Retry Policy ---
    @staticmethod
    def provider_retry_policy():
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((TimeoutError, ConnectionError)),
            reraise=True
        )

    # --- Database Retry Policy ---
    @staticmethod
    def db_retry_policy():
        return retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=0.5, min=1, max=5),
            retry=retry_if_exception_type((Exception)), # Should be more specific in production
            reraise=True
        )

# Global circuit breakers
provider_breaker = CircuitBreaker("LLM_Provider")
db_breaker = CircuitBreaker("PostgreSQL")

async def execute_with_protection(func: Callable, *args, **kwargs) -> Any:
    """Execute a function with circuit breaker protection."""
    if not provider_breaker.can_execute():
        raise RuntimeError("LLM Provider circuit breaker is OPEN. Service degraded.")
    
    try:
        result = await func(*args, **kwargs)
        provider_breaker.record_success()
        return result
    except Exception as e:
        provider_breaker.record_failure()
        raise e
