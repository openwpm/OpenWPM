echo "Would you like to install Adobe Flash Player? (Only required for crawls with Flash) [y,N]"
read -s -n 1 response
if [[ $response = "" ]] || [ $response == 'n' ] || [ $response == 'N' ]; then
    flash=false
    echo Not installing Adobe Flash Plugin
elif [ $response == 'y' ] || [ $response == 'Y' ]; then
    flash=true
    echo Installing Adobe Flash Plugin
    sudo sh -c 'echo "deb http://archive.canonical.com/ubuntu/ trusty partner" >> /etc/apt/sources.list.d/canonical_partner.list'
else
    echo Unrecognized response, exiting
    exit 1
fi

sudo apt-get update

sudo apt-get install firefox htop git python-dev libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb libboost-python-dev libleveldb1 libleveldb-dev libjpeg-dev
if [ "$flash" = true ]; then
    sudo apt-get install adobe-flashplugin
fi

wget https://bootstrap.pypa.io/get-pip.py
sudo -H python get-pip.py
rm get-pip.py

sudo -H pip install -U setuptools
sudo -H pip install -U pyvirtualdisplay beautifulsoup4 pyasn1 PyOPenSSL python-dateutil tld pyamf psutil pyhash plyvel tblib tabulate pytest publicsuffix

# Install specific mitmproxy version since we rely on some internal structure of
# netlib and mitmproxy. New releases tend to break things and should be tested
sudo -H  pip install mitmproxy==0.13

# Install specific version of selenium known to work well with the Firefox install below
sudo -H pip install selenium==2.53.0

# Install specific version of Firefox known to work well with the selenium version above
wget https://ftp.mozilla.org/pub/firefox/releases/45.0.1/linux-x86_64/en-US/firefox-45.0.1.tar.bz2
tar jxf firefox*.tar.bz2
mv firefox firefox-bin
rm firefox*.tar.bz2
