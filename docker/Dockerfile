#=============================================================
# Dockerfile for OpenWPM
# See docker/README.md for build & use instructions
#=============================================================

FROM ubuntu:16.04

#=============================================================
# Packages for minimal run-time
#=============================================================
RUN apt-get -qqy update
RUN apt-get -qqy install bzip2 unzip sudo nano x11-apps ca-certificates python wget curl
RUN apt-get -qqy install fping openvpn dialog iputils-ping net-tools socat
RUN apt-get -qqy install firefox htop git python-dev  libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb libboost-python-dev libleveldb-dev libjpeg-dev libleveldb1v5

#=============================================================
# Copy OpenWPM source
#=============================================================
RUN sudo mkdir /opt/OpenWPM/ && sudo mkdir /opt/OpenWPM/automation/

ADD automation /opt/OpenWPM/automation/
ADD requirements.txt /opt/OpenWPM/
ADD __init__.py /opt/OpenWPM/
ADD LICENSE /opt/OpenWPM/
ADD VERSION /opt/OpenWPM/
# (add more source directories/files as needed)

#=============================================================
# Add normal user with passwordless sudo, and switch
#=============================================================
RUN useradd user \
         --shell /bin/bash  \
         --create-home \
  && usermod -a -G sudo user \
  && echo 'ALL ALL = (ALL) NOPASSWD: ALL' >> /etc/sudoers \
  && echo 'user:secret' | chpasswd

USER user

#=============================================================
# Install OpenWPM
#=============================================================
RUN sudo chown -R user:user /opt/OpenWPM/

RUN cd /opt/OpenWPM/ \
    && wget --no-verbose https://bootstrap.pypa.io/get-pip.py \
    && sudo -H python get-pip.py \
    && rm get-pip.py

RUN cd /opt/OpenWPM/ \
    && sudo pip install -U -r requirements.txt

#=============================================================
# Install Firefox & Selenium's Gecko driver
#=============================================================

RUN cd /opt/OpenWPM/ \
    && wget --no-verbose https://ftp.mozilla.org/pub/firefox/releases/52.4.0esr/linux-x86_64/en-US/firefox-52.4.0esr.tar.bz2 \
    && tar jxf firefox*.tar.bz2 \
    && rm -rf firefox-bin \
    && mv firefox firefox-bin \
    && rm firefox*.tar.bz2

RUN cd /opt/OpenWPM/ \
    && wget --no-verbose https://github.com/mozilla/geckodriver/releases/download/v0.15.0/geckodriver-v0.15.0-linux64.tar.gz \
    && tar zxf geckodriver-*.tar.gz \
    && rm geckodriver-*.tar.gz \
    && mv geckodriver firefox-bin
