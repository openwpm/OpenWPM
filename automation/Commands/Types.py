class BaseCommand:
    def set_visit_crawl_id(self, visit_id, crawl_id):
        self.visit_id = visit_id
        self.crawl_id = crawl_id

    def set_start_time(self, start_time):
        self.start_time = start_time


class GetCommand(BaseCommand):
    def __init__(self, url, sleep):
        self.url = url
        self.sleep = sleep

    def __repr__(self):
        return "Get_Command({},{})".format(self.url, self.sleep)


class BrowseCommand(BaseCommand):
    def __init__(self, url, num_links, sleep):
        self.url = url
        self.num_links = num_links
        self.sleep = sleep

    def __repr__(self):
        return "Browse_Command({},{},{})".format(
            self.url, self.num_links, self.sleep)


class DumpFlashCookiesCommand(BaseCommand):
    def __init__(self):
        pass

    def __repr__(self):
        return "Dump_Flash_Cookies_Command()"


class DumpProfCommand(BaseCommand):
    def __init__(self, dump_folder, close_webdriver, compress):
        self.dump_folder = dump_folder
        self.close_webdriver = close_webdriver
        self.compress = compress

    def __repr__(self):
        return "Dump_Prof_Command({},{},{})".format(
            self.dump_folder, self.close_webdriver, self.compress)


class DumpPageSourceCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "Dump_Page_Source_Command({})".format(self.suffix)


class RecursiveDumpPageSourceCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "Recursive_Dump_Page_Source_Command({})".format(self.suffix)


class SaveScreenshotCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "Save_Screenshot_Command({})".format(self.suffix)


class ScreenshotFullPageCommand(BaseCommand):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return " Screenshot_Full_Page_Command({})".format(self.suffix)


class RunCustomFunctionCommand(BaseCommand):
    def __init__(self, function_handle, func_args):
        self.function_handle = function_handle
        self.func_args = func_args

    def __repr__(self):
        return "Run_Custom_Function_Command({},{})".format(
            self.function_handle, self.func_args)


class ShutdownCommand(BaseCommand):
    def __init__(self):
        pass

    def __repr__(self):
        return "Shutdown_Command()"
