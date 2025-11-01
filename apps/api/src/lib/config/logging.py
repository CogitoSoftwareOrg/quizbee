import os
import json
import logging
from contextvars import ContextVar
from datetime import datetime
from typing import Any

from uvicorn.logging import DefaultFormatter

# Контекстные переменные для request_id и user_id
request_id_context: ContextVar[str] = ContextVar("request_id", default="")
user_id_context: ContextVar[str] = ContextVar("user_id", default="")

log_level = os.getenv("LOG_LEVEL", "INFO")

log_format = os.getenv("LOG_FORMAT", "pretty" if log_level == "local" else "json")

if log_format == "json":
    app_formatter_name = "app_json"
elif log_format == "pretty":
    app_formatter_name = "app_pretty"
else:  # human or default
    app_formatter_name = "app_human"


class RequestContextFilter(logging.Filter):
    """Фильтр для добавления контекста запроса в логи"""

    def filter(self, record):
        # Добавляем request_id и user_id в запись лога
        record.request_id = request_id_context.get() or "-"
        record.user_id = user_id_context.get() or "-"
        return True


def set_user_id(user_id: str) -> None:
    """Устанавливает user_id в контекст логирования"""
    user_id_context.set(str(user_id))


class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированного логирования"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
        }

        # Добавляем exception, если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class PrettyJSONFormatter(logging.Formatter):
    """Красивый JSON форматтер для терминала с цветами"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        logger = record.name
        message = record.getMessage()
        module = record.module
        line = record.lineno
        request_id = getattr(record, "request_id", "-")
        user_id = getattr(record, "user_id", "-")

        # Цвет уровня логирования
        color = self.COLORS.get(level, self.RESET)

        # Форматируем строку
        parts = [
            f"{color}[{timestamp}]{self.RESET}",
            f"{color}{level:7}{self.RESET}",
            f"{self.DIM}{logger:25}{self.RESET}",
            f"{self.DIM}{module}:{line:<4}{self.RESET}",
            f"[{request_id}]" if request_id != "-" else self.DIM + "[-]" + self.RESET,
            f"[{user_id}]" if user_id != "-" else self.DIM + "[-]" + self.RESET,
            message,
        ]

        return " ".join(parts)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "uvicorn_default": {
            "()": DefaultFormatter,
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "app_human": {
            "format": (
                "[%(asctime)s] %(levelname)-7s %(name)-25s "
                "%(module)s:%(lineno)-4d [%(request_id)s] [%(user_id)s] %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "app_json": {
            "()": JSONFormatter,
        },
        "app_pretty": {
            "()": PrettyJSONFormatter,
        },
    },
    "filters": {
        "request_context": {
            "()": RequestContextFilter,
        }
    },
    "handlers": {
        "uvicorn": {
            "class": "logging.StreamHandler",
            "formatter": "uvicorn_default",
            "stream": "ext://sys.stdout",
        },
        "app_console": {
            "class": "logging.StreamHandler",
            "formatter": app_formatter_name,
            "filters": ["request_context"],
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # Логгеры uvicorn
        "uvicorn": {
            "handlers": ["uvicorn"],
            "level": log_level,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["uvicorn"],
            "level": log_level,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["uvicorn"],
            "level": log_level,
            "propagate": False,
        },
        # Семья логгеров приложения
        "app": {
            "handlers": ["app_console"],
            "level": log_level,
            "propagate": False,
        },
        "app.http": {
            "handlers": ["app_console"],
            "level": log_level,
            "propagate": False,
        },
        "app.usecases": {
            "handlers": ["app_console"],
            "level": log_level,
            "propagate": False,
        },
        "app.adapters": {
            "handlers": ["app_console"],
            "level": log_level,
            "propagate": False,
        },
    },
    "root": {
        "level": log_level,
        "handlers": ["app_console"],
    },
}
