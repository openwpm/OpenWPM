import gzip
import json
import logging
import os
import random
import sys
import time
import traceback
from glob import glob
from hashlib import md5

from PIL import Image
from selenium.common.exceptions import (
    MoveTargetOutOfBoundsException,
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException
)
from selenium.webdriver import Firefox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..config import BrowserParams, ManagerParams
from ..socket_interface import ClientSocket
from .types import BaseCommand
from .utils.webdriver_utils import (
    execute_in_all_frames,
    execute_script_with_retry,
    get_intra_links,
    is_displayed,
    scroll_down,
    wait_until_loaded,
)

from urllib.parse import urlparse, urldefrag
from selenium.webdriver.common.by import By

# Constants for bot mitigation
NUM_MOUSE_MOVES = 10  # Times to randomly move the mouse
RANDOM_SLEEP_LOW = 1  # low (in sec) for random sleep between page loads
RANDOM_SLEEP_HIGH = 7  # high (in sec) for random sleep between page loads
logger = logging.getLogger("openwpm")


def bot_mitigation(webdriver):
    """Performs three optional commands for bot-detection mitigation when getting a site"""

    # bot mitigation 1: move the randomly around a number of times
    window_size = webdriver.get_window_size()
    num_moves = 0
    num_fails = 0
    while num_moves < NUM_MOUSE_MOVES + 1 and num_fails < NUM_MOUSE_MOVES:
        try:
            if num_moves == 0:  # move to the center of the screen
                x = int(round(window_size["height"] / 2))
                y = int(round(window_size["width"] / 2))
            else:  # move a random amount in some direction
                move_max = random.randint(0, 500)
                x = random.randint(-move_max, move_max)
                y = random.randint(-move_max, move_max)
            action = ActionChains(webdriver)
            action.move_by_offset(x, y)
            action.perform()
            num_moves += 1
        except MoveTargetOutOfBoundsException:
            num_fails += 1
            pass

    # bot mitigation 2: scroll in random intervals down page
    scroll_down(webdriver)

    # bot mitigation 3: randomly wait so page visits happen with irregularity
    time.sleep(random.randrange(RANDOM_SLEEP_LOW, RANDOM_SLEEP_HIGH))


def close_other_windows(webdriver):
    """
    close all open pop-up windows and tabs other than the current one
    """
    main_handle = webdriver.current_window_handle
    windows = webdriver.window_handles
    if len(windows) > 1:
        for window in windows:
            if window != main_handle:
                webdriver.switch_to.window(window)
                webdriver.close()
        webdriver.switch_to.window(main_handle)


def tab_restart_browser(webdriver):
    """kills the current tab and creates a new one to stop traffic"""
    # note: this technically uses windows, not tabs, due to problems with
    # chrome-targeted keyboard commands in Selenium 3 (intermittent
    # nonsense WebDriverExceptions are thrown). windows can be reliably
    # created, although we do have to detour into JS to do it.
    close_other_windows(webdriver)

    if webdriver.current_url.lower() == "about:blank":
        return

    # Create a new window.  Note that it is not practical to use
    # noopener here, as we would then be forced to specify a bunch of
    # other "features" that we don't know whether they are on or off.
    # Closing the old window will kill the opener anyway.
    webdriver.execute_script("window.open('')")

    # This closes the _old_ window, and does _not_ switch to the new one.
    webdriver.close()

    # The only remaining window handle will be for the new window;
    # switch to it.
    assert len(webdriver.window_handles) == 1
    webdriver.switch_to.window(webdriver.window_handles[0])


class GetCommand(BaseCommand):
    """goes to <url> using the given <webdriver> instance"""

    def __init__(self, url, sleep):
        self.url = url
        self.sleep = sleep

    def __repr__(self):
        return "GetCommand({},{})".format(self.url, self.sleep)

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        tab_restart_browser(webdriver)

        if extension_socket is not None:
            extension_socket.send(self.visit_id)

        # Execute a get through selenium
        try:
            webdriver.get(self.url)
        except TimeoutException:
            pass

        # Sleep after get returns
        time.sleep(self.sleep)

        # Close modal dialog if exists
        try:
            WebDriverWait(webdriver, 0.5).until(EC.alert_is_present())
            alert = webdriver.switch_to.alert
            alert.dismiss()
            time.sleep(1)
        except (TimeoutException, WebDriverException):
            pass

        close_other_windows(webdriver)

        if browser_params.bot_mitigation:
            bot_mitigation(webdriver)


