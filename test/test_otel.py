"""Integration test for OpenTelemetry tracing instrumentation.

Uses a Jaeger all-in-one container (via testcontainers) as an OTLP receiver,
runs a single-URL crawl, then queries the Jaeger HTTP API to verify the
expected span tree exists with correct parentage.
"""

import os
import time

import pytest
import requests

from openwpm.command_sequence import CommandSequence
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager

from . import utilities

# Skip the entire module if Docker is not available
docker = pytest.importorskip("testcontainers")

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


@pytest.fixture(scope="module")
def jaeger_container():
    """Start a Jaeger all-in-one container exposing OTLP HTTP and query API."""
    container = (
        DockerContainer("jaegertracing/all-in-one:1.76.0")
        .with_env("COLLECTOR_OTLP_ENABLED", "true")
        .with_exposed_ports(4318, 16686)
    )
    container.start()
    # Wait for Jaeger to be ready
    wait_for_logs(container, "Starting HTTP server", timeout=30)
    # Give a moment for all endpoints to bind
    time.sleep(2)
    yield container
    container.stop()


@pytest.fixture(scope="module")
def server():
    """Run an HTTP server during the tests."""
    srv, server_thread = utilities.start_server()
    yield
    srv.shutdown()
    server_thread.join()


def _get_jaeger_port(container, port):
    """Get the mapped host port for a container port."""
    return container.get_exposed_port(port)


def _get_jaeger_host(container):
    """Get the host for the Jaeger container."""
    return container.get_container_host_ip()


