
# Chronoi Pilot Corpus Processing

A bunch of scripts for the chronoi pilot corpus partially handling (and more importantly documenting) the steps taken for:
 
 * (pre-)processing
 * basic corpus analysis
 * time-tagging
 * gathering temponym data
 * automatic translation of temponyms and corpus data
 * some evaluation or preparation for evaluation

This comes in the form of two docker containers which can be started with:

```bash
docker-compose up
```

The container `chronoi-pilot` expects two directory paths in a `.env`-file, one for output and for input. An example is in the `.env.example`.

The container `heideltime` offers a command `heideltime` that can be used with e.g. `docker exec`. It mounts the output directory of the `chronoi-pilot` container so that it can work on the data produced by that container, e.g. from pre-processing.

Examples for the usage of both containers from the host are given in the `./experiments` folder.

Examples on how to use the translation scripts can be found in the `translation/README.md`.
