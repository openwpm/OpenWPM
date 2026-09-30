"""WebSocket bridge between the browser extension and Python.

Runs a WebSocket server in the BrowserManager process. The extension
connects via a single WebSocket (replacing the old 3-socket setup:
SendingSocket→StorageController, SendingSocket→MPLogger, ListeningSocket).

Incoming data records are forwarded to the StorageController via a
multiprocess.Queue. Incoming logs are forwarded to the Python logging
system. Outgoing commands are sent from the BrowserManager command loop.
"""

import asyncio
import json
import logging
import threading
from typing import Any, Optional

import websockets
import websockets.asyncio.server
from multiprocess import Queue as MPQueue

logger = logging.getLogger("openwpm")


class WebSocketBridge:
    """WebSocket server bridging extension ↔ StorageController/logging.

    Started in a background thread with its own asyncio event loop.
    """

    def __init__(self, data_queue: MPQueue, browser_id: int) -> None:
        self._data_queue = data_queue
        self._browser_id = browser_id
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws: Optional[websockets.asyncio.server.ServerConnection] = None
        self._port: Optional[int] = None
        self._ready = threading.Event()
        self._stop_event: Optional[asyncio.Event] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def port(self) -> Optional[int]:
        return self._port

    def start(self) -> int:
        """Start the WebSocket server in a background thread.

        Returns the port the server is listening on.
        """
        self._thread = threading.Thread(
            target=self._run, daemon=True, name=f"WSBridge-{self._browser_id}"
        )
        self._thread.start()
        if not self._ready.wait(timeout=30):
            raise RuntimeError("WebSocket bridge failed to start within 30 seconds")
        assert self._port is not None
        return self._port

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()
        try:
            self._loop.run_until_complete(self._serve())
        except Exception:
            logger.error(
                "BROWSER %i: WebSocket bridge crashed", self._browser_id, exc_info=True
            )
        finally:
            self._loop.close()

    async def _serve(self) -> None:
        assert self._stop_event is not None
        async with websockets.asyncio.server.serve(
            self._handler,
            "127.0.0.1",
            0,
            max_size=50 * 1024 * 1024,  # 50MB to handle large page_content
        ) as server:
            # Get the assigned port
            sockets = list(server.sockets)
            assert sockets
            self._port = sockets[0].getsockname()[1]
            logger.debug(
                "BROWSER %i: WebSocket bridge listening on port %d",
                self._browser_id,
                self._port,
            )
            self._ready.set()
            await self._stop_event.wait()

    async def _handler(
        self, websocket: websockets.asyncio.server.ServerConnection
    ) -> None:
        self._ws = websocket
        logger.debug(
            "BROWSER %i: Extension connected via WebSocket", self._browser_id
        )
        try:
            async for raw_message in websocket:
                try:
                    msg = json.loads(raw_message)
                    self._process_message(msg)
                except json.JSONDecodeError:
                    logger.error(
                        "BROWSER %i: Invalid JSON from extension: %s",
                        self._browser_id,
                        raw_message[:200],
                    )
                except Exception:
                    logger.error(
                        "BROWSER %i: Error processing extension message",
                        self._browser_id,
                        exc_info=True,
                    )
        except websockets.exceptions.ConnectionClosed:
            logger.debug(
                "BROWSER %i: Extension WebSocket disconnected", self._browser_id
            )
        finally:
            self._ws = None

    def _process_message(self, msg: dict) -> None:
        msg_type = msg.get("type")

        if msg_type == "data":
            table = msg["table"]
            record = msg["record"]
            self._data_queue.put((table, record))

        elif msg_type == "log":
            level = msg.get("level", logging.INFO)
            log_msg = msg.get("msg", "")
            logger.log(
                level,
                "Extension-%d: %s",
                self._browser_id,
                log_msg,
            )

        else:
            logger.warning(
                "BROWSER %i: Unknown WebSocket message type: %s",
                self._browser_id,
                msg_type,
            )

    def send_to_extension(self, msg: Any) -> None:
        """Send a message to the extension via WebSocket.

        Called from the BrowserManager command loop thread (not the asyncio thread).
        """
        if self._ws is None or self._loop is None:
            raise RuntimeError("No extension connected via WebSocket")

        data = json.dumps(msg)
        future = asyncio.run_coroutine_threadsafe(self._ws.send(data), self._loop)
        future.result(timeout=10)

    def stop(self) -> None:
        if self._loop is not None and self._stop_event is not None:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        if self._thread is not None:
            self._thread.join(timeout=10)


class ExtensionSocketAdapter:
    """Drop-in replacement for ClientSocket in BaseCommand.execute().

    Wraps WebSocketBridge to provide a send() method compatible with
    the existing command interface. Commands send messages to the
    extension through the WebSocket connection.
    """

    def __init__(self, bridge: WebSocketBridge) -> None:
        self._bridge = bridge

    def send(self, msg: Any) -> None:
        """Send a command to the extension.

        Handles the same message types as the old ClientSocket:
        - int (visit_id): legacy GetCommand sends just the visit_id
        - dict: InitializeCommand/FinalizeCommand send action dicts
        """
        if isinstance(msg, int):
            # Legacy: GetCommand sends visit_id as an integer
            ws_msg = {"type": "command", "visit_id": msg}
        elif isinstance(msg, dict):
            ws_msg = {"type": "command", **msg}
        else:
            ws_msg = {"type": "command", "data": msg}

        self._bridge.send_to_extension(ws_msg)

    def close(self) -> None:
        """No-op for compatibility."""
        pass
