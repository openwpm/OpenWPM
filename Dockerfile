FROM continuumio/miniconda:latest

ENTRYPOINT ["/bin/bash", "-c"]

WORKDIR /app

# Docker image OS dependencies for firefox to run
RUN apt-get install -y --quiet libxt6 libdbus-glib-1-2 libgtk-3-0

# Get conda up-to-date
RUN conda update -n base -c defaults conda

COPY ./automation ./automation
COPY ./build-extension.sh ./
COPY ./install-firefox-linux.sh ./
COPY ./environment.yaml ./
COPY ./VERSION ./

RUN conda env create -f environment.yaml
RUN ["/bin/bash", "-c", "source activate openwpm && npm config set unsafe-perm true && ./build-extension.sh"]

# Do this after expensive things as docker seems to want to re-do it each time
RUN ./install-firefox-linux.sh
ENV FIREFOX_BINARY /app/firefox-bin/firefox

COPY ./demo.py ./
CMD ["source activate openwpm && python demo.py"]
