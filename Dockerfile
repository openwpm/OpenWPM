#=============================================================
# Dockerfile for OpenWPM
# See README.md for build & use instructions
#=============================================================

FROM ubuntu:18.04

#=============================================================
# Packages required for container setup
#=============================================================

RUN apt-get -qqy update
RUN apt-get -qqy install sudo

#=============================================================
# Copy OpenWPM source
#=============================================================
RUN sudo mkdir /opt/OpenWPM/

ADD automation /opt/OpenWPM/automation/
ADD requirements.txt /opt/OpenWPM/
ADD VERSION /opt/OpenWPM/
ADD install.sh /opt/OpenWPM/
ADD demo.py /opt/OpenWPM/

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
ENV PATH="/home/user/.local/bin:${PATH}"

#=============================================================
# Install requirements for OpenWPM
#=============================================================
RUN sudo chown -R user:user /opt/OpenWPM/

RUN cd /opt/OpenWPM/ \
     && ./install.sh --no-flash
