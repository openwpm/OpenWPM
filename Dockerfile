FROM ubuntu:22.04

SHELL ["/bin/bash", "-c"]

# Update ubuntu and setup conda
# adapted from: https://hub.docker.com/r/conda/miniconda3/dockerfile
RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list
RUN apt-get clean -qq \
    && rm -r /var/lib/apt/lists/* -vf \
    && apt-get clean -qq \
    && apt-get update -qq \
    && apt-get upgrade -qq \
    # git and make for `npm install`, wget for `install-conda`
    && apt-get install wget git make -qq \
    # deps to run firefox inc. with xvfb
    && apt-get install firefox xvfb libgtk-3-dev libasound2 libdbus-glib-1-2 libpci3 -qq

ENV HOME /opt
COPY scripts/install-conda.sh .
RUN ./install-conda.sh
ENV PATH $HOME/conda/bin:$PATH

# Install OpenWPM
WORKDIR /opt/OpenWPM
COPY . .
RUN ./install.sh
ENV PATH $HOME/conda/envs/openwpm/bin:$PATH

# Move the firefox binary away from the /opt/OpenWPM root so that it is available if
# we mount a local source code directory as /opt/OpenWPM
RUN mv firefox-bin /opt/firefox-bin
ENV FIREFOX_BINARY /opt/firefox-bin/firefox-bin

# Setting demo.py as the default command
CMD [ "python", "demo.py"]
