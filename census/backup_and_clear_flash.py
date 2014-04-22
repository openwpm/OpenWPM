#simple script to copy and clear flash cookies on a unix system
import shutil
import sys
import os

home = os.path.expanduser('~')
locations = [home + '/.macromedia/Flash_Player/#SharedObjects',
             home + '/.macromedia/Flash_Player/macromedia.com/support/flashplayer/sys']

if len(sys.argv) < 2:
    print "ERROR: you must provide a destination directory"
    sys.exit(1)

if sys.argv[1] == '--skip':
    print "SKIP copying flash files - they will still be deleted?"
    raw_input("Press Enter to continue, Control-C to exit")

dst = sys.argv[1]

if dst != '--skip':
    if not os.path.isdir(dst):
        os.makedirs(dst)

    for location in locations:
        print "COPYING: " + location
        (head, tail) = os.path.split(location)
        shutil.copytree(location, dst+tail)

for location in locations:
    print "CLEARING: " + location
    for root, dirs, files in os.walk(location):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
