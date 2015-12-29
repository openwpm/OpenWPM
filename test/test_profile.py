import pytest
import os

from ..automation import TaskManager
from ..automation.Errors import CommandExecutionError, ProfileLoadError

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

    #TODO Check for Flash
    #TODO Check contents of profile (tests should fail anyway if profile doesn't contain everything)
