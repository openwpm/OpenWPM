"""Test correctness of simple commands and check
that resulting data is properly keyed.

This entire test class is parametrized to run against
both headless and xvfb modes to ensure both are exercised
during the test suite and there are no obvious problems.
"""
import glob
import gzip
import json
import os
import re
from urllib.parse import urlparse

import pytest
from PIL import Image

from openwpm import command_sequence
from openwpm.utilities import db_utils

from . import utilities

url_a = utilities.BASE_TEST_URL + "/simple_a.html"
url_b = utilities.BASE_TEST_URL + "/simple_b.html"
url_c = utilities.BASE_TEST_URL + "/simple_c.html"
url_d = utilities.BASE_TEST_URL + "/simple_d.html"

rendered_js_url = utilities.BASE_TEST_URL + "/property_enumeration.html"

# Expected nested page source
# This needs to be changed back once #887 is addressed

NESTED_TEST_DIR = "/recursive_iframes/"
NESTED_FRAMES_URL = utilities.BASE_TEST_URL + NESTED_TEST_DIR + "parent.html"
D1_BASE = utilities.BASE_TEST_URL + NESTED_TEST_DIR
D2_BASE = utilities.BASE_TEST_URL + NESTED_TEST_DIR
D3_BASE = utilities.BASE_TEST_URL + NESTED_TEST_DIR
D4_BASE = utilities.BASE_TEST_URL + NESTED_TEST_DIR
D5_BASE = utilities.BASE_TEST_URL + NESTED_TEST_DIR
EXPECTED_PARENTS = {
    NESTED_FRAMES_URL: [],
    D1_BASE + "child1a.html": [NESTED_FRAMES_URL],
    D1_BASE + "child1b.html": [NESTED_FRAMES_URL],
    D1_BASE + "child1c.html": [NESTED_FRAMES_URL],
    D2_BASE + "child2a.html": [NESTED_FRAMES_URL, D1_BASE + "child1a.html"],
    D2_BASE + "child2b.html": [NESTED_FRAMES_URL, D1_BASE + "child1a.html"],
    D2_BASE + "child2c.html": [NESTED_FRAMES_URL, D1_BASE + "child1c.html"],
    D3_BASE
    + "child3a.html": [
        NESTED_FRAMES_URL,
        D1_BASE + "child1a.html",
        D2_BASE + "child2a.html",
    ],
    D3_BASE
    + "child3b.html": [
        NESTED_FRAMES_URL,
        D1_BASE + "child1c.html",
        D2_BASE + "child2c.html",
    ],
    D3_BASE
    + "child3c.html": [
        NESTED_FRAMES_URL,
        D1_BASE + "child1c.html",
        D2_BASE + "child2c.html",
    ],
    D3_BASE
    + "child3d.html": [
        NESTED_FRAMES_URL,
        D1_BASE + "child1c.html",
        D2_BASE + "child2c.html",
    ],
    D4_BASE
    + "child4a.html": [
        NESTED_FRAMES_URL,
        D1_BASE + "child1a.html",
        D2_BASE + "child2a.html",
        D3_BASE + "child3a.html",
    ],
    D5_BASE
    + "child5a.html": [
        NESTED_FRAMES_URL,
        D1_BASE + "child1a.html",
        D2_BASE + "child2a.html",
        D3_BASE + "child3a.html",
        D4_BASE + "child4a.html",
    ],
}


scenarios = [
    pytest.param("headless", id="headless"),
    pytest.param("xvfb", id="xvfb"),
]


@pytest.mark.parametrize("display_mode", scenarios)
def test_get_site_visits_table_valid(http_params, task_manager_creator, display_mode):
    """Check that get works and populates db correctly."""
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, db = task_manager_creator((manager_params, browser_params))

    # Set up two sequential get commands to two URLS
    cs_a = command_sequence.CommandSequence(url_a)
    cs_a.get(sleep=1)
    cs_b = command_sequence.CommandSequence(url_b)
    cs_b.get(sleep=1)

    # Perform the get commands
    manager.execute_command_sequence(cs_a)
    manager.execute_command_sequence(cs_b)
    manager.close()

    qry_res = db_utils.query_db(
        db,
        "SELECT site_url FROM site_visits ORDER BY site_url",
    )

    # We had two separate page visits
    assert len(qry_res) == 2

    assert qry_res[0][0] == url_a
    assert qry_res[1][0] == url_b


