import subprocess
import os

def get_version():
    """Return OpenWPM version tag/current commit and Firefox version """
    openwpm = subprocess.check_output(["git","describe","--tags"]).strip()

    ff_ini = os.path.join(os.path.dirname(__file__), '../firefox-bin/application.ini')
    with open(ff_ini, 'r') as f:
        ff = None
        for line in f:
            if line.startswith('Version='):
                ff = line[8:].strip()
                break
    return openwpm, ff
