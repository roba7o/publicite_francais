# Enhanced Logging System Examples

This document demonstrates the capabilities of the new structured logging system implemented in the French article scraper.

## Quick Start

### Basic Setup
```python
from article_scrapers.utils.structured_logger import get_structured_logger
from article_scrapers.utils.logging_config_enhanced import setup_logging

# Initialize logging (done automatically in main.py)
setup_logging(level="INFO", console_format="human")

# Get a logger for your module
logger = get_structured_logger(__name__)
```

### Basic Logging with Context
```python
# Simple message
logger.info("Processing started")

# Message with structured context
logger.info("Article processing completed", extra_data={
    "source": "slate.fr",
    "articles_processed": 25,
    "success_rate_percent": 88.5,
    "processing_time_seconds": 12.3
})
```

## Performance Tracking

### Using Timer Context Manager
```python
# Time an operation with context
with logger.performance.timer("url_fetch", {"url": "https://example.com", "source": "slate.fr"}):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

# Output: [INFO] Performance: url_fetch completed in 245.67ms | url=https://example.com source=slate.fr
```

### Manual Timer Control
```python
# Start a timer
logger.performance.start_timer("batch_processing")

# Process multiple items
for item in items:
    process_item(item)

# End timer with context
duration = logger.performance.end_timer("batch_processing", {
    "items_processed": len(items),
    "batch_size": 100
})
```

## Error Handling and Debugging

### Error Logging with Context
```python
try:
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed", extra_data={
        "operation": "data_processing",
        "input_size": len(data),
        "error_type": type(e).__name__,
        "recoverable": False
    }, exc_info=True)  # Include stack trace
```

### Warning with Degradation Info
```python
if success_rate < 0.5:
    logger.warning("Low success rate detected", extra_data={
        "source": source_name,
        "success_rate_percent": round(success_rate * 100, 1),
        "threshold_percent": 50,
        "action": "reducing_load"
    })
```

## Configuration Examples

### Development Mode
```python
from article_scrapers.utils.logging_config_enhanced import configure_development_logging

# Enable detailed debugging with human-readable output
configure_development_logging()
```

### Production Mode
```python
from article_scrapers.utils.logging_config_enhanced import configure_production_logging

# Structured JSON logging for aggregation systems
configure_production_logging()
```

### Custom Component Levels
```python
from article_scrapers.utils.logging_config_enhanced import configure_component_logging

# Set specific log levels for different components
configure_component_logging({
    "article_scrapers.core": "DEBUG",        # Detailed core processing
    "article_scrapers.parsers": "INFO",     # Standard parser info
    "article_scrapers.utils.csv_writer": "WARNING",  # Only warnings/errors
    "requests": "ERROR"                      # External library errors only
})
```

## Real-World Output Examples

### Successful Processing
```
[INFO] 2025-07-13 16:37:40 | core.processor | Source processing completed | source=Slate.fr articles_processed=25 articles_attempted=30 success_rate_percent=83.3 processing_time_seconds=12.45 articles_per_second=2.01

[INFO] 2025-07-13 16:37:40 | french_text_processor | Performance: text_validation completed in 2.34ms | text_length=1250

[INFO] 2025-07-13 16:37:40 | csv_writer | Article data written to CSV | title=France News Update url=https://slate.fr/article-123 rows_written=45 filename=2025-07-13.csv
```

### Error Scenarios
```
[ERROR] 2025-07-13 16:37:41 | core.processor | Component initialization failed | source=FranceInfo scraper_class=article_scrapers.scrapers.france_info_scraper.FranceInfoURLScraper error=Connection timeout

[WARNING] 2025-07-13 16:37:41 | error_recovery | Circuit breaker opened | failure_count=5 failure_threshold=5 state=OPEN

[WARNING] 2025-07-13 16:37:41 | graceful_degradation | URL count reduced for struggling source | source=TF1Info original_count=100 reduced_count=45 reduction_percent=55.0 success_rate=0.35
```

### Performance Analysis
```
[INFO] 2025-07-13 16:37:42 | french_text_processor | Performance: text_tokenization completed in 15.67ms | cleaned_length=2340

[INFO] 2025-07-13 16:37:42 | base_parser | Performance: url_fetch completed in 456.78ms | url=https://example.com status_code=200

[INFO] 2025-07-13 16:37:42 | core.processor | Performance: article_processing_batch completed in 8934.56ms | source=Slate.fr processed=23 attempted=25
```

## JSON Output for Log Aggregation

When using structured format, logs are output as JSON for machine parsing:

```json
{
  "timestamp": "2025-07-13T16:37:40Z",
  "level": "INFO",
  "logger": "article_scrapers.core.processor",
  "message": "Source processing completed",
  "module": "processor",
  "function": "process_source",
  "line": 245,
  "source": "Slate.fr",
  "articles_processed": 25,
  "articles_attempted": 30,
  "success_rate_percent": 83.3,
  "processing_time_seconds": 12.45,
  "articles_per_second": 2.01
}
```

## Debugging Tips

### Enable Debug Mode
```python
from article_scrapers.utils.logging_config_enhanced import configure_debug_mode

# Enable detailed debugging including HTTP requests
configure_debug_mode(enabled=True)
```

### Check Logging Configuration
```python
from article_scrapers.utils.logging_config_enhanced import get_logging_summary

# Get current logging configuration
summary = get_logging_summary()
print(f"Root level: {summary['root_level']}")
print(f"Handlers: {summary['handlers']}")
print(f"Component levels: {summary['component_levels']}")
```

### Persistent Context
```python
# Add context that persists across log messages
logger.add_context(request_id="req-123", user_id="user-456")

logger.info("Processing started")  # Includes request_id and user_id
logger.info("Processing completed")  # Includes request_id and user_id

# Clear context when done
logger.clear_context()
```

## Benefits

### For Development
- **Human-readable output** with colors and clear formatting
- **Detailed debugging information** including HTTP requests and performance
- **Context preservation** across related operations
- **Easy performance profiling** with built-in timers

### For Production
- **Structured JSON logs** for log aggregation systems (ELK, Splunk, etc.)
- **Automatic log rotation** and retention policies
- **Error aggregation** with comprehensive context
- **Performance monitoring** with built-in metrics
- **Health monitoring** integration

### For Debugging
- **Rich context information** in every log message
- **Stack traces** with error logs
- **Performance bottleneck identification** with timing data
- **Component-specific log levels** for focused debugging
- **Backward compatibility** with existing logging code

This enhanced logging system provides enterprise-grade observability while maintaining ease of use for development and debugging.