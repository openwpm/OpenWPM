#============================================
# Dockerfile for OpenWPM
# See README.md for build & use instructions
#============================================

FROM ubuntu:16.04

#===============================
# Packages for minimal run-time
#===============================
RUN apt-get -qqy update
RUN apt-get -qqy install bzip2 unzip sudo nano x11-apps ca-certificates python wget curl

RUN apt-get -qqy install fping openvpn dialog iputils-ping net-tools socat

RUN apt-get -qqy install firefox htop git python-dev  libxml2-dev libxslt-dev libffi-dev libssl-dev build-essential xvfb libboost-python-dev libleveldb-dev libjpeg-dev libleveldb1v5


#===================================================
# Add normal user with passwordless sudo, and switch
#===================================================
RUN useradd user \
         --shell /bin/bash  \
         --create-home \
  && usermod -a -G sudo user \
  && echo 'ALL ALL = (ALL) NOPASSWD: ALL' >> /etc/sudoers \
  && echo 'user:secret' | chpasswd

USER user

#===================
# Install OpenWPM
#===================
RUN cd /opt/ && \
    sudo git clone https://github.com/citp/OpenWPM.git && \
    sudo chown -R user:user /opt/OpenWPM/

RUN cd /opt/OpenWPM/ && \
    wget --no-verbose https://bootstrap.pypa.io/get-pip.py \
    && sudo -H python get-pip.py \
    && rm get-pip.py \
    && sudo pip install -U -r requirements.txt

RUN cd /opt/OpenWPM/ && \
    wget --no-verbose https://ftp.mozilla.org/pub/firefox/releases/45.9.0esr/linux-x86_64/en-US/firefox-45.9.0esr.tar.bz2 \
    && tar jxf firefox*.tar.bz2 \
    && rm -rf firefox-bin \
    && mv firefox firefox-bin \
    && rm firefox*.tar.bz2
