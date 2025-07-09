import sys
import os
from loguru import logger
from app.core.config import settings

# Remove default handlers
logger.remove()

# Configure log format
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# Add console handler
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level=settings.LOG_LEVEL,
    backtrace=True,
    diagnose=True,
)

# Add file handler
log_file_path = os.path.join(settings.LOG_DIR, "app.log")
logger.add(
    log_file_path,
    rotation="10 MB",
    retention="7 days",
    format=LOG_FORMAT,
    level=settings.LOG_LEVEL,
    backtrace=True,
    diagnose=True,
)

# Create a class for context-based logging
class ContextLogger:
    def __init__(self, context=None):
        self.context = context or {}
    
    def bind(self, **kwargs):
        """Bind additional context to the logger"""
        self.context.update(kwargs)
        return self
    
    def _format_message(self, message):
        """Format message with context if available"""
        if self.context:
            context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{message} [{context_str}]"
        return message
    
    def debug(self, message, *args, **kwargs):
        logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        logger.error(self._format_message(message), *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        logger.exception(self._format_message(message), *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        logger.critical(self._format_message(message), *args, **kwargs)


# Export the logger
__all__ = ["logger", "ContextLogger"] 