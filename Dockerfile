
FROM python:3

# install general dependencies
RUN apt-get update
RUN apt-get -y install \
    ghostscript \
    python3-dev \
    libhunspell-dev \
    plotutils

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
    SPARQLWrapper \
    beautifulsoup4 \
    lxml \
    tablign \
    csvkit

# download tokenization data for nltk
RUN python3 -c "import nltk; nltk.download('punkt')"

# install xidel for comand line xpath instructions
RUN wget --quiet "https://sourceforge.net/projects/videlibri/files/Xidel/Xidel%200.9.8/xidel-0.9.8.linux64.tar.gz"
RUN tar xzf "xidel-0.9.8.linux64.tar.gz" -C "/usr/bin" && rm "xidel-0.9.8.linux64.tar.gz"

# copy hunspell dictionaries in place
COPY resources/hunspell/*.aff  resources/hunspell/*.dic /usr/share/hunspell/

# create the log file if it doesn't exist
ARG log_file=/var/log/chronoi-pilot.log
RUN touch ${log_file}
# use ENV to have ${LOG} avalilable in the CMD-line below
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