def test_command_sequence_full_trace(jaeger_container, server, tmp_path, xpi):
    """Verify the full CommandSequence span hierarchy end-to-end.

    Crawls a single URL with OTel export pointing at the Jaeger container,
    then queries the Jaeger API to assert spans exist with correct parentage.
    """
    host = _get_jaeger_host(jaeger_container)
    otlp_port = _get_jaeger_port(jaeger_container, 4318)
    query_port = _get_jaeger_port(jaeger_container, 16686)

    otlp_endpoint = f"http://{host}:{otlp_port}"
    jaeger_query_url = f"http://{host}:{query_port}"

    # Set the OTLP endpoint so OTel activates
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint

    try:
        manager_params = ManagerParams(num_browsers=1)
        browser_params = [BrowserParams(display_mode="headless")]
        manager_params.data_directory = tmp_path
        manager_params.log_path = tmp_path / "openwpm.log"
        manager_params.testing = True

        db_path = tmp_path / "crawl-data.sqlite"
        structured_provider = SQLiteStorageProvider(db_path)

        with TaskManager(
            manager_params,
            browser_params,
            structured_provider,
            None,
        ) as manager:
            test_url = utilities.BASE_TEST_URL + "/simple_a.html"
            cs = CommandSequence(test_url, blocking=True)
            cs.get(sleep=0, timeout=60)
            manager.execute_command_sequence(cs)

        # Poll Jaeger until spans are indexed (up to 30s)
        services = []
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            time.sleep(2)
            services_resp = requests.get(f"{jaeger_query_url}/api/services")
            services_resp.raise_for_status()
            services = services_resp.json().get("data", [])
            if any(s.startswith("BrowserManager-") for s in services):
                break
        browser_service = None
        for svc in services:
            if svc.startswith("BrowserManager-"):
                browser_service = svc
                break

        # Check for task manager service
        task_manager_service = None
        for svc in services:
            if svc == "openwpm-task-manager":
                task_manager_service = svc
                break

        # Check for storage controller service
        storage_service = None
        for svc in services:
            if svc == "StorageController":
                storage_service = svc
                break

        assert (
            browser_service is not None
        ), f"No BrowserManager service found in Jaeger. Available services: {services}"
        assert (
            task_manager_service is not None
        ), f"No openwpm-task-manager service found in Jaeger. Available services: {services}"
        assert (
            storage_service is not None
        ), f"No StorageController service found in Jaeger. Available services: {services}"

        # Query traces for the browser manager
        traces_resp = requests.get(
            f"{jaeger_query_url}/api/traces",
            params={"service": browser_service, "limit": 10},
        )
        traces_resp.raise_for_status()
        traces_data = traces_resp.json().get("data", [])
        assert len(traces_data) > 0, "No traces found for browser manager service"

        # Collect all spans across all traces
        all_spans = []
        for trace_data in traces_data:
            all_spans.extend(trace_data.get("spans", []))

        # Build a map of span names for easier assertion
        span_names = [s["operationName"] for s in all_spans]

        # Assert expected spans exist
        assert (
            "browser_startup" in span_names
        ), f"browser_startup span not found. Spans: {span_names}"
        assert (
            "start_extension" in span_names
        ), f"start_extension span not found. Spans: {span_names}"

        # Check the task manager service for command sequence spans
        tm_traces_resp = requests.get(
            f"{jaeger_query_url}/api/traces",
            params={"service": task_manager_service, "limit": 10},
        )
        tm_traces_resp.raise_for_status()
        tm_traces = tm_traces_resp.json().get("data", [])

        tm_spans = []
        for trace_data in tm_traces:
            tm_spans.extend(trace_data.get("spans", []))

        # The execute_command_sequence and per-command spans run in the
        # TaskManager process (on the command thread), so they use the
        # task-manager tracer provider.
        tm_span_names = [s["operationName"] for s in tm_spans]

        assert (
            "execute_command_sequence" in tm_span_names
        ), f"execute_command_sequence span not found. TM Spans: {tm_span_names}"
        assert (
            "GetCommand" in tm_span_names
        ), f"GetCommand span not found. TM Spans: {tm_span_names}"
        assert (
            "FinalizeCommand" in tm_span_names
        ), f"FinalizeCommand span not found. TM Spans: {tm_span_names}"
        assert (
            "post_cs_chores" in tm_span_names
        ), f"post_cs_chores span not found. TM Spans: {tm_span_names}"

        # Verify parentage: GetCommand should be child of execute_command_sequence
        ecs_span = next(
            s for s in tm_spans if s["operationName"] == "execute_command_sequence"
        )
        get_span = next(s for s in tm_spans if s["operationName"] == "GetCommand")
        finalize_span = next(
            s for s in tm_spans if s["operationName"] == "FinalizeCommand"
        )

        # In Jaeger, references[0].spanID is the parent
        def get_parent_span_id(span):
            refs = span.get("references", [])
            for ref in refs:
                if ref.get("refType") == "CHILD_OF":
                    return ref.get("spanID")
            return None

        assert (
            get_parent_span_id(get_span) == ecs_span["spanID"]
        ), "GetCommand should be a child of execute_command_sequence"
        assert (
            get_parent_span_id(finalize_span) == ecs_span["spanID"]
        ), "FinalizeCommand should be a child of execute_command_sequence"

        # Verify execute_command_sequence has browser_id and visit_id attributes
        ecs_tags = {t["key"]: t["value"] for t in ecs_span.get("tags", [])}
        assert (
            "browser_id" in ecs_tags
        ), "execute_command_sequence should have browser_id attribute"
        assert (
            "visit_id" in ecs_tags
        ), "execute_command_sequence should have visit_id attribute"

        # Check storage controller spans
        sc_traces_resp = requests.get(
            f"{jaeger_query_url}/api/traces",
            params={"service": storage_service, "limit": 10},
        )
        sc_traces_resp.raise_for_status()
        sc_traces = sc_traces_resp.json().get("data", [])

        sc_spans = []
        for trace_data in sc_traces:
            sc_spans.extend(trace_data.get("spans", []))

        sc_span_names = [s["operationName"] for s in sc_spans]

        assert (
            "process_record" in sc_span_names
        ), f"process_record span not found. SC Spans: {sc_span_names}"
        assert (
            "finalize_visit_id" in sc_span_names
        ), f"finalize_visit_id span not found. SC Spans: {sc_span_names}"

        # Verify cross-process trace linking: all three services
        # should share at least one trace ID
        browser_trace_ids = {t["traceID"] for t in traces_data}
        tm_trace_ids = {t["traceID"] for t in tm_traces}
        sc_trace_ids = {t["traceID"] for t in sc_traces}
        shared_traces = browser_trace_ids & tm_trace_ids & sc_trace_ids
        assert shared_traces, (
            "No shared trace IDs across all three services — "
            "cross-process context propagation is broken. "
            f"Browser: {browser_trace_ids}, TM: {tm_trace_ids}, SC: {sc_trace_ids}"
        )

    finally:
        os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
