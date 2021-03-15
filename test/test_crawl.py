"""Runs a short test crawl.

This should be used to test any features that require real crawl data.
This should be avoided if possible, as controlled tests will be easier
to debug.
"""

import os
import tarfile

import domain_utils as du
import pytest

from openwpm.utilities import db_utils

TEST_SITES = [
    "http://google.com",
    "http://facebook.com",
    "http://youtube.com",
    "http://yahoo.com",
    "http://baidu.com",
    "http://wikipedia.org",
    "http://qq.com",
    "http://linkedin.com",
    "http://taobao.com",
    "http://twitter.com",
    "http://live.com",
    "http://amazon.com",
    "http://sina.com.cn",
    "http://google.co.in",
    "http://hao123.com",
    "http://blogspot.com",
    "http://weibo.com",
    "http://wordpress.com",
    "http://yandex.ru",
    "http://yahoo.co.jp",
]


def get_public_suffix(url):
    url_parts = du.hostname_subparts(url, include_ps=True)
    return url_parts[-1]


@pytest.mark.skipif(
    "CI" not in os.environ or os.environ["CI"] == "false",
    reason="Makes remote connections",
)
@pytest.mark.slow
def test_browser_profile_coverage(default_params, task_manager_creator):
    """Test the coverage of the browser's profile.

    This verifies that Firefox's places.sqlite database contains all
    visited sites (with a few exceptions). If it does not, it is likely
    the profile is lost at some point during the crawl.
    """
    # Run the test crawl
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    browser_params[0].profile_archive_dir = (
        manager_params.data_directory / "browser_profile"
    )
    browser_params[0].http_instrument = True
    manager, crawl_db = task_manager_creator((manager_params, browser_params[:1]))
    for site in TEST_SITES:
        manager.get(site)
    manager.close()

    # Extract crawl profile
    ff_db_tar = browser_params[0].profile_archive_dir / "profile.tar.gz"
    with tarfile.open(ff_db_tar) as tar:
        tar.extractall(browser_params[0].profile_archive_dir)

    # Output databases
    ff_db = browser_params[0].profile_archive_dir / "places.sqlite"

    # Grab urls from crawl database
    rows = db_utils.query_db(crawl_db, "SELECT url FROM http_requests")
    req_ps = set()  # visited domains from http_requests table
    for (url,) in rows:
        req_ps.add(get_public_suffix(url))

    hist_ps = set()  # visited domains from crawl_history Table
    statuses = dict()
    rows = db_utils.query_db(
        crawl_db,
        "SELECT arguments, command_status FROM crawl_history WHERE command='GET'",
    )
    for url, command_status in rows:
        ps = get_public_suffix(url)
        hist_ps.add(ps)
        statuses[ps] = command_status

    # Grab urls from Firefox database
    profile_ps = set()  # visited domains from firefox profile
    rows = db_utils.query_db(ff_db, "SELECT url FROM moz_places")
    for (host,) in rows:
        try:
            profile_ps.add(get_public_suffix(host))
        except AttributeError:
            pass

    # We expect a url to be in the Firefox profile if:
    # 1. We've made requests to it
    # 2. The url is a top_url we entered into the address bar
    # 3. The url successfully loaded (see: Issue #40)
    # 4. The site does not respond to the initial request with a 204
    #    (won't show in FF DB)
    missing_urls = req_ps.intersection(hist_ps).difference(profile_ps)
    unexpected_missing_urls = set()
    for url in missing_urls:
        if command_status[url] != "ok":
            continue

        # Get the visit id for the url
        rows = db_utils.query_db(
            crawl_db,
            "SELECT visit_id FROM site_visits WHERE site_url = ?",
            ("http://" + url,),
        )
        visit_id = rows[0]

        rows = db_utils.query_db(
            crawl_db,
            "SELECT COUNT(*) FROM http_responses WHERE visit_id = ?",
            (visit_id,),
        )
        if rows[0] > 1:
            continue

        rows = db_utils.query_db(
            crawl_db,
            "SELECT response_status, location FROM "
            "http_responses WHERE visit_id = ?",
            (visit_id,),
        )
        response_status, location = rows[0]
        if response_status == 204:
            continue
        if location == "http://":  # site returned a blank redirect
            continue
        unexpected_missing_urls.add(url)

    assert len(unexpected_missing_urls) == 0
