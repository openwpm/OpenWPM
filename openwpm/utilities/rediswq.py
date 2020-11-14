import hashlib
import logging
import uuid
from typing import Any

import redis


class RedisWQ(object):
    """Simple Finite Work Queue with Redis Backend

    This work queue is finite: as long as no more work is added
    after workers start, the workers can detect when the queue
    is completely empty.

    The items in the work queue are assumed to have unique values.

    This object is not intended to be used by multiple threads
    concurrently.

    From:
    https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue
    """

    def __init__(self, name, max_retries=2, **redis_kwargs):
        """Redis worker queue instance

        The default connection parameters are:
            * host='localhost'
            * port=6379
            * db=0

        Parameters
        ----------
        name : string
            A prefix that identified all of the objects associated with this
            worker queue. e.g., the main work queue is identified by `name`,
            and the processesing queue is identified by `name`:processing.
        max_retries : int, optional
            Number of times to retry a job before removing it from the queue.
            If you don't wish to retry jobs, set the limit to 0.
        """
        self._db = redis.Redis(**redis_kwargs)
        # The session ID will uniquely identify this "worker".
        self._session = str(uuid.uuid4())
        # Work queue is implemented as two queues: main, and processing.
        # Work is initially in main, and moved to processing when a client
        # picks it up.
        self._main_q_key = name
        self._processing_q_key = name + ":processing"
        self._retry_hash_map_key = name + ":retries"
        self._lease_key_prefix = name + ":leased_by_session:"
        self._logger = logging.getLogger("openwpm")
        self._max_retries = max_retries

    def sessionID(self):
        """Return the ID for this session."""
        return self._session

    def _main_qsize(self):
        """Return the size of the main queue."""
        return self._db.llen(self._main_q_key)

    def _processing_qsize(self):
        """Return the size of the main queue."""
        return self._db.llen(self._processing_q_key)

    def empty(self):
        """Return True if the queue is empty, including work being done,
        False otherwise.

        False does not necessarily mean that there is work available to work
        on right now,
        """
        return self._main_qsize() == 0 and self._processing_qsize() == 0

    def _maybe_renew_job(self, job):
        """Transactionally move job from the processing to the work queue.

        A job will not be renewed if it appears that another worker is
        changing the processing queue or if the job has exceeded the
        maximum number of retries.
        """
        self._logger.debug(
            "Lease expired for job %s. Attempting to move from processing "
            "queue to work queue...[session %s]" % (job, self.sessionID())
        )
        # A pipeline executes a set of commands as a transaction, but
        # does not support rollback in the event any individual
        # command fails.
        pipe = self._db.pipeline(transaction=True)

        # First, watch the processing queue and retry count hash map for
        # changes. The pipeline transaction won't execute if changes occur
        # after this point. This allows us to prevent duplicate updates from
        # different workers.
        pipe.watch(self._processing_q_key)
        pipe.watch(self._retry_hash_map_key)

        # Next, ensure that the job is still in the processing queue.
        # The processing queue is relatively small, so this shouldn't
        # be an expensive operation.
        if job not in self._db.lrange(self._processing_q_key, 0, -1):
            pipe.reset()
            self._logger.debug(
                "Job %s no longer in the processing queue, there is no need "
                "to renew..." % job
            )
            return

        # Next, check that we haven't exceeded the retry limit for this job
        # If we have, remove the job from the queue entirely and don't add it
        # back to the main work queue
        retry_count = self.get_retry_number(job)
        if retry_count + 1 > self._max_retries:
            self._logger.debug(
                "Job %s exceeded maximum retry count, attempting to remove "
                "from the processing queue. [session %s]" % (job, self.sessionID())
            )
            pipe.multi()
            pipe = pipe.lrem(self._processing_q_key, 0, job).hdel(
                self._retry_hash_map_key, job
            )
            results = pipe.execute()
            if results:
                self._logger.debug(
                    "Job %s successfully removed from the processing "
                    "queue due to too many retries. [session %s]"
                    % (job, self.sessionID())
                )
            else:
                self._logger.debug(
                    "Removing job %s was interrupted due to a change by a "
                    "concurrent worker. [session %s]" % (job, self.sessionID())
                )
            return

        # Finally, execute the transaction to move the expired job
        # back to the main queue and increment the retry counter by 1
        pipe.multi()
        pipe = (
            pipe.lrem(self._processing_q_key, 0, job)
            .rpush(self._main_q_key, job)
            .hincrby(self._retry_hash_map_key, job, 1)
        )
        results = pipe.execute()
        if results:
            self._logger.debug(
                "Job %s successfully moved from processing queue to "
                "work queue for retry attempt %d. [session %s]"
                % (job, retry_count + 1, self.sessionID())
            )
        else:
            self._logger.debug(
                "Moving job %s was interrupted due to a change by a "
                "concurrent worker. [session %s]" % (job, self.sessionID())
            )
        return

    def check_expired_leases(self):
        """Return to the work queue

        If the lease key is not present for an item (it expired or was
        never created because the client crashed before creating it)
        then move the item back to the main queue so others can work on
        it.
        """
        processing = self._db.lrange(self._processing_q_key, 0, -1)
        for job in processing:
            if not self._lease_exists(job):
                try:
                    self._maybe_renew_job(job)
                except redis.exceptions.WatchError:
                    self._logger.debug(
                        "Watched variable changed while trying to renew lease "
                        "for job %s. Skipping lease renew for now... "
                        "[session %s]" % (job, self.sessionID())
                    )
                except Exception:
                    self._logger.error(
                        "Exception while renewing job %s. [session %s]"
                        % (job, self.sessionID()),
                        exc_info=True,
                    )
        return

    def _itemkey(self, item):
        """Returns a string that uniquely identifies an item (bytes)."""
        return hashlib.sha224(item).hexdigest()

    def _lease_exists(self, item):
        """True if a lease on 'item' exists."""
        return self._db.exists(self._lease_key_prefix + self._itemkey(item))

    def lease(self, lease_secs=60, block=True, timeout=None):
        """Begin working on an item the work queue.

        Lease the item for lease_secs.  After that time, other
        workers may consider this client to have crashed or stalled
        and pick up the item instead.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self._db.brpoplpush(
                self._main_q_key, self._processing_q_key, timeout=timeout
            )
        else:
            item = self._db.rpoplpush(self._main_q_key, self._processing_q_key)
        if item:
            # Record that we (this session id) are working on a key. Expire
            # that note after the lease timeout.
            # Note: if we crash at this line of the program, then GC will see
            # no lease for this item a later return it to the main queue.
            itemkey = self._itemkey(item)
            self._db.setex(self._lease_key_prefix + itemkey, lease_secs, self._session)
        return item

    def renew_lease(self, job: Any, lease_secs=60) -> bool:
        """Checks if the item is currently leased by this client
        and if so renews that lease by `lease_secs`
        Return false if the lease was already expired"""

        key = self._lease_key_prefix + self._itemkey(job)
        if self._db.get(key):
            self._db.setex(key, lease_secs, self._session)
            return True
        else:
            return False

    def get_retry_number(self, job):
        """Return the number of retries for the given `job`.

        This returns 0 if the job has never been retried. We do not attempt
        to verify that the job is valid, is currently leased by the worker, etc
        The caller is responsible for ensuring that there is currently a
        lease on this job (thus ensuring the retry count reflects the current
        state).
        """
        num_retries = self._db.hget(self._retry_hash_map_key, job)
        if num_retries is None:
            return 0
        else:
            num_retries = int(num_retries)
        return num_retries

    def complete(self, job):
        """Complete working on the `job`.

        If the lease expired, the item may not have completed, and some
        other worker may have picked it up.  There is no indication
        of what happened.
        """
        self._db.lrem(self._processing_q_key, 0, job)
        self._db.hdel(self._retry_hash_map_key, job)
        # If we crash here, then the GC code will try to move the value, but
        # it will not be here, which is fine.  So this does not need to be a
        # transaction.
        itemkey = self._itemkey(job)
        self._db.delete(self._lease_key_prefix + itemkey, self._session)
