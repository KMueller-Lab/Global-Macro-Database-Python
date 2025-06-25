import logging

logger = logging.getLogger('gmd')
logger.setLevel(logging.INFO)  # Default level (can be overridden by user)

# Add NullHandler so importing your package doesn't configure root logger
logger.addHandler(logging.NullHandler())


def enable_verbose_logging(level=logging.INFO):
    """Enable verbose logging for package."""
    logging.basicConfig(
        level=level,
        format='%(levelname)s:%(name)s:%(message)s'
    )