class BrowseCommand(BaseCommand):
    def __init__(self, url, num_links, sleep):
        self.url = url
        self.num_links = num_links
        self.sleep = sleep

    def __repr__(self):
        return "BrowseCommand({},{},{})".format(self.url, self.num_links, self.sleep)

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        """Calls get_website before visiting <num_links> present on the page.

        Note: the site_url in the site_visits table for the links visited will
        be the site_url of the original page and NOT the url of the links visited.
        """
        # First get the site
        get_command = GetCommand(self.url, self.sleep)
        get_command.set_visit_browser_id(self.visit_id, self.browser_id)
        get_command.execute(
            webdriver,
            browser_params,
            manager_params,
            extension_socket,
        )

        # Then visit a few subpages
        for _ in range(self.num_links):
            links = [
                x
                for x in get_intra_links(webdriver, self.url)
                if is_displayed(x) is True
            ]
            if not links:
                break
            r = int(random.random() * len(links))
            logger.info(
                "BROWSER %i: visiting internal link %s"
                % (browser_params.browser_id, links[r].get_attribute("href"))
            )

            try:
                links[r].click()
                wait_until_loaded(webdriver, 300)
                time.sleep(max(1, self.sleep))
                if browser_params.bot_mitigation:
                    bot_mitigation(webdriver)
                webdriver.back()
                wait_until_loaded(webdriver, 300)
            except Exception as e:
                logger.error(
                    "BROWSER %i: Error visitit internal link %s",
                    browser_params.browser_id,
                    links[r].get_attribute("href"),
                    exc_info=e,
                )
                pass


class SaveScreenshotCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "SaveScreenshotCommand({})".format(self.suffix)

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        if self.suffix != "":
            self.suffix = "-" + self.suffix

        urlhash = md5(webdriver.current_url.encode("utf-8")).hexdigest()
        outname = os.path.join(
            manager_params.screenshot_path,
            "%i-%s%s.png" % (self.visit_id, urlhash, self.suffix),
        )
        webdriver.save_screenshot(outname)


def _stitch_screenshot_parts(visit_id, browser_id, manager_params):
    # Read image parts and compute dimensions of output image
    total_height = -1
    max_scroll = -1
    max_width = -1
    images = dict()
    parts = list()
    for f in glob(
        os.path.join(
            manager_params.screenshot_path, "parts", "%i*-part-*.png" % visit_id
        )
    ):
        # Load image from disk and parse params out of filename
        img_obj = Image.open(f)
        width, height = img_obj.size
        parts.append((f, width, height))
        outname, _, index, curr_scroll = os.path.basename(f).rsplit("-", 3)
        curr_scroll = int(curr_scroll.split(".")[0])
        index = int(index)

        # Update output image size
        if curr_scroll > max_scroll:
            max_scroll = curr_scroll
            total_height = max_scroll + height

        if width > max_width:
            max_width = width

        # Save image parameters
        img = {}
        img["object"] = img_obj
        img["scroll"] = curr_scroll
        images[index] = img

    # Output filename same for all parts, so we can just use last filename
    outname = outname + ".png"
    outname = os.path.join(manager_params.screenshot_path, outname)
    output = Image.new("RGB", (max_width, total_height))

    # Compute dimensions for output image
    for i in range(max(images.keys()) + 1):
        img = images[i]
        output.paste(im=img["object"], box=(0, img["scroll"]))
        img["object"].close()
    try:
        output.save(outname)
    except SystemError:
        logger.error(
            "BROWSER %i: SystemError while trying to save screenshot %s. \n"
            "Slices of image %s \n Final size %s, %s."
            % (
                browser_id,
                outname,
                "\n".join([str(x) for x in parts]),
                max_width,
                total_height,
            )
        )
        pass


class ScreenshotFullPageCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "ScreenshotFullPageCommand({})".format(self.suffix)

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        self.outdir = os.path.join(manager_params.screenshot_path, "parts")
        if not os.path.isdir(self.outdir):
            os.mkdir(self.outdir)
        if self.suffix != "":
            self.suffix = "-" + self.suffix
        urlhash = md5(webdriver.current_url.encode("utf-8")).hexdigest()
        outname = os.path.join(
            self.outdir,
            "%i-%s%s-part-%%i-%%i.png" % (self.visit_id, urlhash, self.suffix),
        )

        try:
            part = 0
            max_height = execute_script_with_retry(
                webdriver, "return document.body.scrollHeight;"
            )
            inner_height = execute_script_with_retry(
                webdriver, "return window.innerHeight;"
            )
            curr_scrollY = execute_script_with_retry(
                webdriver, "return window.scrollY;"
            )
            prev_scrollY = -1
            webdriver.save_screenshot(outname % (part, curr_scrollY))
            while (
                curr_scrollY + inner_height
            ) < max_height and curr_scrollY != prev_scrollY:
                # Scroll down to bottom of previous viewport
                try:
                    webdriver.execute_script("window.scrollBy(0, window.innerHeight)")
                except WebDriverException:
                    logger.info(
                        "BROWSER %i: WebDriverException while scrolling, "
                        "screenshot may be misaligned!" % self.browser_id
                    )
                    pass

                # Update control variables
                part += 1
                prev_scrollY = curr_scrollY
                curr_scrollY = execute_script_with_retry(
                    webdriver, "return window.scrollY;"
                )

                # Save screenshot
                webdriver.save_screenshot(outname % (part, curr_scrollY))
        except WebDriverException:
            excp = traceback.format_exception(*sys.exc_info())
            logger.error(
                "BROWSER %i: Exception while taking full page screenshot \n %s"
                % (self.browser_id, "".join(excp))
            )
            return

        _stitch_screenshot_parts(self.visit_id, self.browser_id, manager_params)


class DumpPageSourceCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "DumpPageSourceCommand({})".format(self.suffix)

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        if self.suffix != "":
            self.suffix = "-" + self.suffix

        outname = md5(webdriver.current_url.encode("utf-8")).hexdigest()
        outfile = os.path.join(
            manager_params.source_dump_path,
            "%i-%s%s.html" % (self.visit_id, outname, self.suffix),
        )

        with open(outfile, "wb") as f:
            f.write(webdriver.page_source.encode("utf8"))
            f.write(b"\n")


class RecursiveDumpPageSourceCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "RecursiveDumpPageSourceCommand({})".format(self.suffix)

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        """Dump a compressed html tree for the current page visit"""
        if self.suffix != "":
            self.suffix = "-" + self.suffix

        outname = md5(webdriver.current_url.encode("utf-8")).hexdigest()
        outfile = os.path.join(
            manager_params.source_dump_path,
            "%i-%s%s.json.gz" % (self.visit_id, outname, self.suffix),
        )

        def collect_source(webdriver, frame_stack, rv={}):
            is_top_frame = len(frame_stack) == 1

            # Gather frame information
            doc_url = webdriver.execute_script("return window.document.URL;")
            if is_top_frame:
                page_source = rv
            else:
                page_source = dict()
            page_source["doc_url"] = doc_url
            source = webdriver.page_source
            if type(source) != str:
                source = str(source, "utf-8")
            page_source["source"] = source
            page_source["iframes"] = dict()

            # Store frame info in correct area of return value
            if is_top_frame:
                return
            out_dict = rv["iframes"]
            for frame in frame_stack[1:-1]:
                out_dict = out_dict[frame.id]["iframes"]
            out_dict[frame_stack[-1].id] = page_source

        page_source = dict()
        execute_in_all_frames(webdriver, collect_source, {"rv": page_source})

        with gzip.GzipFile(outfile, "wb") as f:
            f.write(json.dumps(page_source).encode("utf-8"))


class FinalizeCommand(BaseCommand):
    """This command is automatically appended to the end of a CommandSequence

    It's apperance means there won't be any more commands for this
    visit_id
    """

    def __init__(self, sleep):
        self.sleep = sleep

    def __repr__(self):
        return f"FinalizeCommand({self.sleep})"

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        """Informs the extension that a visit is done"""
        tab_restart_browser(webdriver)
        # This doesn't immediately stop data saving from the current
        # visit so we sleep briefly before unsetting the visit_id.
        time.sleep(self.sleep)
        msg = {"action": "Finalize", "visit_id": self.visit_id}
        extension_socket.send(msg)


class InitializeCommand(BaseCommand):
    """The command is automatically prepended to the beginning of a CommandSequence

    It initializes state both in the extensions as well in as the
    StorageController
    """

    def __repr__(self):
        return "InitializeCommand()"

    def execute(
        self,
        webdriver,
        browser_params,
        manager_params,
        extension_socket,
    ):
        msg = {"action": "Initialize", "visit_id": self.visit_id}
        extension_socket.send(msg)


