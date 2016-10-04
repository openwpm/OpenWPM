from Errors import CommandExecutionError

class CommandSequence:
    """A CommandSequence wraps a series of commands to be performed
    on a visit to one top-level site into one logical
    "site visit," keyed by a visit id. An example of a CommandSequence
    that visits a page and dumps cookies modified on that visit would be:

    sequence = CommandSequence(url)
    sequence.get()
    sequence.dump_profile_cookies()
    task_manager.execute_command_sequence(sequence)

    CommandSequence guarantees that a series of commands will be performed
    by a single browser instance.
    """

    def __init__(self, url, reset=False):
        """Nothing to do here"""
        self.url = url
        self.reset = reset
        self.commands_with_timeout = []
        self.total_timeout = 0
        self.contains_get_or_browse = False

    def get(self, sleep=0, timeout=60):
        """ goes to a url """
        self.total_timeout += timeout
        command = ('GET', self.url, sleep)
        self.commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True

    def browse(self, num_links = 2, sleep=0, timeout=60):
        """ browse a website and visit <num_links> links on the page """
        self.total_timeout += timeout
        command = ('BROWSE', self.url, num_links, sleep)
        self.commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True

    def dump_flash_cookies(self, timeout=60):
        """ dumps the local storage vectors (flash, localStorage, cookies) to db
        Side effect: closes the current tab."""
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the dump storage vectors command", self)
        command = ('DUMP_FLASH_COOKIES',)
        self.commands_with_timeout.append((command, timeout))

    def dump_profile_cookies(self, timeout=60):
        """ dumps from the profile path to a given file (absolute path)
        Side effect: closes the current tab."""
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the dump storage vectors command", self)
        command = ('DUMP_PROFILE_COOKIES',)
        self.commands_with_timeout.append((command, timeout))

    def dump_profile(self, dump_folder, close_webdriver=False, compress=True, timeout=120):
        """ dumps from the profile path to a given file (absolute path) """
        self.total_timeout += timeout
        command = ('DUMP_PROF', dump_folder, close_webdriver, compress)
        self.commands_with_timeout.append((command, timeout))

    def extract_links(self, timeout=30):
        """Extracts links found on web page and dumps them externally"""
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the dump storage vectors command", self)
        command = ('EXTRACT_LINKS',)
        self.commands_with_timeout.append((command, timeout))

    def save_screenshot(self, timeout=30):
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the save screenshot command", self)
        command = ('SAVE_SCREENSHOT',)
        self.commands_with_timeout.append((command, timeout))

    def dump_page_source(self, timeout=30):
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the dump page source command", self)
        command = ('DUMP_PAGE_SOURCE',)
        self.commands_with_timeout.append((command, timeout))


