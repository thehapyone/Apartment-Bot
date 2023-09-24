FROM public.ecr.aws/lambda/python:3.9 as base

COPY install-browsers.sh /tmp/

# Install dependencies
RUN yum install xz atk cups-libs gtk3 libXcomposite alsa-lib tar \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel unzip bzip2 -y -q

# Install Browsers
RUN /usr/bin/bash /tmp/install-browsers.sh && yum remove xz tar unzip bzip2 -y

FROM base

ARG GOOGLE_API_KEY
ARG SITE_USERNAME
ARG SITE_PASSWORD
ARG MAX_RENT="15000"
ARG MAX_DISTANCE=18
ARG DISPLAY_PORT="25"
ARG LONG_RENT_ONLY="True"

ENV GOOGLE_API_KEY=$GOOGLE_API_KEY
ENV SITE_USERNAME=$SITE_USERNAME
ENV SITE_PASSWORD=$SITE_PASSWORD
ENV MAX_RENT=$MAX_RENT
ENV MAX_DISTANCE=$MAX_DISTANCE
ENV DISPLAY_PORT=$DISPLAY_PORT
ENV LONG_RENT_ONLY=$LONG_RENT_ONLY

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY main-container.py app.py

#ENTRYPOINT ["/usr/bin/bash", "ls", "-al"]
#CMD ["whoami"]
ENTRYPOINT ["python3", "app.py"]