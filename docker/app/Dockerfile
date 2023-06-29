FROM debian:12.0


## User environment
#
ENV DEV_USER=devusr
ENV DEV_GROUP=devgrp
ENV DEV_UID=1110
ENV DEV_GID=1110
ENV DEV_USER_HOME=/home/$DEV_USER
ENV PYTHON_VER_MAJ=3.10
ENV PYTHON_VER_MIN=${PYTHON_VER_MAJ}.12


## Install base system
#
# install basic packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        rsyslog \
        git \
        unzip \
        wget \
        curl \
        netcat-traditional \
        procps \
        socat \
        net-tools \
        vim \
        build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev llvm \
        libncurses5-dev libncursesw5-dev xz-utils tk-dev \
        libffi-dev \
        liblzma-dev \
        libpq-dev

# install Python
WORKDIR /tmp
RUN wget --no-verbose \
    https://www.python.org/ftp/python/${PYTHON_VER_MIN}/Python-${PYTHON_VER_MIN}.tgz
RUN tar xf Python-${PYTHON_VER_MIN}.tgz
WORKDIR Python-${PYTHON_VER_MIN}
RUN ./configure --enable-optimizations && \
	make -j8 && \
	make altinstall
WORKDIR /usr/local/bin

# cleanup
RUN apt-get -y autoremove && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* && \
    rm -rf /var/tmp/*


## Setup and install user account
#
# create development user/group
RUN addgroup --gid $DEV_GID $DEV_GROUP && \
    adduser --gecos 'Development User' --disabled-password \
      --uid $DEV_UID --gid $DEV_GID $DEV_USER

USER $DEV_USER
WORKDIR $DEV_USER_HOME

# install Python virtual environment
RUN mkdir -p $DEV_USER_HOME/opt/lib
RUN /usr/local/bin/python${PYTHON_VER_MAJ} -m venv --copies $DEV_USER_HOME/opt/lib/python
RUN $DEV_USER_HOME/opt/lib/python/bin/pip3 install --upgrade pip
RUN echo "export PATH=${PATH}:${HOME}/opt/lib/python/bin" >> ~/.profile

# install application Python package
RUN $DEV_USER_HOME/opt/lib/python/bin/pip3 install \
    --use-deprecated=legacy-resolver zensols.mimicsid
RUN $DEV_USER_HOME/opt/lib/python/bin/pip3 check || /usr/bin/true

# force load models and test mednlp models and functionality
RUN $DEV_USER_HOME/opt/lib/python/bin/mednlp \
    show 'John died of liver cancer.'

# force load models and test mimicsid models and functionality
RUN mkdir -p trash
# TODO: revert and test (stanford server is currently down)
RUN mkdir -p $DEV_USER_HOME/.cache/zensols/deepnlp
COPY src/image/glove.6B.zip $DEV_USER_HOME/.cache/zensols/deepnlp
RUN $DEV_USER_HOME/opt/lib/python/bin/mimicsid \
    predict /etc/motd --path trash
RUN $DEV_USER_HOME/opt/lib/python/bin/mimicsid \
    ontology --output trash/trash.txt
RUN $DEV_USER_HOME/opt/lib/python/bin/python -c \
    "from zensols.mednlp import ApplicationFactory ; \
print(ApplicationFactory.create_harness()['cui2vec_500_embedding'].keyed_vectors)"

# cleanup
RUN rm -r trash
RUN rm -r .cache/pip

# cached data directory mapped by the container
RUN mkdir -p data

# tell programs where to find the DB parameters for container logins
RUN echo "export MIMICRC=/mnt/db.conf" >> ~/.profile
RUN echo "export MIMICSIDRC=/mnt/db.conf" >> ~/.profile


## Container config
#
USER root

# default to root home dir on login
WORKDIR /root

# ports and volumes
EXPOSE 22

COPY target/inst/entrypoint.sh /usr/local/bin/entrypoint-zens-dev.sh
ENTRYPOINT ["/usr/local/bin/entrypoint-zens-dev.sh"]