@pytest.mark.parametrize("display_mode", scenarios)
def test_get_http_tables_valid(http_params, task_manager_creator, display_mode):
    """Check that get works and populates http tables correctly."""
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, db = task_manager_creator((manager_params, browser_params))

    # Set up two sequential get commands to two URLS
    cs_a = command_sequence.CommandSequence(url_a)
    cs_a.get(sleep=1)
    cs_b = command_sequence.CommandSequence(url_b)
    cs_b.get(sleep=1)

    manager.execute_command_sequence(cs_a)
    manager.execute_command_sequence(cs_b)
    manager.close()

    qry_res = db_utils.query_db(db, "SELECT visit_id, site_url FROM site_visits")

    # Construct dict mapping site_url to visit_id
    visit_ids = dict()
    for row in qry_res:
        visit_ids[row[1]] = row[0]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_requests WHERE url = ?",
        (url_a,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_requests WHERE url = ?",
        (url_b,),
    )
    assert qry_res[0][0] == visit_ids[url_b]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_a,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_b,),
    )
    assert qry_res[0][0] == visit_ids[url_b]


@pytest.mark.parametrize("display_mode", scenarios)
def test_browse_site_visits_table_valid(
    http_params, task_manager_creator, display_mode
):
    """Check that CommandSequence.browse() populates db correctly."""
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, db = task_manager_creator((manager_params, browser_params))

    # Set up two sequential browse commands to two URLS
    cs_a = command_sequence.CommandSequence(url_a, site_rank=0)
    cs_a.browse(num_links=1, sleep=1)
    cs_b = command_sequence.CommandSequence(url_b, site_rank=1)
    cs_b.browse(num_links=1, sleep=1)

    manager.execute_command_sequence(cs_a)
    manager.execute_command_sequence(cs_b)
    manager.close()

    qry_res = db_utils.query_db(
        db,
        "SELECT site_url, site_rank FROM site_visits ORDER BY site_rank",
    )

    # We had two separate page visits
    assert len(qry_res) == 2

    assert qry_res[0][0] == url_a
    assert qry_res[0][1] == 0
    assert qry_res[1][0] == url_b
    assert qry_res[1][1] == 1


@pytest.mark.parametrize("display_mode", scenarios)
def test_browse_http_table_valid(http_params, task_manager_creator, display_mode):
    """Check CommandSequence.browse() works and populates http tables correctly.

    NOTE: Since the browse command is choosing links randomly, there is a
          (very small -- 2*0.5^20) chance this test will fail with valid
          code.
    """
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, db = task_manager_creator((manager_params, browser_params))

    # Set up two sequential browse commands to two URLS
    cs_a = command_sequence.CommandSequence(url_a)
    cs_a.browse(num_links=20, sleep=1)
    cs_b = command_sequence.CommandSequence(url_b)
    cs_b.browse(num_links=1, sleep=1)

    manager.execute_command_sequence(cs_a)
    manager.execute_command_sequence(cs_b)
    manager.close()

    qry_res = db_utils.query_db(db, "SELECT visit_id, site_url FROM site_visits")

    # Construct dict mapping site_url to visit_id
    visit_ids = dict()
    for row in qry_res:
        visit_ids[row[1]] = row[0]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_requests WHERE url = ?",
        (url_a,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_requests WHERE url = ?",
        (url_b,),
    )
    assert qry_res[0][0] == visit_ids[url_b]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_a,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_b,),
    )
    assert qry_res[0][0] == visit_ids[url_b]

    # Page simple_a.html has three links:
    # 1) An absolute link to simple_c.html
    # 2) A relative link to simple_d.html
    # 3) A javascript: link
    # 4) A link to www.google.com
    # 5) A link to example.com?localhost
    # We should see page visits for 1 and 2, but not 3-5.
    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_c,),
    )
    assert qry_res[0][0] == visit_ids[url_a]
    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_d,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    # We expect 4 urls: a,c,d and a favicon request
    qry_res = db_utils.query_db(
        db,
        "SELECT COUNT(DISTINCT url) FROM http_responses WHERE visit_id = ?",
        (visit_ids[url_a],),
    )
    assert qry_res[0][0] == 4


@pytest.mark.parametrize("display_mode", scenarios)
def test_browse_wrapper_http_table_valid(
    http_params, task_manager_creator, display_mode
):
    """Check that TaskManager.browse() wrapper works and populates
    http tables correctly.

    NOTE: Since the browse command is choosing links randomly, there is a
          (very small -- 2*0.5^20) chance this test will fail with valid
          code.
    """
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, db = task_manager_creator((manager_params, browser_params))

    # Set up two sequential browse commands to two URLS
    manager.browse(url_a, num_links=20, sleep=1)
    manager.browse(url_b, num_links=1, sleep=1)
    manager.close()

    qry_res = db_utils.query_db(db, "SELECT visit_id, site_url FROM site_visits")

    # Construct dict mapping site_url to visit_id
    visit_ids = dict()
    for row in qry_res:
        visit_ids[row[1]] = row[0]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_requests WHERE url = ?",
        (url_a,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_requests WHERE url = ?",
        (url_b,),
    )
    assert qry_res[0][0] == visit_ids[url_b]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_a,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_b,),
    )
    assert qry_res[0][0] == visit_ids[url_b]

    # Page simple_a.html has three links:
    # 1) An absolute link to simple_c.html
    # 2) A relative link to simple_d.html
    # 3) A javascript: link
    # 4) A link to www.google.com
    # 5) A link to example.com?localhost
    # We should see page visits for 1 and 2, but not 3-5.
    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_c,),
    )
    assert qry_res[0][0] == visit_ids[url_a]
    qry_res = db_utils.query_db(
        db,
        "SELECT visit_id FROM http_responses WHERE url = ?",
        (url_d,),
    )
    assert qry_res[0][0] == visit_ids[url_a]

    # We expect 4 urls: a,c,d and a favicon request
    qry_res = db_utils.query_db(
        db,
        "SELECT COUNT(DISTINCT url) FROM http_responses WHERE visit_id = ?",
        (visit_ids[url_a],),
    )
    assert qry_res[0][0] == 4


