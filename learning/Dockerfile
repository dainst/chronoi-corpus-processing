
# Example usage:
#   docker build --tag chronoi/testdl .
#   docker rm testdl && docker run -d --name testdl -v ~/Downloads/entity-annotated-corpus:/srv/data -v ~/Projekte/chronoi/pilotkorpus-code/learning:/scripts chronoi/testdl
#   docker exec -it testdl python3 test_ner_ml.py --test /srv/data/ner_dataset_timex_single_attr.csv

FROM tensorflow/tensorflow:1.12.3-py3

RUN apt-get update && apt-get -y install git

# Only necessary for the 07_bert experiment
# RUN pip3 install pytorch-pretrained-bert==0.4.0

# The versions of keras and keras_contrib are taken from the time of the article, i.e. Nov. 2017
RUN pip3 install keras==2.1.1 \
                 seqeval==0.0.6 \
                 git+https://www.github.com/keras-team/keras-contrib.git@aeebb8c \
                 eli5 \
                 sklearn-crfsuite \
                 tensorflow-hub


ENV PYTHONIOENCODING "UTF-8"

WORKDIR /scripts
ADD . .

# Entrypoint is the same as the parent container
# This serves notebooks from /notebook, we might use it in the future
CMD ["/run_jupyter.sh", "--allow-root"]
