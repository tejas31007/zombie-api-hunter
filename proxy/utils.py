import logging
import sys

def get_logger(name: str):
    """
    Creates a structured logger for the application.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)

    # Create formatter (Time - Level - Message)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Avoid duplicate logs if handler already exists
    if not logger.handlers:
        logger.addHandler(handler)

    return logger