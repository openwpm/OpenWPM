FROM continuumio/miniconda:latest

ENTRYPOINT ["/bin/bash", "-c"]

WORKDIR /app

# Setup environment
RUN apt-get install -y --quiet libxt6 libdbus-glib-1-2 libgtk-3-0
RUN conda update -n base -c defaults conda

# Copy files
COPY ./automation ./automation
COPY ./build-extension.sh ./
COPY ./install-firefox-linux.sh ./
COPY ./environment.yaml ./
COPY ./VERSION ./

# Install everything
RUN conda env create -f environment.yaml
RUN ["/bin/bash", "-c", "source activate openwpm && npm config set unsafe-perm true && ./build-extension.sh"]
RUN ./install-firefox-linux.sh

# Run crawls
ENV FIREFOX_BINARY /app/firefox-bin/firefox
COPY ./demo.py ./
CMD ["source activate openwpm && python demo.py"]
