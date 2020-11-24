##
# Dockerfile that downloads Heideltime and a TreeTagger dependendency
#
#  - https://github.com/HeidelTime/heideltime
#  - https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger
#
# on Ubuntu 18.04, builds/configures them together and enables support
# for temponyms extracted from a chronontology dump.
##

FROM maven:3-jdk-8

# install dependencies
RUN apt-get update \
  && apt-get -y install \
    wget \
    locales \
    # Needed for pip install below, pkg-config lets pip find the icu version
    pkg-config \
    libicu-dev \
    # python deps are needed for ./scripts
    python3 \
    python3-pip \
  && pip3 install PyICU

# setup proper locale handling (important for heideltime to pos-tagger interaction)
RUN sed -i 's/# \(en_US\.UTF-8 .*\)/\1/' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Download and install the tree tagger
# NOTE: Downloads parameter files for the tree tagger for only some langauges, more language options at:
#       https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/#parfiles
WORKDIR /srv/app/treetagger
RUN  wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz \
  && wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz \
  && wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh \
  && wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz \
  && wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz \
  && wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/french.par.gz \
  && wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/italian.par.gz \
  && wget --quiet https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish.par.gz \
  # We need to extract this ourselves as the version in the install-tagger.sh might differ
  && tar -zxf tree-tagger-linux-3.2.2.tar.gz \
  && sh install-tagger.sh \
  && chmod 755 cmd lib \
  && chmod 644 lib/*

# Install heideltime dependencies
WORKDIR /srv/app/heideltime
ADD heideltime/pom.xml .
RUN mvn verify clean --fail-never

# Build heideltime itself
ADD . /srv/app/
RUN sed -i 's|<scope>provided</scope>||g' pom.xml \
  && mvn package \
  # Setup the config to work with the tree tagger and consider temponyms
  && cp conf/config.props /srv/app \
  && sed -i 's|^treeTaggerHome =.*$|treeTaggerHome = /srv/app/treetagger|g' ../config.props \
  && sed -i 's|^considerTemponym =.*$|considerTemponym = true|g' ../config.props \
  # Expose the "java -jar ..." with our config as a simpler "heideltime" command
  && echo '#!/bin/bash\njava -jar /srv/app/heideltime/target/de.unihd.dbs.heideltime.standalone.jar -c /srv/app/config.props "$@" \n' \
  > /bin/heideltime \
  && chmod a+x /bin/heideltime

# just keep the container running when started
CMD /bin/sleep infinity
