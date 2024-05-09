FROM ubuntu:18.04
LABEL org.opencontainers.image.authors="https://github.com/roechi"

RUN apt-get update -y && \
  apt-get install -y python3-scipy && \
  apt-get install -y python3-matplotlib && \
  apt-get install -y python3-pil && \
  apt-get install -y python3-django python3-bs4 && \
  apt-get install -y python3-reportlab imagemagick gifsicle && \
  apt-get install -y python3-psutil && \
  apt-get install -y python3-pip && \
  pip3 install pyeq3

EXPOSE 8000

ADD ./source /source
WORKDIR /source

ENTRYPOINT python3 manage.py runserver 0.0.0.0:8000
