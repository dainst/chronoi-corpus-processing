
FROM python:3

# install python dependencies
RUN pip3 install nltk

# install general dependencies
RUN apt-get update
RUN apt-get -y install \
    ghostscript

# create the log file if it doesn't exist, use ENV as it is available in CMD
ARG log_file=/var/log/preprocessing.log
RUN touch ${log_file}
ENV LOG=${log_file}

# prepare directories to be mounted externally
RUN mkdir -p /srv/input /srv/output
VOLUME /srv/input /srv/output

# setup the files
WORKDIR /srv/preprocessing
ADD . /srv/preprocessing

# follow the log file
CMD /usr/bin/tail -n0 -f "${LOG}"
