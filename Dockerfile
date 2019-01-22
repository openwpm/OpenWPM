FROM ubuntu:18.04

COPY . /app


WORKDIR /app
RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list
RUN apt-get -y update --fix-missing && apt-get install sudo
RUN ./install.sh --flash
CMD python demo.py
