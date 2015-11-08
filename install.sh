sudo apt-get update

sudo apt-get install firefox htop git python-dev libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb libboost-python-dev libleveldb1 libleveldb-dev libjpeg-dev

wget https://bootstrap.pypa.io/get-pip.py
sudo -H python get-pip.py
rm get-pip.py

sudo -H pip install -U setuptools
sudo -H pip install -U pyvirtualdisplay beautifulsoup4 netlib pyasn1 PyOPenSSL python-dateutil tld pyamf psutil mitmproxy pyhash plyvel tblib

# Install specific version of Firefox and selenium
# known to work well together.
sudo pip install selenium==2.47.1
wget https://ftp.mozilla.org/pub/mozilla.org/firefox/releases/39.0.3/linux-x86_64/en-US/firefox-39.0.3.tar.bz2
tar jxf firefox*.tar.bz2 -C ./
rm firefox*.tar.bz2
