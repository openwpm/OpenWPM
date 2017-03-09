import pytest
from os.path import join, isfile
from ..automation import TaskManager
from ..automation.Errors import CommandExecutionError, ProfileLoadError
from openwpmtest import OpenWPMTest


# TODO update these tests to make use of blocking commands
class TestProfile(OpenWPMTest):

    def get_config(self, data_dir=""):
        manager_params, browser_params = self.get_test_config(data_dir)
        browser_params[0]['profile_archive_dir'] =\
            join(manager_params['data_directory'], 'browser_profile')
        return manager_params, browser_params

    def test_saving(self):
        manager_params, browser_params = self.get_config()
        manager = TaskManager.TaskManager(manager_params, browser_params)
        manager.get('http://example.com')
        manager.close()
        assert isfile(join(browser_params[0]['profile_archive_dir'],'profile.tar.gz'))

    def test_crash(self):
        manager_params, browser_params = self.get_config()
        manager_params['failure_limit'] = 0
        manager = TaskManager.TaskManager(manager_params, browser_params)
        with pytest.raises(CommandExecutionError):
            manager.get('http://example.com') # So we have a profile
            manager.get('example.com') # Selenium requires scheme prefix
            manager.get('example.com') # Requires two commands to shut down

    def test_crash_profile(self):
        manager_params, browser_params = self.get_config()
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
        assert isfile(join(browser_params[0]['profile_archive_dir'],'profile.tar.gz'))

    def test_profile_error(self):
        manager_params, browser_params = self.get_config()
        browser_params[0]['profile_tar'] = '/tmp/NOTREAL'
        with pytest.raises(ProfileLoadError):
            TaskManager.TaskManager(manager_params, browser_params)  # noqa

    # TODO the old test for the profile being saved on a startup crash
    # relied on yanking mitmproxy out from under the browser, which is
    # no longer possible - think of a new one

    #TODO Check for Flash
    #TODO Check contents of profile (tests should fail anyway if profile doesn't contain everything)