@pytest.mark.parametrize("display_mode", scenarios)
def test_save_screenshot_valid(http_params, task_manager_creator, display_mode):
    """Check that 'save_screenshot' works"""
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, _ = task_manager_creator((manager_params, browser_params))

    cs = command_sequence.CommandSequence(url_a)
    cs.get(sleep=1)
    cs.save_screenshot("test")
    cs.screenshot_full_page("test_full")
    manager.execute_command_sequence(cs)
    manager.close()

    # Check that viewport image is not blank
    pattern = os.path.join(manager_params.data_directory, "screenshots", "*-*-test.png")
    screenshot = glob.glob(pattern)[0]
    im = Image.open(screenshot)
    bands = im.split()
    is_blank = all(band.getextrema() == (255, 255) for band in bands)
    assert not is_blank

    # Check that full page screenshot is not blank
    pattern = os.path.join(
        manager_params.data_directory, "screenshots", "*-*-test_full.png"
    )
    screenshot = glob.glob(pattern)[0]
    im = Image.open(screenshot)
    bands = im.split()
    is_blank = all(band.getextrema() == (255, 255) for band in bands)
    assert not is_blank


@pytest.mark.parametrize("display_mode", scenarios)
def test_dump_page_source_valid(http_params, task_manager_creator, display_mode):
    """Check that 'dump_page_source' works and source is saved properly."""
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, db = task_manager_creator((manager_params, browser_params))

    cs = command_sequence.CommandSequence(url_a)
    cs.get(sleep=1)
    cs.dump_page_source(suffix="test")
    manager.execute_command_sequence(cs)
    manager.close()

    # Source filename is of the follow structure:
    # `sources/<visit_id>-<md5_of_url>(-suffix).html`
    # thus for this test we expect `sources/1-<md5_of_test_url>-test.html`.
    outfile = os.path.join(manager_params.data_directory, "sources", "*-*-test.html")
    source_file = glob.glob(outfile)[0]
    with open(source_file, "rb") as f:
        actual_source = f.read()
    with open("./test_pages/expected_source.html", "rb") as f:
        expected_source = f.read()

    assert actual_source == expected_source


@pytest.mark.parametrize("display_mode", scenarios)
def test_recursive_dump_page_source_valid(
    http_params, task_manager_creator, display_mode
):
    """Check that 'recursive_dump_page_source' works"""
    # Run the test crawl
    manager_params, browser_params = http_params(display_mode)
    manager, db = task_manager_creator((manager_params, browser_params))
    cs = command_sequence.CommandSequence(NESTED_FRAMES_URL)
    cs.get(sleep=1)
    cs.recursive_dump_page_source()
    manager.execute_command_sequence(cs)
    manager.close()

    outfile = os.path.join(manager_params.data_directory, "sources", "*-*.json.gz")
    src_file = glob.glob(outfile)[0]
    with gzip.GzipFile(src_file, "rb") as f:
        visit_source = json.loads(f.read().decode("utf-8"))

    observed_parents = dict()

    def verify_frame(frame, parent_frames=[]):
        # Verify structure
        observed_parents[frame["doc_url"]] = list(parent_frames)  # copy

        # Verify source
        path = urlparse(frame["doc_url"]).path
        expected_source = ""
        with open("." + path, "r") as f:
            expected_source = re.sub(r"\s", "", f.read().lower())
            if expected_source.startswith("<!doctypehtml>"):
                expected_source = expected_source[14:]
        observed_source = re.sub(r"\s", "", frame["source"].lower())
        if observed_source.startswith("<!doctypehtml>"):
            observed_source = observed_source[14:]
        assert observed_source == expected_source

        # Verify children
        parent_frames.append(frame["doc_url"])
        for key, child_frame in frame["iframes"].items():
            verify_frame(child_frame, parent_frames)
        parent_frames.pop()

    verify_frame(visit_source)
    assert EXPECTED_PARENTS == observed_parents
