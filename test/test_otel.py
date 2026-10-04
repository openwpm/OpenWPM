"""Tests for OpenTelemetry tracing.

The end-to-end tests export to a Jaeger all-in-one container and read the
spans back through its query API. They skip when testcontainers or a
container runtime is unavailable.
"""

import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

import pytest
import requests
from opentelemetry import trace
from opentelemetry.trace import INVALID_SPAN

from openwpm.command_sequence import CommandSequence
from openwpm.config import BrowserParams, ManagerParams
from openwpm.errors import ConfigError
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.storage.storage_controller import _with_otel_context
from openwpm.task_manager import TaskManager
from openwpm.utilities import db_utils, otel
from openwpm.utilities.multiprocess_utils import Process

from .utilities import ServerUrls

TM = otel.TASK_MANAGER_SERVICE
BM = otel.BROWSER_MANAGER_SERVICE
SC = otel.STORAGE_CONTROLLER_SERVICE
COMMANDS = ("InitializeCommand", "GetCommand", "FinalizeCommand")


@pytest.fixture
def no_global_provider(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Fail if OpenWPM touches the process-global tracer provider."""
    before = trace.get_tracer_provider()

    def forbidden(*_: Any, **__: Any) -> None:
        raise AssertionError("OpenWPM must not set the global tracer provider")

    monkeypatch.setattr(trace, "set_tracer_provider", forbidden)
    yield
    assert trace.get_tracer_provider() is before


@pytest.fixture
def clean_otel_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "OTEL_SDK_DISABLED",
        "OTEL_TRACES_EXPORTER",
        "OTEL_EXPORTER_OTLP_PROTOCOL",
        "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL",
    ):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def black_hole() -> Iterator[str]:
    """An OTLP endpoint that accepts connections and never answers."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        yield f"http://127.0.0.1:{sock.getsockname()[1]}"


@pytest.mark.pyonly
def test_disabled_creates_nothing(no_global_provider: None) -> None:
    assert otel.get_tracer(None) is None
    with otel.start_span(None, "x") as span:
        assert span is INVALID_SPAN
        assert trace.get_current_span() is INVALID_SPAN
    record = {"visit_id": 1}
    assert _with_otel_context(record) is record


@pytest.mark.pyonly
@pytest.mark.parametrize(
    "variable", ["OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"]
)
def test_enabled_provider_is_private(
    monkeypatch: pytest.MonkeyPatch,
    no_global_provider: None,
    clean_otel_env: None,
    variable: str,
) -> None:
    monkeypatch.setenv(variable, "http://127.0.0.1:9")
    provider = otel.create_provider(BM, {"openwpm.browser_id": 7})
    assert provider is not None
    try:
        assert provider.resource.attributes["service.name"] == BM
        assert provider.resource.attributes["openwpm.browser_id"] == 7
        tracer = otel.get_tracer(provider)
        with otel.start_span(tracer, "x") as span:
            assert span.is_recording()
            record = _with_otel_context({"visit_id": 1})
            assert "traceparent" in record["__otel_ctx"]
    finally:
        provider.shutdown()


@pytest.mark.pyonly
@pytest.mark.parametrize(
    "variable, value",
    [("OTEL_SDK_DISABLED", "true"), ("OTEL_TRACES_EXPORTER", "none")],
)
def test_standard_opt_outs_win(
    monkeypatch: pytest.MonkeyPatch, clean_otel_env: None, variable: str, value: str
) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:9")
    monkeypatch.setenv(variable, value)
    assert otel.create_provider(TM) is None


@pytest.mark.pyonly
@pytest.mark.parametrize(
    "variable, value",
    [
        ("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc"),
        ("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL", "http/json"),
        ("OTEL_TRACES_EXPORTER", "zipkin"),
    ],
)
def test_unsupported_exporter_is_refused(
    monkeypatch: pytest.MonkeyPatch, clean_otel_env: None, variable: str, value: str
) -> None:
    monkeypatch.setenv(variable, value)
    with pytest.raises(ConfigError, match=value):
        otel.create_provider(TM)


@pytest.mark.pyonly
def test_shutdown_is_bounded_when_collector_hangs(
    monkeypatch: pytest.MonkeyPatch, clean_otel_env: None, black_hole: str
) -> None:
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", black_hole)
    provider = otel.create_provider(TM)
    with otel.start_span(otel.get_tracer(provider), "x"):
        pass
    start = time.monotonic()
    otel.shutdown_provider(provider)
    assert time.monotonic() - start < otel.SHUTDOWN_TIMEOUT_S + 1


def test_tracing_is_opt_in(
    monkeypatch: pytest.MonkeyPatch,
    default_params: tuple[ManagerParams, list[BrowserParams]],
    clean_otel_env: None,
) -> None:
    """Ambient OTEL_* variables alone must not switch tracing on."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:9")
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    structured = SQLiteStorageProvider(manager_params.data_directory / "crawl.sqlite")
    with TaskManager(manager_params, browser_params[:1], structured, None) as manager:
        assert manager.tracer is None
        processes = [
            manager.storage_controller_handle.storage_controller,
            manager.browsers[0].browser_manager,
        ]
        assert [p.otel_service for p in processes] == [None, None]


def _emit_one_span() -> None:
    with otel.start_span(otel.process_tracer(), "x"):
        pass


@pytest.mark.pyonly
def test_child_exit_is_bounded_when_collector_hangs(
    monkeypatch: pytest.MonkeyPatch, clean_otel_env: None, black_hole: str
) -> None:
    """A browser restart joins the old BrowserManager process; its final
    flush must not wait out the exporter's 10s timeout."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", black_hole)
    child = Process(otel_service=BM, target=_emit_one_span)
    start = time.monotonic()
    child.start()
    child.join(30)
    assert child.exitcode == 0
    assert time.monotonic() - start < otel.SHUTDOWN_TIMEOUT_S + 3


def test_browser_spawn_failure_closes_cleanly(
    monkeypatch: pytest.MonkeyPatch,
    default_params: tuple[ManagerParams, list[BrowserParams]],
    capsys: pytest.CaptureFixture[str],
    clean_otel_env: None,
    black_hole: str,
) -> None:
    """close() during a failed launch must not trip over tracing state."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", black_hole)
    monkeypatch.setattr(
        "openwpm.browser_manager.BrowserManagerHandle.launch_browser_manager",
        lambda self: False,
    )
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.tracing = True
    structured = SQLiteStorageProvider(manager_params.data_directory / "crawl.sqlite")
    with pytest.raises(Exception) as excinfo:
        TaskManager(manager_params, browser_params[:1], structured, None)
    assert not isinstance(excinfo.value, AttributeError)
    assert "Shutdown took" in capsys.readouterr().out


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    name: str
    service: str
    process: Dict[str, Any]
    tags: Dict[str, Any]


class Jaeger:
    def __init__(self, otlp_endpoint: str, query_url: str) -> None:
        self.otlp_endpoint = otlp_endpoint
        self.query_url = query_url

    def spans(self) -> List[Span]:
        """All spans of all traces that touch an OpenWPM service."""
        traces: Dict[str, Any] = {}
        for service in (TM, BM, SC):
            resp = requests.get(
                f"{self.query_url}/api/traces",
                params={"service": service, "limit": "10000", "lookback": "1h"},
            )
            resp.raise_for_status()
            for t in resp.json().get("data") or []:
                traces[t["traceID"]] = t
        spans = []
        for t in traces.values():
            for s in t["spans"]:
                proc = t["processes"][s["processID"]]
                parents = [
                    r["spanID"]
                    for r in s.get("references", [])
                    if r["refType"] == "CHILD_OF"
                ]
                spans.append(
                    Span(
                        trace_id=s["traceID"],
                        span_id=s["spanID"],
                        parent_id=parents[0] if parents else None,
                        name=s["operationName"],
                        service=proc["serviceName"],
                        process={tg["key"]: tg["value"] for tg in proc["tags"]},
                        tags={tg["key"]: tg["value"] for tg in s["tags"]},
                    )
                )
        return spans

    def wait_for(self, done: Callable[[List[Span]], bool]) -> List[Span]:
        """Poll until the indexed spans satisfy `done`, or give up after 60s."""
        deadline = time.monotonic() + 60
        while True:
            spans = self.spans()
            if done(spans) or time.monotonic() > deadline:
                return spans
            time.sleep(1)


@pytest.fixture
def jaeger(monkeypatch: pytest.MonkeyPatch, clean_otel_env: None) -> Iterator[Jaeger]:
    """A fresh Jaeger per test, with OpenWPM's exporter pointed at it."""
    pytest.importorskip("testcontainers")
    import docker
    from testcontainers.core.container import DockerContainer
    from testcontainers.core.waiting_utils import wait_for_logs

    try:
        docker.from_env().ping()
    except Exception as e:
        pytest.skip(f"no container runtime: {e}")

    container = (
        DockerContainer("jaegertracing/all-in-one:1.76.0")
        .with_env("COLLECTOR_OTLP_ENABLED", "true")
        .with_exposed_ports(4318, 16686)
    )
    container.start()
    try:
        wait_for_logs(container, "Starting HTTP server", timeout=30)
        host = container.get_container_host_ip()
        j = Jaeger(
            f"http://{host}:{container.get_exposed_port(4318)}",
            f"http://{host}:{container.get_exposed_port(16686)}",
        )
        deadline = time.monotonic() + 30
        while True:
            try:
                requests.get(f"{j.query_url}/api/services").raise_for_status()
                break
            except requests.RequestException:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.5)
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", j.otlp_endpoint)
        yield j
    finally:
        container.stop()


