
import base64
import json
import time
from typing import Any, Dict, Tuple, Union

from .base import (
    BaseParams,
)



def listener_process_runner(base_params: BaseParams,
                            manager_params: Dict[str, Any],
                            ldb_enabled: bool) -> None:
    """LocalListener runner. Pass to new process"""
    listener = LocalListener(base_params, manager_params, ldb_enabled)
    listener.startup()

    while True:
        listener.update_status_queue()
        if listener.should_shutdown():
            break

        if listener.record_queue.empty():
            time.sleep(1)
            listener.commit_structured_records()
            listener.commit_unstructured_records()
            continue

        # Process record
        record = listener.record_queue.get()
        listener.process_record(record)

        # batch commit if necessary
        listener.commit_structured_records()
        listener.commit_unstructured_records()

    listener.drain_queue()
    listener.shutdown()