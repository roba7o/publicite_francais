import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from article_scrapers.utils.logger import get_logger

logger = get_logger(__name__)


class CircuitBreaker:
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
    def __init__(self, health_monitor: SourceHealthMonitor):
        self.health_monitor = health_monitor

    def should_skip_source(self, source_name: str) -> bool:
        """Decide if a source should be skipped based on health"""
        if not self.health_monitor.is_source_healthy(source_name):
            logger.warning(f"Skipping unhealthy source: {source_name}")
            return True
        return False

    def get_reduced_url_count(self, source_name: str, original_count: int) -> int:
        """Reduce URL count for struggling sources"""
        success_rate = self.health_monitor.get_success_rate(source_name)

        if success_rate < 0.7:
            reduced_count = max(1, int(original_count * success_rate))
            logger.info(
                f"Reducing URL count for {source_name} from {original_count} to {reduced_count}"
            )
            return reduced_count

        return original_count

    def get_adaptive_delay(self, source_name: str, base_delay: float) -> float:
        """Increase delay for sources with poor performance"""
        stats = self.health_monitor.source_stats.get(source_name, {})
        consecutive_failures = stats.get("consecutive_failures", 0)

        if consecutive_failures > 0:
            adaptive_delay = base_delay * (1 + consecutive_failures * 0.5)
            logger.debug(f"Adaptive delay for {source_name}: {adaptive_delay}s")
            return adaptive_delay

        return base_delay


# Global instances for the application
health_monitor = SourceHealthMonitor()
graceful_degradation = GracefulDegradation(health_monitor)
retry_handler = RetryHandler()
