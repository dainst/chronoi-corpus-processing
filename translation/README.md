
# Translation of Corpus resources

This folder has some scripts which are used to translate either the corpus itself or the temponyms used for time tagging.

This is all very preliminary work without a fixed workflow, so some examples on how this was used are just in this readme instead of in a dedicated script.

All the following commands were executed in the docker container, e.g. after a `docker exec chronoi-pilot -it bash`

Translation of the corpus:

```bash
./translate_en_corpus.sh corpus_dir
```

Translation of temponyms by idai.vocab:

```bash
mkdir -p /srv/output/temponym-translations
while read -r line
do
    python3 translation/translate_by_idai_vocab.py "$line"
done < /srv/output/heideltime_temponym_files/en_repattern.txt > /srv/output/temponym-translations/translate_en_idai_vocab.txt
```


Translation of temponyms by dbpedia:

```bash
while read -r line
do
    python3 translation/translate_by_dbpedia.py "$line"
done < /srv/output/heideltime_temponym_files/en_repattern.txt > /srv/output/temponym-translations/translate_en_dbpedia.txt
```

For the translation of temponyms using google:

```bash
for lang in fr it es de
do
    translate -c 'google' -d "$lang" -p /srv/output/heideltime_temponym_files/en_repattern.txt
done
```

One-Liner to merge the google translation files and bring them in the same format as the other translation files (slow, because of python startup, awk would be faster, but we need the python escaping later):

```bash
paste -d '#' /srv/output/heideltime_temponym_files/en_repattern.txt /srv/output/heideltime_temponym_files/translate_* | \
while read -r line
do
    python3 -c "import sys; line=sys.argv[1]; en, de, es, fr, it = line.split('#'); print([('en', en), ('de', de), ('es', es), ('fr', fr), ('it', it)])" "$line"
done > /srv/output/temponym-translations/translate_en_google.txt
```

To merge the translations of temponyms into an overview .csv-File and at the same time create the heideltime pattern and normalization files for the automatic translations:

```bash
python3 translation/merge_temponym_translations.py
```
