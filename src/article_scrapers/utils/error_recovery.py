"""
Advanced error recovery and resilience patterns for web scraping.

This module implements sophisticated error handling patterns to make
the scraping system robust against failures and performance issues.
Includes circuit breakers, retry logic, health monitoring, and
graceful degradation strategies.

Key Components:
- CircuitBreaker: Prevents cascading failures by temporarily stopping requests
- RetryHandler: Implements exponential backoff retry logic
- SourceHealthMonitor: Tracks success rates and performance metrics
- GracefulDegradation: Adapts behavior based on source health

These patterns work together to create a resilient system that can
handle network issues, server problems, and varying load conditions
while maintaining overall system stability.

Example:
    >>> health_monitor.record_attempt('source1', success=True, response_time=1.2)
    >>> if not graceful_degradation.should_skip_source('source1'):
    ...     result = retry_handler.execute_with_retry(some_function)
"""

import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from article_scrapers.utils.logger import get_logger

logger = get_logger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascading failures.
    
    A circuit breaker monitors failures and stops making requests to failing
    services for a specified timeout period. This prevents system overload
    and allows failing services time to recover.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    
    Attributes:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before testing recovery
        failure_count: Current count of consecutive failures
        state: Current circuit state (CLOSED, OPEN, HALF_OPEN)
    
    Example:
        >>> cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        >>> try:
        ...     result = cb.call(risky_function, arg1, arg2)
        ... except Exception:
        ...     print("Circuit breaker prevented call or function failed")
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time
            and datetime.now() - self.last_failure_time
            > timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


class RetryHandler:
    """
    Retry mechanism with exponential backoff for transient failures.
    
    Automatically retries failed operations with increasing delays between
    attempts. Useful for handling temporary network issues, server overload,
    or other transient problems.
    
    Features:
    - Configurable maximum retry attempts
    - Exponential backoff with jitter
    - Maximum delay cap to prevent excessive waits
    - Comprehensive error logging
    
    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay cap in seconds
    
    Example:
        >>> handler = RetryHandler(max_retries=3, base_delay=1.0)
        >>> result = handler.execute_with_retry(unstable_function, arg1, arg2)
        >>> if result is None:
        ...     print("All retry attempts failed")
    """
    def __init__(
        self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2**attempt), self.max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_retries + 1} attempts failed. Last error: {e}"
                    )

        return None


class SourceHealthMonitor:
    """
    Health monitoring system for tracking source performance and reliability.
    
    Continuously monitors the health of different news sources by tracking
    success rates, response times, and failure patterns. This data drives
    adaptive behavior in other system components.
    
    Tracked Metrics:
    - Success/failure rates
    - Average response times
    - Consecutive failure counts
    - Last success/failure timestamps
    - Total attempt counts
    
    Health Criteria:
    - Success rate >= 50%
    - Consecutive failures < 3
    
    Usage:
        The monitor is used by other components to make decisions about
        request routing, load balancing, and graceful degradation.
    
    Example:
        >>> monitor = SourceHealthMonitor()
        >>> monitor.record_attempt('slate.fr', success=True, response_time=1.5)
        >>> if monitor.is_source_healthy('slate.fr'):
        ...     # Proceed with normal processing
        >>> health_summary = monitor.get_health_summary()
    """
    def __init__(self):
        self.source_stats: Dict[str, Dict[str, Any]] = {}

    def record_attempt(self, source_name: str, success: bool, response_time: float = 0):
        if source_name not in self.source_stats:
            self.source_stats[source_name] = {
                "total_attempts": 0,
                "successes": 0,
                "failures": 0,
                "avg_response_time": 0,
                "last_success": None,
                "last_failure": None,
                "consecutive_failures": 0,
            }

        stats = self.source_stats[source_name]
        stats["total_attempts"] += 1

        if success:
            stats["successes"] += 1
            stats["consecutive_failures"] = 0
            stats["last_success"] = datetime.now()
            # Update rolling average response time
            stats["avg_response_time"] = (
                stats["avg_response_time"] + response_time
            ) / 2
        else:
            stats["failures"] += 1
            stats["consecutive_failures"] += 1
            stats["last_failure"] = datetime.now()

    def get_success_rate(self, source_name: str) -> float:
        if source_name not in self.source_stats:
            return 1.0

        stats = self.source_stats[source_name]
        if stats["total_attempts"] == 0:
            return 1.0

        return stats["successes"] / stats["total_attempts"]

    def is_source_healthy(self, source_name: str) -> bool:
        if source_name not in self.source_stats:
            return True

        stats = self.source_stats[source_name]
        success_rate = self.get_success_rate(source_name)

        # Consider unhealthy if success rate < 50% and more than 3 consecutive failures
        return success_rate >= 0.5 and stats["consecutive_failures"] < 3

    def get_health_summary(self) -> Dict[str, Any]:
        summary = {}
        for source_name, stats in self.source_stats.items():
            summary[source_name] = {
                "success_rate": self.get_success_rate(source_name),
                "healthy": self.is_source_healthy(source_name),
                "consecutive_failures": stats["consecutive_failures"],
                "avg_response_time": stats["avg_response_time"],
            }
        return summary


