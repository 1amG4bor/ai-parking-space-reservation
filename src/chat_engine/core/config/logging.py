"""Shared logging configuration for the application."""

import logging
import os


def create_logger():
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure logging
    logging.basicConfig(
        level=log_level_str,
        format="%(asctime)s - %(name)s|%(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    )

    return logging.getLogger("APSR")


logger = create_logger()