def _by_id(spans: List[Span]) -> Dict[str, Span]:
    return {s.span_id: s for s in spans}


def _children(spans: List[Span], parent: Span, name: str, service: str) -> List[Span]:
    return [
        s
        for s in spans
        if s.parent_id == parent.span_id and s.name == name and s.service == service
    ]


def test_restarted_browsers_trace(
    jaeger: Jaeger,
    no_global_provider: None,
    default_params: tuple[ManagerParams, list[BrowserParams]],
    server: ServerUrls,
    xpi: None,
) -> None:
    """A stateless crawl restarts the browser after every visit; each
    generation must export its own spans, linked to the TaskManager's."""
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.tracing = True
    browser_params = browser_params[:1]
    browser_params[0].http_instrument = True
    db_path = manager_params.data_directory / "crawl-data.sqlite"
    urls = [f"{server.base}/simple_{c}.html" for c in "abc"]

    with TaskManager(
        manager_params, browser_params, SQLiteStorageProvider(db_path), None
    ) as manager:
        browser_id = manager.browsers[0].browser_id
        for url in urls:
            cs = CommandSequence(url, reset=True, blocking=True)
            cs.get(sleep=0, timeout=60)
            manager.execute_command_sequence(cs)

    generations = len(urls) + 1
    spans = jaeger.wait_for(
        lambda spans: sum(
            s.name == "browser_startup" and s.service == BM for s in spans
        )
        >= generations
        and sum(s.name == "execute_command_sequence" for s in spans) >= len(urls)
        and sum(s.name == "finalize_visit_id" for s in spans) >= len(urls)
    )
    by_id = _by_id(spans)
    assert {s.service for s in spans} == {TM, BM, SC}

    # Every browser generation reports under the browser service, from its
    # own process, carrying the browser id as an attribute.
    bm_spans = [s for s in spans if s.service == BM]
    pids = {s.process["process.pid"] for s in bm_spans}
    assert len(pids) == generations, pids
    for pid in pids:
        names = [s.name for s in bm_spans if s.process["process.pid"] == pid]
        assert names.count("browser_startup") == 1, (pid, names)
        assert "start_extension" in names, (pid, names)
    assert {s.process["openwpm.browser_id"] for s in bm_spans} == {browser_id}
    for s in bm_spans:
        if s.name == "browser_startup":
            assert s.parent_id is None

    sequences = [
        s for s in spans if s.name == "execute_command_sequence" and s.service == TM
    ]
    assert sorted(s.tags["url.full"] for s in sequences) == urls
    for ecs in sequences:
        assert ecs.parent_id is None
        assert ecs.tags["openwpm.browser_id"] == browser_id
        assert len(_children(spans, ecs, "post_cs_chores", TM)) == 1
        for command in COMMANDS:
            (tm_cmd,) = _children(spans, ecs, command, TM)
            assert tm_cmd.tags["openwpm.command_status"] == "ok"
            # Cross-process edge: the browser executes it as a child.
            (bm_cmd,) = _children(spans, tm_cmd, command, BM)
            assert bm_cmd.trace_id == ecs.trace_id
        # The commands of one visit run in one browser generation.
        visit_pids = {
            bm.process["process.pid"]
            for command in COMMANDS
            for tm_cmd in _children(spans, ecs, command, TM)
            for bm in spans
            if bm.parent_id == tm_cmd.span_id and bm.service == BM
        }
        assert len(visit_pids) == 1

    # Storage spans only exist for records sent from a traced span, and hang
    # off the span that sent them. Extension records produce none.
    records = [s for s in spans if s.name == "process_record"]
    assert records
    for r in records:
        assert r.service == SC
        assert r.parent_id in by_id and by_id[r.parent_id].service in (TM, BM)

    # The propagated context never reaches the stored data.
    visits = db_utils.query_db(
        db_path, "SELECT visit_id, site_url FROM site_visits", as_tuple=True
    )
    assert sorted(url for _, url in visits) == urls
    # The extension sends the finalize record, so its span is a root.
    finalizes = [
        s
        for s in spans
        if s.name == "finalize_visit_id" and s.tags["openwpm.visit_id"] != -1
    ]
    assert {f.tags["openwpm.visit_id"] for f in finalizes} == {
        visit_id for visit_id, _ in visits
    }
    assert all(f.service == SC and f.parent_id is None for f in finalizes)
    history = db_utils.query_db(
        db_path, "SELECT command_status FROM crawl_history", as_tuple=True
    )
    assert len(history) == len(COMMANDS) * len(urls)
    assert set(history) == {("ok",)}
    (http,) = db_utils.query_db(
        db_path, "SELECT COUNT(*) FROM http_requests", as_tuple=True
    )
    assert http[0] > 0
    with open(manager_params.log_path) as log:
        assert "__otel_ctx" not in log.read()


def test_two_task_managers_both_export(
    jaeger: Jaeger,
    no_global_provider: None,
    default_params: tuple[ManagerParams, list[BrowserParams]],
    server: ServerUrls,
    xpi: None,
    tmp_path: Path,
) -> None:
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.tracing = True
    urls = [f"{server.base}/simple_a.html", f"{server.base}/simple_b.html"]
    for i, url in enumerate(urls):
        db = SQLiteStorageProvider(tmp_path / f"crawl-{i}.sqlite")
        with TaskManager(manager_params, browser_params[:1], db, None) as manager:
            manager.get(url)

    def sequences(spans: List[Span]) -> List[Span]:
        return [
            s for s in spans if s.name == "execute_command_sequence" and s.service == TM
        ]

    def done(spans: List[Span]) -> bool:
        return (
            len(sequences(spans)) >= 2
            and sum(s.name == "browser_startup" for s in spans) >= 2
        )

    spans = jaeger.wait_for(done)
    assert sorted(s.tags["url.full"] for s in sequences(spans)) == urls
    assert len({s.process["process.pid"] for s in spans if s.service == BM}) == 2
