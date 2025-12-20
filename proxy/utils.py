import logging
import os
from typing import Dict, Any, Optional  # <--- Added strict types

def get_logger(name: str) -> logging.Logger:  # <--- Added return type
    """
    Creates a standardized logger for the application.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Add formatter to handler
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger


def load_template(filename: str, replacements: Dict[str, Any]) -> Optional[str]: # <--- Added explicit types
    """
    Loads an HTML file and replaces {{variables}} with actual values.
    """
    path = os.path.join("proxy/templates", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple template engine: Find {{key}} and replace with value
        for key, value in replacements.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        return content
    except FileNotFoundError:
        print(f"❌ Error: Template {path} not found.")
        return None
    except Exception as e:
        print(f"❌ Error loading template: {e}")
        return None