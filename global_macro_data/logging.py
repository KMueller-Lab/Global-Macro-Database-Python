import logging

logger = logging.getLogger('gmd')
logger.setLevel(logging.INFO)  # Default level (can be overridden by user)

# Add NullHandler so importing your package doesn't configure root logger
logger.addHandler(logging.NullHandler())


def enable_verbose_logging(level=logging.INFO):
    """Enable console logging specifically for the gmd package."""
    handler = logging.StreamHandler()
    handler.setLevel(level)

    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(handler)

    logger.setLevel(level)
