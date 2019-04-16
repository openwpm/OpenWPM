FROM ubuntu:18.04

COPY . /app

WORKDIR /app
RUN sed -i'' 's/archive\.ubuntu\.com/us\.archive\.ubuntu\.com/' /etc/apt/sources.list
RUN apt-get clean -y && rm -r /var/lib/apt/lists/* -vf && apt-get clean -y && apt-get update -y && apt-get upgrade -y && apt-get install sudo -y
RUN ./install.sh --no-flash
CMD python demo.py
