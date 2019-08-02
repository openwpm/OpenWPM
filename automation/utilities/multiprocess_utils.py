import logging

import multiprocess as mp


class Process(mp.Process):
    """Wrapper Process class that includes exception logging"""
    def __init__(self, *args, **kwargs):
        mp.Process.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger('openwpm')

    def run(self):
        try:
            mp.Process.run(self)
        except Exception as e:
            self.logger.error(
                "Exception in child process.", exc_info=True
            )
            raise e
