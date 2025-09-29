"""
AWS Operations Command Center - Logging Configuration
Structured logging setup with JSON formatting and context support.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from config.settings import settings

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add process info for debugging
        if settings.debug_mode:
            log_entry['process_id'] = record.process
            log_entry['thread_id'] = record.thread
        
        return json.dumps(log_entry, default=str)

class PlainFormatter(logging.Formatter):
    """Plain text formatter for development"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logging(
    level: Optional[str] = None,
    format_type: Optional[str] = None,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Setup structured logging for the application
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ('json' or 'plain')
        logger_name: Name of the logger to configure
    
    Returns:
        Configured logger instance
    """
    # Use settings defaults if not provided
    level = level or settings.log_level
    format_type = format_type or settings.log_format
    logger_name = logger_name or 'aws_operations_center'
    
    # Get or create logger
    logger = logging.getLogger(logger_name)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    
    # Set formatter based on type
    if format_type.lower() == 'json':
        formatter = StructuredFormatter()
    else:
        formatter = PlainFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the application's configuration"""
    return logging.getLogger(f"aws_operations_center.{name}")

def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any
) -> None:
    """
    Log a message with additional context fields
    
    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **context: Additional context fields
    """
    # Create a LogRecord with extra fields
    extra = {'extra_fields': context}
    logger.log(level, message, extra=extra)

def log_agent_operation(
    logger: logging.Logger,
    agent_name: str,
    operation: str,
    status: str,
    duration: Optional[float] = None,
    **context: Any
) -> None:
    """
    Log agent operation with standardized fields
    
    Args:
        logger: Logger instance
        agent_name: Name of the agent
        operation: Operation being performed
        status: Operation status (started, completed, failed)
        duration: Operation duration in seconds
        **context: Additional context
    """
    log_context = {
        'agent': agent_name,
        'operation': operation,
        'status': status,
        **context
    }
    
    if duration is not None:
        log_context['duration_seconds'] = round(duration, 3)
    
    level = logging.INFO if status in ['started', 'completed'] else logging.ERROR
    message = f"Agent {agent_name} {operation} {status}"
    
    log_with_context(logger, level, message, **log_context)

def log_aws_api_call(
    logger: logging.Logger,
    service: str,
    operation: str,
    status: str,
    duration: Optional[float] = None,
    error_code: Optional[str] = None,
    **context: Any
) -> None:
    """
    Log AWS API call with standardized fields
    
    Args:
        logger: Logger instance
        service: AWS service name
        operation: API operation name
        status: Call status (success, error, retry)
        duration: Call duration in seconds
        error_code: AWS error code if applicable
        **context: Additional context
    """
    log_context = {
        'aws_service': service,
        'aws_operation': operation,
        'status': status,
        **context
    }
    
    if duration is not None:
        log_context['duration_seconds'] = round(duration, 3)
    
    if error_code:
        log_context['aws_error_code'] = error_code
    
    level = logging.INFO if status == 'success' else logging.WARNING
    message = f"AWS {service}.{operation} {status}"
    
    log_with_context(logger, level, message, **log_context)

# Initialize application logger
app_logger = setup_logging()

# Export commonly used loggers
cost_logger = get_logger('cost_intelligence')
ops_logger = get_logger('operations_intelligence')
infra_logger = get_logger('infrastructure_intelligence')
orchestrator_logger = get_logger('orchestrator')
api_logger = get_logger('api')
