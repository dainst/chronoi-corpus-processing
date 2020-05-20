##
# Dockerfile that downloads Heideltime and a TreeTagger dependendency
#
#  - https://github.com/HeidelTime/heideltime
#  - https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger
#
# on Ubuntu 18.04, builds/configures them together and enables support
# for temponyms extracted from a chronontology dump.
##

FROM ubuntu:18.04

# install dependencies
RUN apt-get update && apt-get -y install \
    openjdk-8-jdk \
    git \
    maven \
    wget \
    libicu-dev \
    locales \
    python3 \
    python3-pip

RUN pip3 install PyICU

# setup proper locale handling (important for heideltime to pos-tagger interaction)
RUN sed -i 's/# \(en_US\.UTF-8 .*\)/\1/' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Download and install the tree tagger
# NOTE: Downloads parameter files for the tree tagger for only some langauges, more language options at:
#       https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/#parfiles
WORKDIR /srv/app/treetagger
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/french.par.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/italian.par.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish.par.gz
RUN sh install-tagger.sh
RUN chmod 755 /srv/app/treetagger/cmd
RUN chmod 755 /srv/app/treetagger/lib
RUN chmod 644 /srv/app/treetagger/lib/*

# Install heideltime dependencies
# NOTE: This modifies the pom.xml to include dependencies in the standalone jar.
WORKDIR /srv/app/heideltime
ADD heideltime/pom.xml .
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/
RUN sed -i 's|<scope>provided</scope>||g' pom.xml
RUN mvn verify clean --fail-never

# Setup the heideltime config to work with the tree tagger
WORKDIR /srv/app
ADD heideltime/conf/config.props .
RUN sed -i 's|^treeTaggerHome =.*$|treeTaggerHome = /srv/app/treetagger|g' config.props

# Prepare temponym files tagging and enable temponym tagging in the config
# This needs the heideltime resource directory structure in place
ADD ./heideltime/resources /srv/app/heideltime/resources
ADD ./scripts /srv/app/scripts
WORKDIR /srv/app/scripts
RUN python3 chronontology_temponyms_export.py -i resources/chronontology.json -o /tmp/temponyms
RUN ./prepare_heideltime_temponym_files.sh /tmp/temponyms
RUN sed -i 's|^considerTemponym =.*$|considerTemponym = true|g' /srv/app/config.props

# Build heideltime itself
ADD ./heideltime /srv/app/heideltime
WORKDIR /srv/app/heideltime
RUN mvn package

# Expose the "java -jar ..." with our config as a simpler "heideltime" command
RUN echo '#!/bin/bash \n\
java -jar /srv/app/heideltime/target/de.unihd.dbs.heideltime.standalone.jar -c /srv/app/config.props "$@" \n\
' > /bin/heideltime && chmod a+x /bin/heideltime

# keep the container running when started
CMD /bin/sleep infinity
