import logging
import os
import sys
import traceback
from typing import Any, TypeAlias

import multiprocess as mp
import psutil
from honeycomb.opentelemetry import HoneycombOptions, configure_opentelemetry
from opentelemetry.trace import get_tracer_provider


def parse_traceback_for_sentry(tb):
    """Parse traceback to send Sentry-compatible strings

    Sentry appears to limit each `extra` string to 500 characters. This splits
    the traceback string across N chunks of at most 500 characters each.
    Chunks are split at newlines for readability. Traceback lines over 500
    characters are still truncated.

    Parameters
    ----------
    tb : list of strings
        Traceback formatted such that each list item is a new line.
    """
    out = dict()
    out_str = ""
    counter = 0
    for i in range(len(tb)):
        out_str += tb[i][0 : min(500, len(tb[i]))]
        if i != len(tb) - 1 and len(out_str) + len(tb[i + 1]) < 500:
            continue
        out["traceback-%d" % counter] = out_str
        out_str = ""
        counter += 1
    return out


ProcessName: TypeAlias = str


class Process(mp.Process):
    """Wrapper Process class that includes exception logging"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        mp.Process.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger("openwpm")

    def run(self) -> None:
        configure_opentelemetry(
            HoneycombOptions(
                debug=True,  # prints exported traces & metrics to the console, useful for debugging and setting up
                # Honeycomb API Key, required to send data to Honeycomb
                apikey=os.getenv("HONEYCOMB_API_KEY"),
                # Dataset that will be populated with data from this service in Honeycomb
                service_name=self.name,
                enable_local_visualizations=True,  # Will print a link to a trace produced in Honeycomb to the console, useful for debugging
                # sample_rate = DEFAULT_SAMPLE_RATE, Set a sample rate for spans
            )
        )
        try:
            mp.Process.run(self)
        except Exception as e:
            tb = traceback.format_exception(*sys.exc_info())
            extra = parse_traceback_for_sentry(tb)
            extra["exception"] = tb[-1]
            self.logger.error("Exception in child process.", exc_info=True, extra=extra)
            raise e
        provider = get_tracer_provider()
        # This is an opentelemetry.sdk.TraceProvider which has a shutdown method
        if hasattr(provider, "shutdown"):
            provider.shutdown()


def kill_process_and_children(
    parent_process: psutil.Process, logger, timeout: int = 20
) -> None:
    """Attempts to recursively kill the entire process tree under
    a given parent process"""
    try:
        for child in parent_process.children():
            kill_process_and_children(child, logger)

        parent_process.kill()
        parent_process.wait(timeout=timeout)
    except psutil.NoSuchProcess:
        logger.debug("Process %i has already exited", parent_process.pid)
        pass
    except psutil.TimeoutExpired:
        logger.debug(
            "Timeout while waiting for process %i to terminate" % parent_process.pid
        )
        pass
