FROM krallin/ubuntu-tini:bionic

SHELL ["/bin/bash", "-c"]

# Update ubuntu and setup conda
# adapted from: https://hub.docker.com/r/conda/miniconda3/dockerfile
RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list
RUN apt-get clean -y \
    && rm -r /var/lib/apt/lists/* -vf \
    && apt-get clean -qq \
    && apt-get update -qq \
    && apt-get upgrade -qq \
    && apt-get install wget make -qq

WORKDIR /opt/OpenWPM
ENV HOME /opt

COPY install-miniconda.sh .
RUN ./install-miniconda.sh
ENV PATH $HOME/miniconda/bin:$PATH

# Install OpenWPM
COPY . .
RUN ./install.sh

# Move the firefox binary away from the /opt/OpenWPM root so that it is available if
# we mount a local source code directory as /opt/OpenWPM
RUN mv firefox-bin /opt/firefox-bin
ENV FIREFOX_BINARY /opt/firefox-bin/firefox-bin

# Setting demo.py as the default command
CMD [ "python", "demo.py"]
