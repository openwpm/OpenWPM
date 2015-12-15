from publicsuffix import PublicSuffixList, fetch
from urlparse import urlparse
import sqlite3
import tarfile
import codecs
import pytest
import os

from ..automation import TaskManager
from ..automation.Errors import CommandExecutionError, ProfileLoadError

PSL_CACHE_LOC = '/tmp/public_suffix_list.dat'
TEST_SITES = [
    'http://google.com',
    'http://facebook.com',
    'http://youtube.com',
    'http://yahoo.com',
    'http://baidu.com',
    'http://wikipedia.org',
    'http://qq.com',
    'http://linkedin.com',
    'http://taobao.com',
    'http://twitter.com',
    'http://live.com',
    'http://amazon.com',
    'http://sina.com.cn',
    'http://google.co.in',
    'http://hao123.com',
    'http://blogspot.com',
    'http://weibo.com',
    'http://wordpress.com',
    'http://yandex.ru',
    'http://yahoo.co.jp'
]

def get_psl():
    """
    Grabs an updated public suffix list.
    """
    if not os.path.isfile(PSL_CACHE_LOC):
        print "%s does not exist, downloading a copy." % PSL_CACHE_LOC
        psl_file = fetch()
        with codecs.open(PSL_CACHE_LOC, 'w', encoding='utf8') as f:
            f.write(psl_file.read())
    psl_cache = codecs.open(PSL_CACHE_LOC, encoding='utf8')
    return PublicSuffixList(psl_cache)

psl = get_psl()

class TestProfile():
    NUM_BROWSERS = 1

    def get_config(self, data_dir):
        manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        browser_params[0]['profile_archive_dir'] = os.path.join(data_dir,'browser_profile')
        browser_params[0]['headless'] = True
        return manager_params, browser_params

    def test_saving(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get('http://example.com')
        manager.close(post_process=False)
        assert os.path.isfile(os.path.join(browser_params[0]['profile_archive_dir'],'profile.tar.gz'))

    def test_crash(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager_params['failure_limit'] = 0
        manager = TaskManager.TaskManager(manager_params, browser_params)
        with pytest.raises(CommandExecutionError):
            manager.get('http://example.com') # So we have a profile
            manager.get('example.com') # Selenium requires scheme prefix
            manager.get('example.com') # Requires two commands to shut down

    def test_crash_profile(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager_params['failure_limit'] = 2
        manager = TaskManager.TaskManager(manager_params, browser_params)
        try:
            manager.get('http://example.com') # So we have a profile
            manager.get('example.com') # Selenium requires scheme prefix
            manager.get('example.com') # Selenium requires scheme prefix
            manager.get('example.com') # Selenium requires scheme prefix
            manager.get('example.com') # Requires two commands to shut down
        except CommandExecutionError:
            pass
        assert os.path.isfile(os.path.join(browser_params[0]['profile_archive_dir'],'profile.tar.gz'))

    def test_profile_error(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        browser_params[0]['profile_tar'] = '/tmp/NOTREAL'
        with pytest.raises(ProfileLoadError):
            manager = TaskManager.TaskManager(manager_params, browser_params)

    def test_browser_profile_coverage(self, tmpdir):
        # Run the test crawl
        data_dir = os.path.join(str(tmpdir),'data_dir')
        manager_params, browser_params = self.get_config(data_dir)
        manager = TaskManager.TaskManager(manager_params, browser_params)
        for site in TEST_SITES:
            manager.get(site)
        fp = manager.browsers[0].current_profile_path
        ff_db_tar = os.path.join(browser_params[0]['profile_archive_dir'],'profile.tar.gz')
        manager.close(post_process=False)
        
        # Extract crawl profile
        with tarfile.open(ff_db_tar) as tar:
            tar.extractall(browser_params[0]['profile_archive_dir'])
        
        # Output databases
        ff_db = os.path.join(browser_params[0]['profile_archive_dir'],'places.sqlite')
        crawl_db = os.path.join(manager_params['data_directory'], manager_params['database_name'])
        
        # Grab urls from crawl database
        crawl_con = sqlite3.connect(crawl_db)
        ccur = crawl_con.cursor()

        req_ps = set()
        ccur.execute("SELECT url FROM http_requests")
        for url, in ccur.fetchall():
            req_ps.add(psl.get_public_suffix(urlparse(url).hostname))

        hist_ps = set()
        successes = dict()
        ccur.execute("SELECT arguments, bool_success FROM CrawlHistory WHERE command='GET'")
        for url, success in ccur.fetchall():
            ps = psl.get_public_suffix(urlparse(url).hostname)
            hist_ps.add(ps)
            successes[ps] = success

        # Grab urls from Firefox database
        profile_con = sqlite3.connect(ff_db)
        pcur = profile_con.cursor()
        profile_ps = set()
        pcur.execute("SELECT url FROM moz_places")
        for host, in pcur.fetchall():
            try:
                profile_ps.add(psl.get_public_suffix(urlparse(host).hostname))
            except AttributeError:
                pass
        profile_con.close()

        # We expect urls to be in the Firefox profile if:
        # 1. We've made requests to it
        # 2. The url is a top_url we entered into the address bar
        # 3. The url successfully loaded (see: Issue #40)
        # 4. The site does not respond to the initial request with a 204 (won't show in FF DB)
        missing_urls = req_ps.intersection(hist_ps).difference(profile_ps)
        unexpected_missing_urls = set()
        for url in missing_urls:
            if successes[url] == 0 or successes[url] == -1:
                continue
            ccur.execute("SELECT COUNT(*) FROM http_responses WHERE top_url = ?",('http://'+url,))
            if ccur.fetchone()[0] > 1:
                continue
            ccur.execute("SELECT response_status FROM http_responses WHERE top_url = ?",('http://'+url,))
            if ccur.fetchone()[0] == 204:
                continue
            unexpected_missing_url.add(url)

        crawl_con.close()
        assert len(unexpected_missing_urls) == 0

    #TODO Check for Flash
    #TODO Check contents of profile (tests should fail anyway if profile doesn't contain everything)
