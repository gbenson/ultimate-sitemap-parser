import logging
from . import log

# Use standard Python logging
log.create_logger = logging.getLogger

from .flex import main
