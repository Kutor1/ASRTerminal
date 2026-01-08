"""
Retry and fallback mechanisms.
"""
import asyncio
from typing import Callable, TypeVar, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryStrategy:
    """
    Retry strategy configuration.

    Supports automatic retry with configurable attempts and delay.
    """

    def __init__(self, config: dict):
        """
        Initialize retry strategy.

        Args:
            config: Configuration dictionary with keys:
                - enabled (bool): Whether retry is enabled
                - max_retries (int): Maximum number of retries
                - retry_delay (float): Delay between retries in seconds
        """
        self.enabled = config.get('enabled', True)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)

    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                if not self.enabled:
                    raise

                logger.warning(
                    f"Execution failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)

        logger.error(f"All retries failed: {last_exception}")
        raise last_exception


class EngineFallback:
    """
    Engine fallback strategy.

    Automatically switches to backup engine when primary engine fails.
    """

    def __init__(self, priority_engines: list[str]):
        """
        Initialize fallback strategy.

        Args:
            priority_engines: List of engine names in priority order
        """
        self.priority_engines = priority_engines
        self.current_index = 0

    def get_next_engine(self) -> Optional[str]:
        """
        Get next backup engine.

        Returns:
            Next engine name or None if no more engines
        """
        self.current_index += 1

        if self.current_index < len(self.priority_engines):
            return self.priority_engines[self.current_index]

        return None

    def reset(self) -> None:
        """Reset to primary engine."""
        self.current_index = 0


class CircuitBreaker:
    """
    Circuit breaker pattern.

    Prevents cascading failures by temporarily disabling failing engines.
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures: dict[str, int] = {}
        self.last_failure_time: dict[str, float] = {}

    def record_failure(self, engine: str) -> None:
        """
        Record a failure for an engine.

        Args:
            engine: Engine name
        """
        self.failures[engine] = self.failures.get(engine, 0) + 1
        try:
            self.last_failure_time[engine] = asyncio.get_event_loop().time()
        except RuntimeError:
            # No event loop
            import time
            self.last_failure_time[engine] = time.time()

    def record_success(self, engine: str) -> None:
        """
        Record a success for an engine.

        Args:
            engine: Engine name
        """
        self.failures[engine] = 0

    def is_open(self, engine: str) -> bool:
        """
        Check if circuit breaker is open for an engine.

        Args:
            engine: Engine name

        Returns:
            True if circuit is open (should not use this engine)
        """
        failures = self.failures.get(engine, 0)

        if failures >= self.failure_threshold:
            # Check if timeout has passed
            last_time = self.last_failure_time.get(engine, 0)

            try:
                current_time = asyncio.get_event_loop().time()
            except RuntimeError:
                import time
                current_time = time.time()

            if current_time - last_time < self.timeout:
                return True
            else:
                # Timeout has passed, reset
                self.failures[engine] = 0

        return False
