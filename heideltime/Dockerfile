##
# Dockerfile that downloads Heideltime and a TreeTagger dependendency
#
#  - https://github.com/HeidelTime/heideltime
#  - https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger
#
# on a Ubuntu 18.04, and builds/configures them together.
#
# Before using this, be sure to review the TreeTagger and Heideltime Licenses,
# as they are not the most permissive ones.
#
#  - https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/Tagger-Licence
#  - https://github.com/HeidelTime/heideltime/blob/master/COPYING
##

FROM ubuntu:18.04

# install dependencies
RUN apt-get update && apt-get -y install \
    openjdk-8-jdk \
    git \
    maven \
    wget

# Download and install the tree tagger
# NOTE: Downloads english and german parameter files for the tree tagger, more language options at:
#       https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/#parfiles
WORKDIR /srv/app/treetagger
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz
RUN sh install-tagger.sh

# Clone heideltime itself and set up the location of the tagger in a new config file
WORKDIR /srv/app
RUN git clone https://github.com/HeidelTime/heideltime.git
RUN cp heideltime/conf/config.props .
RUN sed -i 's|^treeTaggerHome =.*$|treeTaggerHome = /srv/app/treetagger|g' config.props

# Build heideltime
# NOTE: This modifies the pom.xml to include dependencies in the standalone jar.
WORKDIR /srv/app/heideltime
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/
RUN sed -i 's|<scope>provided</scope>||g' pom.xml
RUN mvn clean package

# Expose the "java -jar ..." with our config as a simpler "heideltime" command
RUN echo '#!/bin/bash \n\
java -jar /srv/app/heideltime/target/de.unihd.dbs.heideltime.standalone.jar -c /srv/app/config.props "$@" \n\
' > /bin/heideltime && chmod a+x /bin/heideltime

# Do a test annotation
RUN echo "Did we install heideltime today?" > /tmp/test.txt
RUN heideltime -l english -t scientific -dct 1970-01-01 /tmp/test.txt

# keep the container running when started
CMD /bin/sleep infinity