class GracefulDegradation:
    """
    Graceful degradation strategies based on source health monitoring.
    
    Implements adaptive behavior that reduces load on struggling sources
    while maintaining overall system functionality. Uses health metrics
    to make intelligent decisions about request patterns and resource allocation.
    
    Strategies:
    - Skip unhealthy sources temporarily
    - Reduce URL count for struggling sources
    - Increase delays for sources with performance issues
    - Early termination on high failure rates
    
    This approach ensures the system remains functional even when some
    sources are experiencing problems, rather than failing completely.
    
    Example:
        >>> degradation = GracefulDegradation(health_monitor)
        >>> if not degradation.should_skip_source('problematic-source'):
        ...     url_count = degradation.get_reduced_url_count('source', 100)
        ...     delay = degradation.get_adaptive_delay('source', 1.0)
    """
    def __init__(self, health_monitor: SourceHealthMonitor):
        self.health_monitor = health_monitor

    def should_skip_source(self, source_name: str) -> bool:
        """
        Decide if a source should be skipped based on health metrics.
        
        Args:
            source_name: Name of the news source to evaluate
            
        Returns:
            True if the source should be skipped, False otherwise
            
        The decision is based on the source's health status as determined
        by success rates and consecutive failure counts.
        """
        if not self.health_monitor.is_source_healthy(source_name):
            logger.warning(f"Skipping unhealthy source: {source_name}")
            return True
        return False

    def get_reduced_url_count(self, source_name: str, original_count: int) -> int:
        """
        Calculate reduced URL count for sources with poor performance.
        
        Reduces the number of URLs to process based on the source's
        success rate, helping to reduce load on struggling sources.
        
        Args:
            source_name: Name of the news source
            original_count: Original number of URLs to process
            
        Returns:
            Adjusted URL count (minimum 1)
            
        Formula: reduced_count = max(1, original_count * success_rate)
        Applied when success_rate < 0.7
        """
        success_rate = self.health_monitor.get_success_rate(source_name)

        if success_rate < 0.7:
            reduced_count = max(1, int(original_count * success_rate))
            logger.info(
                f"Reducing URL count for {source_name} from {original_count} to {reduced_count}"
            )
            return reduced_count

        return original_count

    def get_adaptive_delay(self, source_name: str, base_delay: float) -> float:
        """
        Calculate adaptive delay based on source performance.
        
        Increases request delays for sources experiencing consecutive
        failures to reduce load and give them time to recover.
        
        Args:
            source_name: Name of the news source
            base_delay: Base delay in seconds
            
        Returns:
            Adjusted delay in seconds
            
        Formula: adaptive_delay = base_delay * (1 + consecutive_failures * 0.5)
        """
        stats = self.health_monitor.source_stats.get(source_name, {})
        consecutive_failures = stats.get("consecutive_failures", 0)

        if consecutive_failures > 0:
            adaptive_delay = base_delay * (1 + consecutive_failures * 0.5)
            logger.debug(f"Adaptive delay for {source_name}: {adaptive_delay}s")
            return adaptive_delay

        return base_delay


# Global instances for the application
# These are shared across all components to maintain consistent state
health_monitor = SourceHealthMonitor()
graceful_degradation = GracefulDegradation(health_monitor)
retry_handler = RetryHandler()

# Export the main components
__all__ = [
    'CircuitBreaker',
    'RetryHandler', 
    'SourceHealthMonitor',
    'GracefulDegradation',
    'health_monitor',
    'graceful_degradation',
    'retry_handler'
]
