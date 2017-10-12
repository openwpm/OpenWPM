# utility functions for cookie banner notice detection
from __future__ import print_function
from __future__ import absolute_import
import lxml.html
from time import time
from os import path, makedirs
from collections import namedtuple, Counter
try:
    from urllib import urlretrieve  # py2
except ImportError:
    from urllib.request import urlretrieve  # py3

from ...utilities.domain_utils import hostname_subparts


def fetch_banner_list(output_directory):
    """ Saves an updated "I don't care about cookies" banner list to the specified directory.
    <output_directory> - The directory to save lists to. Will be created if it
                         does not already exist.
    """
    output_directory = path.expanduser(output_directory)
    if not path.isdir(output_directory):
        print("Output directory %s does not exist, creating." % output_directory)
        makedirs(output_directory)

    banner_list_url = "https://www.i-dont-care-about-cookies.eu/abp/"
    urlretrieve(banner_list_url, path.join(output_directory, 'bannerlist.txt'))


def parse_banner_list(banner_list_loc):
    """Parse the banner selectors in the bannerlist and return them as a dictionary of lists.
    """
    filterlist = {}  # dictionary of {domain: list of banner selectors}

    with open(banner_list_loc) as f:
        for line in f:
            if line.startswith('!'):
                continue

            # AdBlock's filter rules are complex, but we only care about a subset:
            # element hiding rules.  These rules are denoted by the symbol "##".
            # (see: https://adblockplus.org/en/filter-cheatsheet#elementhiding)
            if "##" in line:
                domains, selectors = line.strip().split("##")

                # Commas denote a list of domains and selectors.
                domains = [s.strip() for s in domains.split(",")]
                selectors = [s.strip() for s in selectors.split(",")]

                for domain in domains:
                    assert not domain.startswith('~')  # currently unsupported
                    domain = '__global__' if domain == '' else domain
                    filterlist.setdefault(domain, []).extend(selectors)
            else:
                # the rest appear to be rules to block scripts
                filterlist.setdefault('__unknown__', []).append(line.strip())

    return filterlist


def find_banners_by_selectors(page_url, page_html, banner_list_loc, logger=None):
    """ Finds cookie-notice/cookie-wall banners on an HTML page using CSS selectors. The
    selectors are collected by the browser extension "I don't care about cookies".

    Args:
        page_url: URL of the webpage, used to add domain-specific selectors
        page_html: HTML of the webpage
        banner_list_loc: location of selector file (ABP filter-list style)
        logger: optional paramter to report progress; if None, stdout is used
    Returns:
        Tuple: (number of selectors, list of banner elements)
        The banners are in a named tuple (selector, element-tag, element-id, banner-text)

    Notes:
        Since the selectors are collected using crowd-sourcing, and thus might miss sites.
        There are additional false-negatives and false-positive problems as well, but the
        overall  accuracy is high for well-known sites (>90%).

        The false-negatives are caused by banners created using javascript redirects, which
        the extension detects, but are not in their ABP filter list (e.g. see dumpert.nl).
        The false-positives are multiple matches (e.g. nu.nl) or matches to invisible elements
        (e.g. faz.net).

        The speed of this function varies based on the passed HTML -- from a few seconds to
        almost a minute.
    """
    time0 = time()
    log_func = logger.info if logger else print

    # Combine domain-specific CSS selectors (if there is one) with the general
    banner_list = parse_banner_list(banner_list_loc)  # pretty fast, caching not needed
    domains, selectors = [], []
    if page_url:
        domains = hostname_subparts(page_url)
        for domain in domains:
            selectors += banner_list.get(domain, [])
    selectors += banner_list["__global__"]

    SE = namedtuple('SelectedElement', ['selector', 'tag', 'id', 'text'])
    seen, banners = set(), []
    doc = lxml.html.fromstring(page_html)

    for i, css in enumerate(selectors):
        time1 = time()
        match = doc.cssselect(css)  # doesn't seem to raise an exception
        if time() - time1 >= 0.03:
            log_func("find_banners_by_selectors: SLOW cssselect(#%d '%s') => %0.3fs" %
                     (i+1, css, time()-time1))
        if match and len(match) > 10:
            log_func("find_banners_by_selectors: MANY cssselect(#%d '%s') => %d matches" %
                     (i+1, css, len(match)))
        for elem in match:
            if len(match) > 10 and elem.tag in ('a', 'li', 'strong'):
                # skip some tags if this returns too large...
                # alternatively:only keep divs; / decide based on attrs / fully ignore if > 100
                continue
            if elem not in seen:
                seen.add(elem)
                banners.append(SE(selector=css,
                                  tag=elem.tag,
                                  id=elem.attrib.get('id', ''),
                                  text=elem.text_content()))

    count_by_tag = Counter([b.tag for b in banners])
    log_func("find_banners_by_selectors(%.f KB, %d selectors, %s) => %s in %0.1fs" %
             (len(page_html)/1024, len(selectors), domains, count_by_tag, time()-time0))

    return len(selectors), banners
