"""Shared logging configuration for the application."""
import os
import logging


def create_logger():
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure logging
    logging.basicConfig(
        level=log_level_str,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger("APSR")

    return logger

logger = create_logger()