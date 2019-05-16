FROM ubuntu:18.04

COPY . /app

WORKDIR /app
RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list
RUN apt-get clean -y && rm -r /var/lib/apt/lists/* -vf && apt-get clean -y && apt-get update -y && apt-get upgrade -y && apt-get install sudo -y

# The build-extension.sh script does not work as root. We create another user and allow it to run sudo without a password. Then we run the install.sh script as openwpm, which calls build-extension.sh.
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers; adduser --disabled-password --gecos "OpenWPM"  openwpm; adduser  openwpm sudo
RUN chown -R openwpm.openwpm .; su openwpm -c "./install.sh --no-flash"; chown -R root.root .
CMD python demo.py
