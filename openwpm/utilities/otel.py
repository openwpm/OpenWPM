"""OpenTelemetry tracing for OpenWPM.

OpenWPM never reads or sets the global tracer provider, so an embedding
application's OTel setup is left alone. With ManagerParams.tracing set, each
OpenWPM process owns a provider that exports over OTLP/HTTP. When tracing is
disabled no span objects are created at all.
"""

import os
import threading
from contextlib import nullcontext
from typing import TYPE_CHECKING, Any, ContextManager, Dict, Optional

from opentelemetry.context import Context
from opentelemetry.trace import INVALID_SPAN, Span, Tracer

from ..errors import ConfigError

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider

TASK_MANAGER_SERVICE = "openwpm-task-manager"
BROWSER_MANAGER_SERVICE = "openwpm-browser-manager"
STORAGE_CONTROLLER_SERVICE = "openwpm-storage-controller"

# Pending spans are dropped after this. A healthy collector needs
# milliseconds; an unreachable one would hold every browser restart for the
# exporter's full retry window.
SHUTDOWN_TIMEOUT_S = 1.0


def enabled() -> bool:
    """Whether the standard OTEL_* variables leave trace export on."""
    if os.getenv("OTEL_SDK_DISABLED", "").strip().lower() == "true":
        return False
    exporter = os.getenv("OTEL_TRACES_EXPORTER") or "otlp"
    if exporter.strip().lower() == "none":
        return False
    if exporter.strip().lower() != "otlp":
        raise ConfigError(
            f"OTEL_TRACES_EXPORTER={exporter!r}: OpenWPM only exports traces "
            "over OTLP. Set it to 'none' to disable tracing."
        )
    protocol = (
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL")
        or os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL")
        or "http/protobuf"
    )
    if protocol.strip().lower() != "http/protobuf":
        raise ConfigError(
            f"OTLP protocol {protocol!r}: OpenWPM only exports traces over "
            "http/protobuf. Point the endpoint at the collector's OTLP/HTTP "
            "port (usually 4318) and unset the protocol variable."
        )
    return True


def create_provider(
    service_name: str, attributes: Optional[Dict[str, Any]] = None
) -> Optional["TracerProvider"]:
    """Return a new exporting provider, or None when tracing is disabled."""
    if not enabled():
        return None

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {**(attributes or {}), "service.name": service_name, "process.pid": os.getpid()}
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    return provider


def get_tracer(provider: Optional["TracerProvider"]) -> Optional[Tracer]:
    return None if provider is None else provider.get_tracer("openwpm")


def shutdown_provider(provider: Optional["TracerProvider"]) -> None:
    """Flush and shut down, waiting at most SHUTDOWN_TIMEOUT_S."""
    if provider is None:
        return
    # The SDK's shutdown cannot be bounded: BatchSpanProcessor waits for an
    # in-flight export, which retries until the exporter's own timeout.
    flusher = threading.Thread(
        target=provider.shutdown, name="OpenWPMTracerShutdown", daemon=True
    )
    flusher.start()
    flusher.join(SHUTDOWN_TIMEOUT_S)


def start_span(
    tracer: Optional[Tracer], name: str, context: Optional[Context] = None
) -> ContextManager[Span]:
    """Like Tracer.start_as_current_span, but free when tracer is None."""
    if tracer is None:
        return nullcontext(INVALID_SPAN)
    return tracer.start_as_current_span(name, context=context)


# The provider of the current child process, set by Process.run. It is never
# set in the process that owns the TaskManager.
_process_provider: Optional["TracerProvider"] = None


def init_process(service_name: str, attributes: Optional[Dict[str, Any]]) -> None:
    global _process_provider
    _process_provider = create_provider(service_name, attributes)


def shutdown_process() -> None:
    global _process_provider
    shutdown_provider(_process_provider)
    _process_provider = None


def process_tracer() -> Optional[Tracer]:
    return get_tracer(_process_provider)
