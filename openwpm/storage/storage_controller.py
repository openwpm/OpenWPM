import asyncio
import base64
import logging
import queue
import random
import socket
import time
from asyncio import IncompleteReadError, Task
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, NoReturn, Optional, Tuple

from multiprocess import Queue

from openwpm.utilities.multiprocess_utils import Process

from ..config import BrowserParamsInternal, ManagerParamsInternal
from ..socket_interface import ClientSocket, get_message_from_reader
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
INVALID_VISIT_ID = VisitId(-1)


class StorageController:
    """
    Manages incoming data and it's saving to disk

    Provides it's status to the task manager via the completion and status queue.
    Can be shut down via a shutdown signal in the shutdown queue
    """

    def __init__(
        self,
        structured_storage: StructuredStorageProvider,
        unstructured_storage: Optional[UnstructuredStorageProvider],
        status_queue: Queue,
        completion_queue: Queue,
        shutdown_queue: Queue,
    ) -> None:
        """
        Parameters
        ----------
        status_queue
            queue through which the StorageControllerHandler
            receives updates on the current amount of records to be processed.
            Also used for initialization
        completion_queue
            queue containing the visit_ids of saved records
        shutdown_queue
            queue that the main process can use to shut down the StorageController
        """
        self.status_queue = status_queue
        self.completion_queue = completion_queue
        self.shutdown_queue = shutdown_queue
        self._shutdown_flag = False
        self._relaxed = False
        self.logger = logging.getLogger("openwpm")
        self.store_record_tasks: DefaultDict[VisitId, List[Task[None]]] = defaultdict(
            list
        )
        """Contains all store_record tasks for a given visit_id"""
        self.finalize_tasks: List[Tuple[VisitId, Optional[Task[None]], bool]] = []
        """Contains all information required for update_completion_queue to work
            Tuple structure is: VisitId, optional completion token, success
        """
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
                "An exception occurred while processing records", exc_info=e
            )

    async def handler(
        self, reader: asyncio.StreamReader, _: asyncio.StreamWriter
    ) -> None:
        """Created for every new connection to the Server"""
        self.logger.debug("Initializing new handler")
        while True:
            try:
                record: Tuple[str, Any] = await get_message_from_reader(reader)
            except IncompleteReadError:
                self.logger.info(
                    "Terminating handler, because the underlying socket closed"
                )
                break
            if len(record) != 2:
                self.logger.error("Query is not the correct length %s", repr(record))
                continue

            self._last_record_received = time.time()
            record_type, data = record

            if record_type == RECORD_TYPE_CREATE:
                raise RuntimeError(
                    f"""{RECORD_TYPE_CREATE} is no longer supported.
                    Please change the schema before starting the StorageController.
                    For an example of that see test/test_custom_function.py
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
            await self.store_record(table_name, visit_id, data)

    async def store_record(
        self, table_name: TableName, visit_id: VisitId, data: Dict[str, Any]
    ) -> None:

        if visit_id == INVALID_VISIT_ID:
            # Hacking around the fact that task and crawl don't have a VisitID
            del data["visit_id"]
        # Turning these into task to be able to have them complete without blocking the socket
        self.store_record_tasks[visit_id].append(
            asyncio.create_task(
                self.structured_storage.store_record(
                    table=table_name, visit_id=visit_id, record=data
                )
            )
        )

    async def _handle_meta(self, visit_id: VisitId, data: Dict[str, Any]) -> None:
        """
        Messages for the table RECORD_TYPE_SPECIAL are meta information
        communicated to the storage controller
        Supported message types:
        - finalize: A message sent by the extension to
                    signal that a visit_id is complete.
        - initialize: TODO: Start complaining if we receive data for a visit_id
                      before the initialize event happened.
                      See also https://github.com/mozilla/OpenWPM/issues/846
        """
        action: str = data["action"]
        if action == ACTION_TYPE_INITIALIZE:
            return
        elif action == ACTION_TYPE_FINALIZE:
            success: bool = data["success"]
            completion_token = await self.finalize_visit_id(visit_id, success)
            self.finalize_tasks.append((visit_id, completion_token, success))
        else:
            raise ValueError("Unexpected action: %s", action)

    async def finalize_visit_id(
        self, visit_id: VisitId, success: bool
    ) -> Optional[Task[None]]:
        """Makes sure all records for a given visit_id
        have been processed before we invoke finalize_visit_id
        on the structured_storage

        See StructuredStorageProvider::finalize_visit_id for additional
        documentation
        """

        if visit_id not in self.store_record_tasks:
            self.logger.error(
                "There are no records to be stored for visit_id %d, skipping...",
                visit_id,
            )
            return None

        self.logger.info("Awaiting all tasks for visit_id %d", visit_id)
        for task in self.store_record_tasks[visit_id]:
            await task
        del self.store_record_tasks[visit_id]
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
            visit_id_count = len(self.store_record_tasks.keys())
            task_count = 0
            for task_list in self.store_record_tasks.values():
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

    async def shutdown(self, completion_queue_task: Task[None]) -> None:
        completion_tokens = {}
        visit_ids = list(self.store_record_tasks.keys())
        for visit_id in visit_ids:
            t = await self.finalize_visit_id(visit_id, success=False)
            if t is not None:
                completion_tokens[visit_id] = t
        await self.structured_storage.flush_cache()
        await completion_queue_task
        for visit_id, token in completion_tokens.items():
            await token
            self.completion_queue.put((visit_id, False))

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
        regardless of the current batch size.

        This coroutine will get cancelled with an exception
        so there is no need for an orderly return
        """
        while True:
            if self._last_record_received is None:
                await asyncio.sleep(BATCH_COMMIT_TIMEOUT)
                continue

            diff = time.time() - self._last_record_received
            if diff < BATCH_COMMIT_TIMEOUT:
                time_until_timeout = BATCH_COMMIT_TIMEOUT - diff
                await asyncio.sleep(time_until_timeout)
                continue

            self.logger.debug(
                "Saving current records since no new data has "
                "been written for %d seconds." % diff
            )
            await self.structured_storage.flush_cache()
            if self.unstructured_storage:
                await self.unstructured_storage.flush_cache()
            self._last_record_received = None

    async def update_completion_queue(self) -> None:
        """All completed finalize_visit_id tasks get put into the completion_queue here"""
        while not (self._shutdown_flag and len(self.finalize_tasks) == 0):
            # This list is needed because iterating over a list and changing it at the same time
            # is forbidden
            new_finalize_tasks: List[Tuple[VisitId, Optional[Task[None]], bool]] = []
            for visit_id, token, success in self.finalize_tasks:
                if (
                    not token or token.done()
                ):  # Either way all data for the visit_id was saved out
                    self.completion_queue.put((visit_id, success))
                else:
                    new_finalize_tasks.append((visit_id, token, success))
            self.finalize_tasks = new_finalize_tasks
            await asyncio.sleep(5)

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

        update_completion_queue = asyncio.create_task(
            self.update_completion_queue(), name="CompletionQueueFeeder"
        )
        # Blocks until we should shutdown
        await self.should_shutdown()

        server.close()
        status_queue_update.cancel()
        timeout_check.cancel()
        await server.wait_closed()
        await self.shutdown(update_completion_queue)

    def run(self) -> None:
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        asyncio.run(self._run(), debug=True)


class DataSocket:
    """Wrapper around ClientSocket to make sending records to the StorageController more convenient"""

    def __init__(self, listener_address: Tuple[str, int]) -> None:
        self.socket = ClientSocket(serialization="dill")
        self.socket.connect(*listener_address)
        self.logger = logging.getLogger("openwpm")

    def store_record(
        self, table_name: TableName, visit_id: VisitId, data: Dict[str, Any]
    ) -> None:
        data["visit_id"] = visit_id
        self.socket.send(
            (
                table_name,
                data,
            )
        )

    def finalize_visit_id(self, visit_id: VisitId, success: bool) -> None:
        self.socket.send(
            (
                RECORD_TYPE_META,
                {
                    "action": ACTION_TYPE_FINALIZE,
                    "visit_id": visit_id,
                    "success": success,
                },
            )
        )

    def close(self) -> None:
        self.socket.close()


class StorageControllerHandle:
    """This class contains all methods relevant for the TaskManager
    to interact with the StorageController
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
        self.storage_controller = StorageController(
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

    def save_configuration(
        self,
        manager_params: ManagerParamsInternal,
        browser_params: List[BrowserParamsInternal],
        openwpm_version: str,
        browser_version: str,
    ) -> None:
        assert self.listener_address is not None
        sock = DataSocket(self.listener_address)
        task_id = random.getrandbits(32)
        sock.store_record(
            TableName("task"),
            INVALID_VISIT_ID,
            {
                "task_id": task_id,
                "manager_params": manager_params.to_json(),
                "openwpm_version": openwpm_version,
                "browser_version": browser_version,
            },
        )
        # Record browser details for each browser
        for browser_param in browser_params:
            sock.store_record(
                TableName("crawl"),
                INVALID_VISIT_ID,
                {
                    "browser_id": browser_param.browser_id,
                    "task_id": task_id,
                    "browser_params": browser_param.to_json(),
                },
            )
        sock.finalize_visit_id(INVALID_VISIT_ID, success=True)

    def launch(self) -> None:
        """Starts the storage controller"""
        self.storage_controller = Process(
            name="StorageController",
            target=StorageController.run,
            args=(self.storage_controller,),
        )
        self.storage_controller.daemon = True
        self.storage_controller.start()

        self.listener_address = self.status_queue.get()

    def get_new_completed_visits(self) -> List[Tuple[int, bool]]:
        """
        Returns a list of all visit ids that have been processed since
        the last time the method was called and whether or not they
        ran successfully.

        This method will return an empty list in case no visit ids have
        been processed since the last time this method was called
        """
        finished_visit_ids = list()
        while not self.completion_queue.empty():
            finished_visit_ids.append(self.completion_queue.get())
        return finished_visit_ids

    def shutdown(self, relaxed: bool = True) -> None:
        """Terminate the storage controller process"""
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
        """Return the most recent queue size sent from the Storage Controller process"""

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
                "No status update from the storage controller process "
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
                "No status update from the storage controller process "
                "for %d seconds." % (time.time() - self._last_status_received)
            )
        assert isinstance(self._last_status, int)
        return self._last_status
