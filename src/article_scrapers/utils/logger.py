
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """Returns a logger with standard formatting."""
    logger = logging.getLogger(name)
    
    # If root logger has handlers, we don't need to add our own
    if not logging.root.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
