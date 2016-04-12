from utilities import BASE_TEST_URL, start_server
import subprocess


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def run_cmd(command):
    popen = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    return iter(popen.stdout.readline, b"")


def start_manual_test():
    cmd_cd = "cd ../automation/Extension/firefox/"
    cmd_jpm = "jpm run --binary-args '%s' -b `which firefox`" % BASE_TEST_URL
    server, thread = start_server()
    try:
        # http://stackoverflow.com/a/4417735/3104416
        for line in run_cmd("%s && %s" % (cmd_cd, cmd_jpm)):
            print bcolors.OKGREEN, line, bcolors.ENDC,
    except KeyboardInterrupt:
        print "Keyboard Interrupt detected, shutting down..."
    print "\nClosing server thread..."
    server.shutdown()
    thread.join()


if __name__ == '__main__':
    start_manual_test()
