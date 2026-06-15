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


# The maximum number of TEST_SITES we tolerate failing to resolve and
# appear in the Firefox profile. A healthy crawl resolves nearly all of
# them; we allow a little headroom for genuine network failures (a couple
# of sites timing out on a CI runner) but still fail loudly if most sites
# are missing from the profile, which is the symptom of a lost/corrupt
# profile.
MAX_TOLERATED_DNS_FAILURES = 3


@pytest.mark.skipif(
    "CI" not in os.environ or os.environ["CI"] == "false",
    reason="Makes remote connections",
)
@pytest.mark.slow
def test_browser_profile_coverage(default_params, task_manager_creator):
    """Test the coverage of the browser's profile.

    This verifies that Firefox's ``places.sqlite`` (``moz_places``)
    contains the sites the crawl actually visited. If it does not, the
    profile was likely lost or corrupted at some point during the crawl.

    Network conditions are not under our control: any TEST_SITE may fail
    to resolve (a transient DNS failure on the CI runner) or may redirect
    to a different eTLD+1. To avoid flaking on those, the per-site profile
    assertion is anchored on the host the browser *actually resolved and
    received a response from*, not on the eTLD+1 of the URL we typed.

    Concretely:

    * A ``dns_responses`` row with a non-empty ``addresses`` field is
      written from the ``onHeadersReceived`` handler, i.e. only after a
      response arrived. Its ``hostname`` is therefore a host that both
      resolved and was successfully requested. We treat that host's
      eTLD+1 as the ground truth for "this site was visited".
    * For each such resolved host we assert its eTLD+1 is present in the
      Firefox profile. ``moz_places`` is written by Firefox itself, so
      this is an independent check on whether the profile survived the
      crawl — it is not implied by the DNS/HTTP instrumentation.
    * Resolving by the *resolved* host (rather than the entered URL)
      sidesteps two network-dependent traps: public-suffix entries and
      redirects to a different eTLD+1. The correctness here does not
      depend on ``get_ps_plus_1`` returning any particular value; it
      relies on internal consistency. The same ``get_ps_plus_1`` is
      applied both to the resolved host and to every ``moz_places`` URL,
      so a host that genuinely landed in the profile matches by
      construction. ``blogspot.com`` is itself a public suffix, so
      ``get_ps_plus_1("blogspot.com")`` returns ``"blogspot.com"``
      verbatim and ``get_ps_plus_1("www.blogspot.com")`` returns the
      same value — whatever the resolved host's eTLD+1 is, it is compared
      against the identically-derived value from the profile.

    A site that never resolved (only timeout/NXDOMAIN rows, or no row at
    all) is silently dropped — that is a network outcome, not a profile
    bug. To stop the test from degrading to "at least one site resolved",
    we tolerate at most ``MAX_TOLERATED_DNS_FAILURES`` of TEST_SITES
    failing to both resolve and appear in the profile.

    This replaces the previous network-dependent check that compared the
    set of requested domains against the profile, which flaked whenever
    Firefox contacted an unexpected domain (see Issue #1163).
    """
    # Run the test crawl
    manager_params, browser_params = default_params
    manager_params.num_browsers = 1
    manager_params.testing = False
    browser_params[0].profile_archive_dir = (
        manager_params.data_directory / "browser_profile"
    )
    browser_params[0].http_instrument = True
    browser_params[0].dns_instrument = True
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

    # Hosts that the browser actually resolved *and* got a response from.
    # A dns_responses row is written from onHeadersReceived (a response
    # arrived) with addresses = record.addresses.toString(); an empty
    # result is the empty string "", so we test truthiness rather than
    # "is not None". The hostname here is the real, resolved host — which
    # may differ from the entered URL after a redirect.
    resolved_hosts = set()
    rows = db_utils.query_db(crawl_db, "SELECT hostname, addresses FROM dns_responses")
    for hostname, addresses in rows:
        if hostname and addresses:
            resolved_hosts.add(hostname)

    # eTLD+1 of every domain recorded in the Firefox profile.
    profile_ps = set()
    rows = db_utils.query_db(ff_db, "SELECT url FROM moz_places")
    for (host,) in rows:
        try:
            profile_ps.add(du.get_ps_plus_1(host))
        except AttributeError:
            pass

    # Map each entered site to the host(s) it actually resolved to, by
    # suffix containment. This handles public-suffix entries (blogspot.com
    # resolving to www.blogspot.com) and redirects within the same domain.
    # An entered site "covered" by a resolved host whose eTLD+1 is in the
    # profile counts toward our coverage floor.
    covered_sites = set()
    for site in TEST_SITES:
        entered_host = du.urlparse(site).hostname or ""
        for resolved_host in resolved_hosts:
            # The resolved host is the entered host itself or a subdomain of
            # it (e.g. entered blogspot.com resolving to www.blogspot.com, or
            # a same-site redirect). A redirect to a *different* eTLD+1 simply
            # leaves this site uncovered, which the floor below tolerates.
            if resolved_host == entered_host or resolved_host.endswith(
                "." + entered_host
            ):
                ps = du.get_ps_plus_1(resolved_host)
                assert ps in profile_ps, (
                    f"{site} resolved to {resolved_host} (eTLD+1 {ps}) and a "
                    f"response was received, but it is missing from the "
                    f"Firefox profile (places.sqlite); the profile may have "
                    f"been lost during the crawl"
                )
                covered_sites.add(site)
                break

    # Floor: a healthy crawl visits and records nearly every site. If most
    # entered sites failed to resolve or never reached the profile, the
    # crawl is broken (e.g. the profile was lost) and the test must fail
    # rather than quietly passing on a single surviving site.
    min_covered = len(TEST_SITES) - MAX_TOLERATED_DNS_FAILURES
    assert len(covered_sites) >= min_covered, (
        f"Only {len(covered_sites)}/{len(TEST_SITES)} entered sites resolved "
        f"and appear in the Firefox profile; expected at least {min_covered}. "
        f"This indicates a broken crawl or a lost profile, not ordinary "
        f"network flakiness. Covered: {sorted(covered_sites)}"
    )
