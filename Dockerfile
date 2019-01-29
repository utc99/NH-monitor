FROM ubuntu:16.04

MAINTAINER Your Name "youremail@domain.tld"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev default-jre apache2 php-pear php-fpm php-dev php-zip php-curl php-xmlrpc php-gd php-mysql php-mbstring php-xml libapache2-mod-php wget nodejs clang gcc unzip

# We copy just the requirements.txt first to leverage Docker cache
#COPY ./requirements.txt /app/requirements.txt
COPY ./app-requirements.txt /app/app-requirements.txt

WORKDIR /app

#RUN pip3 install -r requirements.txt
RUN pip3 install -r app-requirements.txt

COPY . /app

ENV FLASK_APP=application.py
ENV FLASK_DEBUG=1
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN service apache2 restart

ENTRYPOINT [ "flask", "run", "--host=0.0.0.0" ]

#CMD [ "flask run" ]
