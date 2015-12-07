from Errors import CommandExecutionError

class CommandSequence:
    """A command sequence should be associated with one top url site visit"""

    def __init__(self, url, reset=False):
        """Nothing to do here"""
        self.url = url
        self.reset = reset
        self.commands = []
        self.total_timeout = 0
        self.contains_get_or_browse = False

    def get(self, timeout=60):
        """ goes to a url """
        self.total_timeout += timeout
        command = ('GET', self.url)
        self.commands.append((command, timeout))
        self.contains_get_or_browse = True

    def browse(self, num_links = 2, timeout=60):
        """ browse a website and visit <num_links> links on the page """
        self.total_timeout += timeout
        command = ('BROWSE', self.url, num_links)
        self.commands.append((command, timeout))
        self.contains_get_or_browse = True

    def dump_storage_vectors(self, timeout=60):
        """ dumps the local storage vectors (flash, localStorage, cookies) to db """
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("Not get or browse request preceding the dump storage vectors command", self)
        command = ('DUMP_STORAGE_VECTORS', self.url)
        self.commands.append((command, timeout))

    def dump_profile(self, dump_folder, close_webdriver=False, compress=True, timeout=120):
        self.total_timeout += timeout
        """ dumps from the profile path to a given file (absolute path) """
        command = ('DUMP_PROF', dump_folder, close_webdriver, compress)
        self.commands.append((command, timeout))

    def extract_links(self, timeout=30):
        self.total_timeout += timeout
        command = ('EXTRACT_LINKS',)
        self.commands.append((command, timeout))