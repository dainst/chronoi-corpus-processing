
# Translation of Corpus resources

This folder has some scripts which are used to translate either the corpus itself or the temponyms used for time tagging.

This is all very preliminary work without a fixed workflow, so some examples on how this was used are just in this readme instead of in a dedicated script.

All the following commands were executed in the docker container, e.g. after a `docker exec chronoi-pilot -it bash`

For the translation of the corpus:

```bash
./translate_en_corpus.sh /srv/output/006_separate_by_language
```

For the translation of temponyms by idai.vocab:

```bash
mkdir -p /srv/output/temponym-translations
while read -r line
do
    python3 translate_by_idai_vocab.py "$line"
done < /srv/output/heideltime_temponym_files/en_repattern.txt > /srv/output/temponym-translations/translate_en_idai_vocab.txt
```

For the translation of temponyms using google:

```bash
for lang in fr it es de
do
    translate -c 'google' -d "$lang" -p /srv/output/heideltime_temponym_files/en_repattern.txt
done
```


