# Minimal type stub for the `multiprocess` package (the dill-backed fork of
# the stdlib `multiprocessing`). It ships no type information of its own, but
# mirrors `multiprocessing`'s public API, so we re-export the names we use.
from multiprocessing import JoinableQueue as JoinableQueue
from multiprocessing import Process as Process
from multiprocessing import Queue as Queue
