# Two stage Dockerfile to build OpenWPM
# Stage 1 builds the extension, stage 2 builds the main OpenWPM image

FROM node:10 as extension
WORKDIR /usr/src/app

# The extension needs to run for example the TypeScript transpiler
# to generate the JavaScript code of the extension. This must be done as root
# as long as the directory of the extension is only writeable as root.
RUN npm config set unsafe-perm true

COPY automation/Extension/firefox/. ./
COPY automation/Extension/webext-instrumentation/. ../webext-instrumentation
RUN npm install
RUN npm run build
RUN cp dist/openwpm-1.0.zip openwpm.xpi

# Stage 2, build the main OpenWPM image
FROM ubuntu:18.04

WORKDIR /opt/OpenWPM
# This is just a performance optimization and can be skipped by non-US
# based users
RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list

RUN apt-get clean -y && rm -r /var/lib/apt/lists/* -vf && apt-get clean -y && apt-get update -y && apt-get upgrade -y && apt-get install sudo -y

# Install the Ubuntu packages as well as firefox and the geckodriver first
COPY ./install-system.sh .
RUN ./install-system.sh --no-flash

# Move the firefox binary away from the /opt/OpenWPM root so that it is available if
# we mount a local source code directory as /opt/OpenWPM
RUN mv firefox-bin /opt/firefox-bin
ENV FIREFOX_BINARY /opt/firefox-bin/firefox-bin

# For some reasons, python3-publicsuffix doesn't work with pip3 at the moment,
# so install it from the ubuntu repository
RUN apt-get -y install python3-publicsuffix

COPY requirements.txt .
COPY install-pip-and-packages.sh .
RUN ./install-pip-and-packages.sh

COPY --from=extension /usr/src/app/dist/openwpm-*.zip automation/Extension/firefox/openwpm.xpi

# Node is not required, the extension is build in the first build stage so
# there is no need to run install-node.sh and build-extension.sh

# Technically, the automation/Extension/firefox directory could be skipped
# here, but there is no nice way to do that with the Docker COPY command
COPY . .

# Optionally create an OpenWPM user. This is not strictly required since it is
# possible to run everything as root as well.
RUN adduser --disabled-password --gecos "OpenWPM"  openwpm

# Setting demo.py as the default command
CMD python3 demo.py
