import logging
import os
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Dict, Optional

from opentelemetry import trace
from opentelemetry.context import attach, detach, get_current, set_value
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Tracer, get_tracer_provider, set_tracer_provider
from opentelemetry.trace.propagation import get_current_span

_current_browser_id: ContextVar[Optional[int]] = ContextVar(
    "_current_browser_id", default=None
)

LOG_FORMAT = (
    "%(asctime)s - %(processName)-11s[%(threadName)-10s]"
    "- %(module)-20s - %(levelname)-8s: %(message)s"
)
CONSOLE_FORMAT = "%(module)-20s - %(levelname)-8s - %(message)s"

_initialized = False


class BrowserLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that injects browser_id into log records."""

    def __init__(self, logger: logging.Logger, browser_id: int) -> None:
        super().__init__(logger, {"browser_id": browser_id})

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"]["browser_id"] = self.extra["browser_id"]
        return "BROWSER %d: %s" % (self.extra["browser_id"], msg), kwargs


def setup_telemetry(log_file: Path, service_name: str = "openwpm") -> None:
    """Initialize OpenTelemetry tracing and configure logging handlers."""
    global _initialized

    # Set up TracerProvider
    provider = TracerProvider()

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    elif os.environ.get("OTEL_DEBUG"):
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    set_tracer_provider(provider)

    # Set up logging
    logger = logging.getLogger("openwpm")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers = []

    # File handler
    log_file = Path(os.path.expanduser(log_file))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    _initialized = True


def get_tracer(name: str = "openwpm") -> Tracer:
    """Return the OTel tracer."""
    return trace.get_tracer(name)


def shutdown_telemetry() -> None:
    """Clean shutdown of OTel providers and logging handlers."""
    global _initialized

    provider = get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()

    logger = logging.getLogger("openwpm")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    _initialized = False


def serialize_context() -> Dict[str, object]:
    """Serialize the current span context for propagation to child processes."""
    span = get_current_span()
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return {}
    return {
        "trace_id": ctx.trace_id,
        "span_id": ctx.span_id,
        "trace_flags": ctx.trace_flags,
        "trace_state": str(ctx.trace_state),
    }


def attach_context(ctx_dict: Dict[str, object]) -> None:
    """Attach a serialized span context in a child process."""
    if not ctx_dict:
        return
    from opentelemetry.trace import SpanContext, TraceFlags
    from opentelemetry.trace.propagation import set_span_in_context

    trace_id = ctx_dict["trace_id"]
    span_id = ctx_dict["span_id"]
    trace_flags = ctx_dict["trace_flags"]
    assert isinstance(trace_id, int)
    assert isinstance(span_id, int)
    assert isinstance(trace_flags, int)
    span_context = SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=True,
        trace_flags=TraceFlags(trace_flags),
    )
    ctx = set_span_in_context(trace.NonRecordingSpan(span_context))
    attach(ctx)


def get_browser_logger(browser_id: int) -> BrowserLoggerAdapter:
    """Return a logger adapter that includes browser_id in all messages."""
    logger = logging.getLogger("openwpm")
    return BrowserLoggerAdapter(logger, browser_id)


def set_browser_context(browser_id: int) -> None:
    """Set the browser_id in the current context variable."""
    _current_browser_id.set(browser_id)


def get_browser_context() -> Optional[int]:
    """Get the browser_id from the current context variable."""
    return _current_browser_id.get()


def log_extension_message(browser_id: int, level: int, msg: str) -> None:
    """Log a message from the browser extension with browser_id metadata."""
    logger = logging.getLogger("openwpm")
    record = logging.LogRecord(
        name="openwpm.extension",
        level=level,
        pathname="Extension",
        lineno=0,
        msg="Extension-%d : %s" % (browser_id, msg),
        args=None,
        exc_info=None,
    )
    record.browser_id = browser_id  # type: ignore[attr-defined]
    logger.handle(record)
