import logging
import sys


def setup_logging(level=logging.INFO):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        root_logger.addHandler(handler)