class CrawlCommand(BaseCommand):
    """
    Hybrid BFS --> DFS crawler for realistic, deep website interaction.

    This command simulates human-like browsing behavior on modern websites to capture
    realistic third-party request patterns (ads, analytics, trackers, consent flows,
    paywalls, dynamic content). It uses a two-phase crawling strategy:

    **Phase 1 (BFS):** Collects internal links from the start URL and selects
    `frontier_links` of them as "frontier" entry points. This ensures coverage across
    different site sections (e.g., politics, sports, opinion pages) rather than
    following the first link found.

    **Phase 2 (DFS):** For each frontier link, performs a depth-first search down to
    `max_depth`, exploring `dfs_links` links per level. This creates coherent
    browsing sequences that better trigger dynamic content and third-party requests.

    After each subtree is explored, the crawler returns to the start URL before
    proceeding to the next frontier link.

    **Parameters:**
        url (str): The starting URL to begin the crawl from.

        frontier_links (int, optional): Number of frontier links to select in the BFS
            phase. These represent different top-level sections of the site. Default: 5.

        dfs_links (int, optional): Number of links to explore at each DFS level.
            Controls branching factor during depth-first exploration. Default: 5.

        depth (int, optional): Maximum depth to explore from each frontier link.
            Depth 1 = frontier link only, depth 2 = frontier + one level of children,
            depth 3 = frontier + two levels of children, etc. Default: 2.

        sleep (int, optional): Sleep time in seconds after page loads. Default: 2.

    **Output:**
        Saves a crawl tree visualization to `datadir/crawl-tree-{visit_id}.txt`
        showing the hierarchical structure of visited URLs.

    **Example:**
        ```python
        # Crawl with 10 frontier links, explore 5 links per DFS level, to depth 3
        command = CrawlCommand(
            url="https://example.com",
            frontier_links=10,
            dfs_links=5,
            depth=3,
            sleep=2
        )
        ```

    **Notes:**
        - Uses a global visited set to prevent infinite loops, which may limit
          exploration in later subtrees if many links are already visited.
        - Prefers clicking links over direct navigation when possible for realism.
        - Automatically handles URL normalization (strips fragments) and same-site
          link filtering.
    """

    def __init__(self, url, frontier_links=5, dfs_links=5, depth=2, sleep=2):
        self.start_url = url
        self.frontier_links = frontier_links  # Number of BFS frontier links to select
        self.dfs_links = dfs_links  # Number of links to explore per DFS level
        self.max_depth = depth
        self.sleep = sleep
        self.visited = set()

        # Track crawl tree structure: {parent_url: [child_url, ...]}
        self.crawl_tree = {}

    def __repr__(self):
        return f"CrawlCommand({self.start_url}, frontier={self.frontier_links}, dfs={self.dfs_links}, depth={self.max_depth})"

    # Utils

    def wait_dom(self, driver, timeout=15):
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) in ("interactive", "complete")
            )
        except Exception:
            pass

    def scroll_like_human(self, driver):
        try:
            viewport = driver.execute_script("return window.innerHeight") or 800
            for _ in range(random.randint(3, 6)):
                offset = random.randint(100, viewport // 2)
                driver.execute_script("window.scrollBy(0, arguments[0]);", offset)
                time.sleep(random.uniform(0.2, 0.5))
        except Exception:
            pass

    def safe_get(self, driver, url, timeout=15):
        start = time.time()
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(url)
        except TimeoutException:
            logger.warning(f"GET timeout for {url}")
        except WebDriverException:
            return False

        # HARD STOP if page misbehaves
        if time.time() - start > timeout:
            logger.warning(f"Navigation exceeded {timeout}s, aborting")
            return False

        return True


    def safe_click_or_get(self, driver, href):
        before = driver.current_url
        try:
            el = driver.find_element(By.CSS_SELECTOR, f'a[href="{href}"]')
            el.click()
            self.wait_dom(driver)
            if driver.current_url != before:
                return "CLICK"
        except Exception:
            pass

        self.safe_get(driver, href)
        if driver.current_url != before:
            return "DIRECT"

        return None

    def same_site(self, base_netloc, href):
        try:
            return urlparse(href).netloc.endswith(base_netloc)
        except Exception:
            return False

    def normalize_url(self, url):
        clean, _ = urldefrag(url)
        return clean

    def add_to_tree(self, parent_url, child_url):
        """Add a parent-child relationship to the crawl tree"""
        parent = self.normalize_url(parent_url)
        child = self.normalize_url(child_url)
        if parent not in self.crawl_tree:
            self.crawl_tree[parent] = []
        if child not in self.crawl_tree[parent]:
            self.crawl_tree[parent].append(child)

    def format_tree(self, start_url):
        """Format the crawl tree as a text tree structure"""
        lines = []
        start = self.normalize_url(start_url)
        
        def format_node(url, prefix="", is_last=True, visited=None):
            if visited is None:
                visited = set()
            
            if url in visited:
                return  # Prevent infinite loops in tree display
            visited.add(url)
            
            # Format current node
            connector = "└" if is_last else "├"
            lines.append(f"{prefix}{connector}_____{url}")
            
            # Get children
            children = self.crawl_tree.get(url, [])
            if not children:
                return
            
            # Format children
            for i, child in enumerate(children):
                is_child_last = (i == len(children) - 1)
                child_prefix = prefix + ("    " if is_last else "│   ")
                format_node(child, child_prefix, is_child_last, visited.copy())
        
        # Start with root
        lines.append(start)
        children = self.crawl_tree.get(start, [])
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            format_node(child, "", is_last, {start})
        
        return "\n".join(lines)

    def save_crawl_tree(self, manager_params):
        """Save the crawl tree to a text file"""
        if not self.crawl_tree:
            return
        
        tree_text = self.format_tree(self.start_url)
        
        # Create filename with visit_id
        outname = os.path.join(
            manager_params.data_directory,
            f"crawl-tree-{self.visit_id}.txt"
        )
        
        try:
            with open(outname, "w", encoding="utf-8") as f:
                f.write(f"Crawl Tree for visit_id {self.visit_id}\n")
                f.write(f"Start URL: {self.start_url}\n")
                f.write(f"Frontier links: {self.frontier_links}, DFS links per level: {self.dfs_links}, Max depth: {self.max_depth}\n")
                f.write("=" * 80 + "\n\n")
                f.write(tree_text)
                f.write("\n")
            logger.info(f"BROWSER {self.browser_id}: Saved crawl tree to {outname}")
        except Exception as e:
            logger.error(
                f"BROWSER {self.browser_id}: Failed to save crawl tree: {e}",
                exc_info=True
            )

    # Link extraction
    def extract_links(self, driver, base_netloc):
        raw = get_intra_links(driver, driver.current_url)
        hrefs = []

        for el in raw:
            try:
                href = el.get_attribute("href")
            except Exception:
                continue

            if not href:
                continue

            if not self.same_site(base_netloc, href):
                continue
            if href in self.visited:
                continue

            href = self.normalize_url(href)
            hrefs.append(href)

        # dedupe
        out = []
        seen = set()
        for h in hrefs:
            if h not in seen:
                seen.add(h)
                out.append(h)

        return out


    # DFS inside subtree
    def dfs(self, driver, depth, base_netloc):
        if depth > self.max_depth:
            return

        current = self.normalize_url(driver.current_url)
        logger.info(f"DFS depth {depth}: at {current}")

        # Don't explore children if we're already at max_depth
        if depth >= self.max_depth:
            return

        links = self.extract_links(driver, base_netloc)
        if not links:
            return

        random.shuffle(links)
        links = links[:self.dfs_links]

        for href in links:
            if href in self.visited:
                continue

            self.visited.add(href)
            method = self.safe_click_or_get(driver, href)
            if not method:
                continue

            # Track navigation in tree (current -> actual destination)
            actual_url = self.normalize_url(driver.current_url)
            self.add_to_tree(current, actual_url)

            logger.info(f"DFS depth {depth}: visiting {driver.current_url} via {method}")

            self.dfs(driver, depth + 1, base_netloc)

            # deterministic return
            self.safe_get(driver, current)

    # Entry point
    def execute(self, driver, browser_params, manager_params, extension_socket):
        base_netloc = urlparse(self.start_url).netloc

        # Phase 1: BFS frontier
        self.safe_get(driver, self.start_url)
        logger.info("Collecting BFS frontier")

        frontier = self.extract_links(driver, base_netloc)
        random.shuffle(frontier)
        frontier = frontier[:self.frontier_links]

        logger.info(f"Selected {len(frontier)} frontier links")

        # Phase 2: DFS per subtree
        for i, href in enumerate(frontier, start=1):
            logger.info(f"Starting subtree {i}/{len(frontier)}: {href}")

            self.visited.add(href)
            method = self.safe_click_or_get(driver, href)
            if not method:
                continue

            # Track frontier link in tree
            actual_url = self.normalize_url(driver.current_url)
            self.add_to_tree(self.start_url, actual_url)

            logger.info(f"Subtree root via {method}")

            self.dfs(driver, depth=2, base_netloc=base_netloc)

            # always return home
            self.safe_get(driver, self.start_url)

        # Save crawl tree to file
        self.save_crawl_tree(manager_params)
