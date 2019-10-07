
FROM python:2

# install java as a dependency
RUN apt-get update && \
    apt-get -y install openjdk-11-jre

# chekcout the tempeval3 toolkit in our modified version
ENV TEMPEVAL3_DIR=/srv/tempeval3_toolkit
RUN git clone https://github.com/dainst/tempeval3_toolkit.git ${TEMPEVAL3_DIR}
WORKDIR ${TEMPEVAL3_DIR}
RUN git checkout update-timeml-normalizer

# after it is started, just keep the container running
CMD /bin/sleep infinity

