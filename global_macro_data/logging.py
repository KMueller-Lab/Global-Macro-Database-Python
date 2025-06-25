import logging

logger = logging.getLogger('gmd')
logger.setLevel(logging.INFO)  # Default level (can be overridden by user)

# Add NullHandler so importing your package doesn't configure root logger
logger.addHandler(logging.NullHandler())
