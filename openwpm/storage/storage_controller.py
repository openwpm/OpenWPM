import asyncio
import base64
import logging
import queue
import random
import socket
import threading
import time
from collections import defaultdict
from typing import (
    Any,
    Awaitable,
    DefaultDict,
    Dict,
    List,
    Literal,
    NoReturn,
    Optional,
    Tuple,
)

from multiprocess import Queue

from openwpm.utilities.multiprocess_utils import Process

from ..socket_interface import get_message_from_reader
from ..types import BrowserId, VisitId
from .storage_providers import (
    StructuredStorageProvider,
    TableName,
    UnstructuredStorageProvider,
)

RECORD_TYPE_CONTENT = "page_content"
RECORD_TYPE_META = "meta_information"
ACTION_TYPE_FINALIZE = "Finalize"
ACTION_TYPE_INITIALIZE = "Initialize"

RECORD_TYPE_CREATE = "create_table"
STATUS_TIMEOUT = 120  # seconds
SHUTDOWN_SIGNAL = "SHUTDOWN"
BATCH_COMMIT_TIMEOUT = 30  # commit a batch if no new records for N seconds


STATUS_UPDATE_INTERVAL = 5  # seconds


class StorageController:
    def __init__(
        self,
        structured_storage: StructuredStorageProvider,
        unstructured_storage: Optional[UnstructuredStorageProvider],
        status_queue: Queue,
        completion_queue: Queue,
        shutdown_queue: Queue,
    ) -> None:
        """
        Creates a BaseListener instance

        Parameters
        ----------
        status_queue
            queue that the current amount of records to be processed will
            be sent to
            also used for initialization
        completion_queue
            queue containing the visitIDs of saved records
        shutdown_queue
            queue that the main process can use to shut down the listener
        """
        self.status_queue = status_queue
        self.completion_queue = completion_queue
        self.shutdown_queue = shutdown_queue
        self._shutdown_flag = False
        self._relaxed = False
        self.logger = logging.getLogger("openwpm")
        self.current_tasks: DefaultDict[VisitId, List[asyncio.Task]] = defaultdict(list)
        self.structured_storage = structured_storage
        self.unstructured_storage = unstructured_storage
        self._last_record_received: Optional[float] = None

    async def _handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """This is a dirty hack around the fact that exceptions get swallowed by the asyncio.Server
        and the coroutine just dies without any message.
        By having this function be a wrapper we at least get a log message
        """
        try:
            await self.handler(reader, writer)
        except Exception as e:
            self.logger.error(
                "An exception occurred while processing for records", exc_info=e
            )

    async def handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Created for every new connection to the Server"""
        self.logger.debug("Initializing new handler")
        while True:
            try:
                record: Tuple[str, Any] = await get_message_from_reader(reader)
            except IOError as e:
                self.logger.debug(
                    "Terminating handler, because the underlying socket closed",
                    exc_info=e,
                )
                break

            if len(record) != 2:
                self.logger.error("Query is not the correct length %s", repr(record))
                continue

            self._last_record_received = time.time()
            record_type, data = record

            self.logger.debug("Received record for record_type %s", record_type)

            if record_type == RECORD_TYPE_CREATE:
                raise RuntimeError(
                    f"""{RECORD_TYPE_CREATE} is no longer supported.
                    since the user now has access to the DB before it
                    goes into use, they should set up all schemas before
                    launching the DataAggregator
                    """
                )

            if record_type == RECORD_TYPE_CONTENT:
                assert len(data) == 2
                if self.unstructured_storage is None:
                    self.logger.error(
                        """Tried to save content while not having
                        provided any unstructured storage provider."""
                    )
                    continue
                content, content_hash = data
                content = base64.b64decode(content)
                await self.unstructured_storage.store_blob(
                    filename=content_hash, blob=content
                )
                continue

            if "visit_id" not in data:
                self.logger.error(
                    "Skipping record: No visit_id contained in record %r", record
                )
                continue

            visit_id = VisitId(data["visit_id"])

            if record_type == RECORD_TYPE_META:
                await self._handle_meta(visit_id, data)
                continue

            table_name = TableName(record_type)
            # Turning these into task to be able to verify
            self.current_tasks[visit_id].append(
                asyncio.create_task(
                    self.structured_storage.store_record(
                        table=table_name, visit_id=visit_id, record=data
                    )
                )
            )

    async def _handle_meta(self, visit_id: VisitId, data: Dict[str, Any]) -> None:
        """
        Messages for the table RECORD_TYPE_SPECIAL are metainformation
        communicated to the aggregator
        Supported message types:
        - finalize: A message sent by the extension to
                    signal that a visit_id is complete.
        - initialize: TODO: Start complaining if we receive data for a visit_id
                      before the initialize event happened. (This might not be easy
                      because of `site_visits`
        """
        action: str = data["action"]
        if action == ACTION_TYPE_INITIALIZE:
            return
        elif action == ACTION_TYPE_FINALIZE:
            success = data["success"]
            completion_token = await self.finalize_visit_id(visit_id, success)
            await completion_token
            self.completion_queue.put((visit_id, success))
            del self.current_tasks[visit_id]
        else:
            raise ValueError("Unexpected action: %s", action)

    async def finalize_visit_id(
        self, visit_id: VisitId, success: bool
    ) -> Awaitable[None]:
        """Makes sure all records for a given visit_id
        have been processed before we invoke finalize_visit_id
        on the structured_storage
        """
        self.logger.info("Awaiting all tasks for visit_id %d", visit_id)

        for task in self.current_tasks[visit_id]:
            await task
        self.logger.debug(
            "Awaited all tasks for visit_id %d while finalizing", visit_id
        )
        completion_token = await self.structured_storage.finalize_visit_id(
            visit_id, interrupted=not success
        )
        return completion_token

    async def update_status_queue(self) -> NoReturn:
        """Send manager process a status update.

        This coroutine will get cancelled with an exception
        so there is no need for an orderly return
        """
        while True:
            await asyncio.sleep(STATUS_UPDATE_INTERVAL)
            visit_id_count = len(self.current_tasks.keys())
            task_count = 0
            for task_list in self.current_tasks.values():
                for task in task_list:
                    if not task.done():
                        task_count += 1
            self.status_queue.put(task_count)
            self.logger.debug(
                (
                    "StorageController status: There are currently %d scheduled tasks "
                    "for %d visit_ids"
                ),
                task_count,
                visit_id_count,
            )

    async def shutdown(self) -> None:
        await self.structured_storage.flush_cache()
        await self.structured_storage.shutdown()
        if self.unstructured_storage is not None:
            await self.unstructured_storage.flush_cache()
            await self.unstructured_storage.shutdown()

    async def should_shutdown(self) -> None:
        """Returns when we should shut down"""

        while self.shutdown_queue.empty():
            await asyncio.sleep(STATUS_UPDATE_INTERVAL)
        _, relaxed = self.shutdown_queue.get()
        self._relaxed = relaxed
        self._shutdown_flag = True
        self.logger.info("Received shutdown signal!")

    async def save_batch_if_past_timeout(self) -> NoReturn:
        """Save the current batch of records if no new data has been received.

        If we aren't receiving new data for this batch we commit early
        regardless of the current batch size."""
        while True:
            if self._last_record_received is None:
                await asyncio.sleep(BATCH_COMMIT_TIMEOUT)
                continue

            time_until_timeout = (
                time.time() - self._last_record_received - BATCH_COMMIT_TIMEOUT
            )
            if time_until_timeout > 0:
                await asyncio.sleep(time_until_timeout)
                continue

            self.logger.debug(
                "Saving current records since no new data has "
                "been written for %d seconds."
                % (time.time() - self._last_record_received)
            )
            await self.structured_storage.flush_cache()
            if self.unstructured_storage:
                await self.unstructured_storage.flush_cache()
            self._last_record_received = None

    async def finish_tasks(self) -> None:
        self.logger.info("Awaiting unfinished tasks before shutting down")
        for visit_id, tasks in self.current_tasks.items():
            self.logger.debug("Awaiting tasks for visit_id %d", visit_id)
            for task in tasks:
                await task

    async def _run(self) -> None:

        await self.structured_storage.init()
        if self.unstructured_storage:
            await self.unstructured_storage.init()
        server: asyncio.AbstractServer = await asyncio.start_server(
            self._handler, "localhost", 0, family=socket.AF_INET
        )
        sockets = server.sockets
        assert sockets is not None
        socketname = sockets[0].getsockname()
        self.status_queue.put(socketname)
        status_queue_update = asyncio.create_task(
            self.update_status_queue(), name="StatusQueue"
        )
        timeout_check = asyncio.create_task(
            self.save_batch_if_past_timeout(), name="TimeoutCheck"
        )
        # Blocks until we should shutdown
        await self.should_shutdown()

        server.close()
        status_queue_update.cancel()
        timeout_check.cancel()
        await server.wait_closed()

        await self.finish_tasks()

        finalization_tokens = {}
        visit_ids = list(self.current_tasks.keys())
        for visit_id in visit_ids:
            finalization_tokens[visit_id] = await self.finalize_visit_id(
                visit_id, success=False
            )
        await self.structured_storage.flush_cache()
        for visit_id, token in finalization_tokens.items():
            await token
            self.completion_queue.put((visit_id, False))
            del self.current_tasks[visit_id]

        await self.shutdown()

    def run(self) -> None:
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        asyncio.run(self._run(), debug=True)


class StorageControllerHandle:
    """This class contains all methods relevant for the TaskManager
    to interact with the DataAggregator
    """

    def __init__(
        self,
        structured_storage: StructuredStorageProvider,
        unstructured_storage: Optional[UnstructuredStorageProvider],
    ) -> None:

        self.listener_address: Optional[Tuple[str, int]] = None
        self.listener_process: Optional[Process] = None
        self.status_queue = Queue()
        self.completion_queue = Queue()
        self.shutdown_queue = Queue()
        self._last_status = None
        self._last_status_received: Optional[float] = None
        self.logger = logging.getLogger("openwpm")
        self.aggregator = StorageController(
            structured_storage,
            unstructured_storage,
            status_queue=self.status_queue,
            completion_queue=self.completion_queue,
            shutdown_queue=self.shutdown_queue,
        )

    def get_next_visit_id(self) -> VisitId:
        """Generate visit id as randomly generated positive integer less than 2^53.

        Parquet can support integers up to 64 bits, but Javascript can only
        represent integers up to 53 bits:
        https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER
        Thus, we cap these values at 53 bits.
        """
        return VisitId(random.getrandbits(53))

    def get_next_browser_id(self) -> BrowserId:
        """Generate crawl id as randomly generated positive 32bit integer

        Note: Parquet's partitioned dataset reader only supports integer
        partition columns up to 32 bits.
        """
        return BrowserId(random.getrandbits(32))

    def save_configuration(self, openwpm_version: str, browser_version: str) -> None:
        # FIXME I need to find a solution for this
        self.logger.error(
            "Can't log config as of yet, because it's still not implemented"
        )

    def launch(self) -> None:
        """Starts the data aggregator"""
        self.storage_controller = Process(
            name="StorageController",
            target=StorageController.run,
            args=(self.aggregator,),
        )
        self.storage_controller.daemon = True
        self.storage_controller.start()

        self.listener_address = self.status_queue.get()

    def get_new_completed_visits(self) -> List[Tuple[int, bool]]:
        """
        Returns a list of all visit ids that have been processed since
        the last time the method was called and whether or not they
        have been interrupted.

        This method will return an empty list in case no visit ids have
        been processed since the last time this method was called
        """
        finished_visit_ids = list()
        while not self.completion_queue.empty():
            finished_visit_ids.append(self.completion_queue.get())
        return finished_visit_ids

    def shutdown(self, relaxed: bool = True) -> None:
        """ Terminate the aggregator listener process"""
        assert isinstance(self.storage_controller, Process)
        self.logger.debug("Sending the shutdown signal to the Storage Controller...")
        self.shutdown_queue.put((SHUTDOWN_SIGNAL, relaxed))
        start_time = time.time()
        self.storage_controller.join(300)
        self.logger.debug(
            "%s took %s seconds to close."
            % (type(self).__name__, str(time.time() - start_time))
        )

    def get_most_recent_status(self) -> int:
        """Return the most recent queue size sent from the listener process"""

        # Block until we receive the first status update
        if self._last_status is None:
            return self.get_status()

        # Drain status queue until we receive most recent update
        while not self.status_queue.empty():
            self._last_status = self.status_queue.get()
            self._last_status_received = time.time()

        # Check last status signal
        if (time.time() - self._last_status_received) > STATUS_TIMEOUT:
            raise RuntimeError(
                "No status update from DataAggregator listener process "
                "for %d seconds." % (time.time() - self._last_status_received)
            )

        return self._last_status

    def get_status(self) -> int:
        """Get listener process status. If the status queue is empty, block."""
        try:
            self._last_status = self.status_queue.get(
                block=True, timeout=STATUS_TIMEOUT
            )
            self._last_status_received = time.time()
        except queue.Empty:
            assert self._last_status_received is not None
            raise RuntimeError(
                "No status update from DataAggregator listener process "
                "for %d seconds." % (time.time() - self._last_status_received)
            )
        assert isinstance(self._last_status, int)
        return self._last_status
