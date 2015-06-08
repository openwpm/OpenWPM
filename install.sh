sudo apt-get update

sudo apt-get install firefox htop git python-dev python-pip libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb

sudo pip install -U pyvirtualdisplay beautifulsoup4 netlib pyasn1 PyOPenSSL python-dateutil tld pyamf psutil

# Pin a specific version of mitmproxy
# current version has compatibility issues with 
# the most recent cffi release
sudo pip install mitmproxy==0.11.2
sudo pip install cffi=1.0.3

# Install specific version of Firefox and selenium
# known to work well together.
sudo pip install selenium==2.46.0
wget https://ftp.mozilla.org/pub/mozilla.org/firefox/releases/38.0.5/linux-x86_64/en-US/firefox-38.0.5.tar.bz2
tar jxf firefox*.tar.bz2 -C ./
rm firefox*.tar.bz2
