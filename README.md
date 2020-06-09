
# Chronoi Corpus Processing

This is a collection of loosely related scripts and other resources that were used in setting up the Chronoi pilot corpus as well as the extended multilingual corpus. They are meant to document and make reproducible the following steps in corpus setup and analysis:


 * (pre-)processing of the texts (with [`preprocessing.py`](preprocessing.py) using [`preprocessing`](preprocessing/))
 * guidelines and tools for annotation (at [`annotation`](annotation/))
 * time-tagging (dockerized at [`heideltime`](heideltime) and using [our fork](https://github.com/dainst/heideltime) as a subproject)
 * gathering temponym data (at [`heideltime/scripts`](heideltime/scripts))
 * evaluation and preparation for evaluation ([`postprocessing`](postprocessing))
 * basic corpus analysis (also at [`postprocessing`](postprocessing) and [`experiments`](experiments))

Some scripts cover experimental steps that were never actually used in the end. These include:

* automatic translation of temponyms and corpus data (at [`translation`](translation))
* using machine learning approaches in the detection step (at [`learning`](learning))

## Setup and use

The main container `chronoi-pilot` expects two directory paths in a `.env`-file, one for output and for input. An example is in the [`.env.example`](.env.example). The input folder is expected to contain pdf- and/or text files to process.

To pull our heideltime fork as a submodule, run:

```bash
git submodule update --init
```

The total setup comes in the form of three docker containers which can now be started with:

```bash
docker-compose up
```

Besides the `chronoi-pilot` container there are two additional containers b which will be started by that command.

The `heideltime` container offers a command `heideltime` that can be used with e.g. `docker exec`. It mounts the output directory of the `chronoi-pilot` container so that it can work on the data produced by that container.

The container `tempeval3` also mounts the output directory of the `chronoi-pilot` container so that it can work on the data produced by that container. It was mainly used for checking our evaluation against an official script and will probably not be needed for most use cases.

**Examples** for the usage of the containers from the host are given in the [`experiments`](experiments) folder.
