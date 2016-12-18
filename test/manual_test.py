from utilities import BASE_TEST_URL, start_server
from os.path import dirname, join, realpath
import subprocess

OPENWPM_LOG_PREFIX = "console.log: openwpm: "
INSERT_PREFIX = "Array"


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_command_output(command, cwd=None):
    popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, cwd=cwd)
    return iter(popen.stdout.readline, b"")


def colorize(line):
    if INSERT_PREFIX in line:  # print long DB insert lines in blue
        line = line.replace(INSERT_PREFIX, bcolors.OKBLUE + INSERT_PREFIX)
    if OPENWPM_LOG_PREFIX in line:
        line = line.replace(OPENWPM_LOG_PREFIX,
                            OPENWPM_LOG_PREFIX + bcolors.OKGREEN)
    return line


def start_manual_test():
    base_dir = dirname(dirname(realpath(__file__)))
    ext_path = join(base_dir, 'automation', 'Extension', 'firefox')
    ff_bin_path = join(base_dir, 'firefox-bin', 'firefox')
    cmd_jpm_run = "jpm run --binary-args 'url %s' -b %s" % (BASE_TEST_URL,
                                                            ff_bin_path)
    server, thread = start_server()
    try:
        # http://stackoverflow.com/a/4417735/3104416
        for line in get_command_output(cmd_jpm_run, cwd=ext_path):
            print colorize(line), bcolors.ENDC,
    except KeyboardInterrupt:
        print "Keyboard Interrupt detected, shutting down..."
    print "\nClosing server thread..."
    server.shutdown()
    thread.join()


if __name__ == '__main__':
    start_manual_test()
