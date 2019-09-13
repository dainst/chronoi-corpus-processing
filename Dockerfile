
FROM python:3

# install general dependencies
RUN apt-get update
RUN apt-get -y install \
    ghostscript \
    python3-dev \
    libhunspell-dev

# install python dependencies
RUN pip3 install nltk \
    langid \
    chardet \
    pdfminer.six \
    hunspell \
    PyICU \
    mkTranslation \
    python-Levenshtein \
    furl \
    SPARQLWrapper

# download tokenization data for nltk
RUN python3 -c "import nltk; nltk.download('punkt')"

# copy hunspell dictionaries in place
COPY resources/de_DE.aff resources/de_DE.dic /usr/share/hunspell/

# create the log file if it doesn't exist, use ENV as it is available in CMD
ARG log_file=/var/log/chronoi-pilot.log
RUN touch ${log_file}
ENV LOG=${log_file}

# prepare directories to be mounted externally
ENV INPUT_DIR=/srv/input
ENV OUTPUT_DIR=/srv/output
RUN mkdir -p ${INPUT_DIR} ${OUTPUT_DIR}
VOLUME ${INPUT_DIR} ${OUTPUT_DIR}

# setup the files
WORKDIR /srv/chronoi-pilot
ADD . /srv/chronoi-pilot

# follow the log file
CMD /usr/bin/tail -n0 -f "${LOG}"
