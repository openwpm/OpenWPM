from pathlib import Path
from typing import Callable, List, Tuple

from .commands.browser_commands import (
    BrowseCommand,
    DumpPageSourceCommand,
    FinalizeCommand,
    GetCommand,
    InitializeCommand,
    RecursiveDumpPageSourceCommand,
    SaveScreenshotCommand,
    ScreenshotFullPageCommand,
)
from .commands.profile_commands import DumpProfileCommand
from .commands.types import BaseCommand
from .errors import CommandExecutionError


class CommandSequence:
    """A CommandSequence wraps a series of commands to be performed
    on a visit to one top-level site into one logical
    "site visit," keyed by a visit id. An example of a CommandSequence
    that visits a page and saves a screenshot of it would be:

    sequence = CommandSequence(url)
    sequence.get()
    sequence.save_screenshot()
    task_manager.execute_command_sequence(sequence)

    CommandSequence guarantees that a series of commands will be performed
    by a single browser instance.
    """

    def __init__(
        self,
        url: str,
        reset: bool = False,
        blocking: bool = False,
        retry_number: int = None,
        site_rank: int = None,
        callback: Callable[[bool], None] = None,
    ) -> None:
        """Initialize command sequence.

        Parameters
        ----------
        url : string
            url of page visit the command sequence should execute on
        reset : bool, optional
            True if browser should clear state and restart after sequence
        blocking : bool, optional
            True if sequence should block parent process during execution
        retry_number : int, optional
            Integer denoting the number of attempts that have been made to
            execute this command. Will be saved in `crawl_history`.
        site_rank : int, optional
            Integer indicating the ranking of the page to visit, saved
            to `site_visits`
        callback :
            A callback to be invoked once all data regarding this
            CommandSequence has been saved out or it has been interrupted.
            If the command sequence completes and all data is saved
            successfully, `True` will be passed to the callback.
            Otherwise `False` will be passed. A value of `False` indicates
            that the data saved from the site visit may be incomplete or empty.
        """
        self.url = url
        self.reset = reset
        self.blocking = blocking
        self.retry_number = retry_number
        self._commands_with_timeout: List[Tuple[BaseCommand, int]] = []
        self.total_timeout = 0
        self.contains_get_or_browse = False
        self.site_rank = site_rank
        self.callback = callback

    def get(self, sleep=0, timeout=60):
        """goes to a url"""
        self.total_timeout += timeout
        command = GetCommand(self.url, sleep)
        self._commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True

    def browse(self, num_links=2, sleep=0, timeout=60):
        """browse a website and visit <num_links> links on the page"""
        self.total_timeout += timeout
        command = BrowseCommand(self.url, num_links, sleep)
        self._commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True

    def dump_profile(
        self,
        tar_path: Path,
        close_webdriver: bool = False,
        compress: bool = True,
        timeout: int = 120,
    ) -> None:
        """dumps from the profile path to a given file (absolute path)"""
        self.total_timeout += timeout
        command = DumpProfileCommand(tar_path, close_webdriver, compress)
        self._commands_with_timeout.append((command, timeout))

    def save_screenshot(self, suffix="", timeout=30):
        """Save a screenshot of the current viewport."""
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError(
                "No get or browse request preceding the save screenshot command",
                self,
            )
        command = SaveScreenshotCommand(suffix)
        self._commands_with_timeout.append((command, timeout))

    def screenshot_full_page(self, suffix="", timeout=30):
        """Save a screenshot of the entire page.

        NOTE: geckodriver v0.15 only supports viewport screenshots. To
        screenshot the entire page we scroll the page using javascript and take
        a viewport screenshot at each location. This method will save the
        parts and a stitched version in the `screenshot_path`. We only scroll
        vertically, so pages that are wider than the viewport will be clipped.
        See: https://github.com/mozilla/geckodriver/issues/570

        The screenshot produced will only include the area originally
        loaded at the start of the command. Sites which dynamically expand as
        the page is scrolled (i.e. infinite scroll) will only go as far as the
        original height.

        NOTE: In geckodriver v0.15 doing any scrolling (or having devtools
        open) seems to break element-only screenshots. So using this command
        will cause any future element-only screenshots to be mis-aligned
        """
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError(
                "No get or browse request preceding the screenshot full page command",
                self,
            )
        command = ScreenshotFullPageCommand(suffix)
        self._commands_with_timeout.append((command, timeout))

    def dump_page_source(self, suffix="", timeout=30):
        """Dumps rendered source of current page to 'sources' directory."""
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError(
                "No get or browse request preceding the dump page source command",
                self,
            )
        command = DumpPageSourceCommand(suffix)
        self._commands_with_timeout.append((command, timeout))

    def recursive_dump_page_source(self, suffix="", timeout=30):
        """Dumps rendered source of current page visit to 'sources' dir.
        Unlike `dump_page_source`, this includes iframe sources. Archive is
        stored in `manager_params.source_dump_path` and is keyed by the
        current `visit_id` and top-level url. The source dump is a gzipped json
        file with the following structure:
        {
            'document_url': "http://example.com",
            'source': "<html> ... </html>",
            'iframes': {
                'frame_1': {'document_url': ...,
                            'source': ...,
                            'iframes: { ... }},
                'frame_2': {'document_url': ...,
                            'source': ...,
                            'iframes: { ... }},
                'frame_3': { ... }
            }
        }
        """
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError(
                "No get or browse request preceding the recursive dump"
                " page source command",
                self,
            )
        command = RecursiveDumpPageSourceCommand(suffix)
        self._commands_with_timeout.append((command, timeout))

    def append_command(self, command: BaseCommand, timeout: int = 30) -> None:
        self._commands_with_timeout.append((command, timeout))

    def mark_done(self, success: bool) -> None:
        if self.callback is not None:
            self.callback(success)

    def get_commands_with_timeout(self) -> List[Tuple[BaseCommand, int]]:
        """Returns a list of all commands in the command_sequence
        appended by a finalize command
        """
        commands = list(self._commands_with_timeout)
        commands.insert(0, (InitializeCommand(), 10))
        commands.append((FinalizeCommand(sleep=5), 10))
        return commands
