class Command:
    def set_visit_crawl_id(self, visit_id, crawl_id):
        self.visit_id = visit_id
        self.crawl_id = crawl_id

    def set_start_time(self, start_time):
        self.start_time = start_time


class Get_Command(Command):
    def __init__(self, url, sleep):
        self.url = url
        self.sleep = sleep

    def __repr__(self):
        return "Get_Command({},{})".format(self.url, self.sleep)


class Browse_Command(Command):
    def __init__(self, url, num_links, sleep):
        self.url = url
        self.num_links = num_links
        self.sleep = sleep

    def __repr__(self):
        return "Browse_Command({},{},{})".format(
            self.url, self.num_links, self.sleep)


class Dump_Flash_Cookies_Command(Command):
    def __init__(self):
        pass

    def __repr__(self):
        return "Dump_Flash_Cookies_Command()"


class Dump_Prof_Command(Command):
    def __init__(self, dump_folder, close_webdriver, compress):
        self.dump_folder = dump_folder
        self.close_webdriver = close_webdriver
        self.compress = compress

    def __repr__(self):
        return "Dump_Prof_Command({},{},{})".format(
            self.dump_folder, self.close_webdriver, self.compress)


class Dump_Page_Source_Command(Command):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "Dump_Page_Source_Command({})".format(self.suffix)


class Recursive_Dump_Page_Source_Command(Command):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "Recursive_Dump_Page_Source_Command({})".format(self.suffix)


class Save_Screenshot_Command(Command):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return "Save_Screenshot_Command({})".format(self.suffix)


class Screenshot_Full_Page_Command(Command):
    def __init__(self, suffix):
        self.suffix = suffix

    def __repr__(self):
        return " Screenshot_Full_Page_Command({})".format(self.suffix)


class Run_Custom_Function_Command(Command):
    def __init__(self, function_handle, func_args):
        self.function_handle = function_handle
        self.func_args = func_args

    def __repr__(self):
        return "Run_Custom_Function_Command({},{})".format(
            self.function_handle, self.func_args)


class Shutdown_Command(Command):
    def __init__(self):
        pass

    def __repr__(self):
        return "Shutdown_Command()"
