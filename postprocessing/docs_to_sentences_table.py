#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import bs4
import csv
import glob
import langdetect
import os
import sys
import treetaggerwrapper

from nltk.tokenize import word_tokenize

try:
    from corpus_reading import Document
except ImportError:
    # Import for pytest as that will have a different path
    from .corpus_reading import Document

# TODO: Remove
os.environ['TAGDIR'] = "/home/david/Documents/Projekte/chronoi/tree-tagger"

languages = {
    "de": "german",
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "it": "italian"
}


taggers = {
    "de": None,
    "en": None,
    "es": None,
    "fr": None,
    "it": None
}

csv_writer = None


# The default function tag function using all possible ner values
def _tag_to_ner_name_default(tag: bs4.Tag, default="") -> str:
    if not isinstance(tag, bs4.Tag):
        return default

    # the ner name is either the tags name or the value of the type attribute
    if tag.name in ["timex3", "temponym", "TIMEX3"]:
        result = tag.name.lower()
    elif tag.name in ["dne"]:
        result = tag.get("type", default)
    else:
        result = default

    return result

def _tag_to_ner_name_only_non_timex(tag: bs4.Tag, default="") -> str:
    if not isinstance(tag, bs4.Tag):
        return default
    if tag.name == "dne":
        return tag.get("type", default)
    return default

def _tag_to_ner_name_only_time_stuff(tag: bs4.Tag, default="") -> str:
    if not isinstance(tag, bs4.Tag):
        return default
    if tag.name in ["timex3", "temponym", "TIMEX3"]:
        return tag.name.lower()
    return default

# A non-default tag function returning an NER-Range only for literature tags
def _tag_to_ner_name_literature(tag: bs4.Tag, default="") -> str:
    if not isinstance(tag, bs4.Tag):
        return default

    if tag.name == "literature":
        return tag.name
    else:
        return default


# the function to decide if a tag is a ner value
_tag_to_ner_name_fn = _tag_to_ner_name_default


class Prefixed:
    """
    Helper class for ner ranges, returns a "B-" prefix of the own name
    only once, afterwards, a "I-" is prefixed for the own name every time.
    """

    def __init__(self, name: str):
        self._used = False
        self.name = name

    def __repr__(self):
        return f"<Prefixed '{self.name}' {self._used}>"

    def get(self):
        if not self._used:
            prefix = "B-"
        else:
            prefix = "I-"
        self._used = True
        return prefix + self.name


def _get_writer():
    global csv_writer
    if csv_writer is None:
        csv_writer = csv.writer(sys.stdout, delimiter=",", quoting=csv.QUOTE_MINIMAL, lineterminator=os.linesep)
    return csv_writer


def _get_tagger(lang) -> any:
    if lang in taggers.keys() and taggers[lang] is None:
        taggers[lang] = treetaggerwrapper.TreeTagger(TAGLANG=lang)
    return taggers[lang]


def _pos_tag(words: [str], lang: str):
    tagger = _get_tagger(lang)
    # we do our own chunking, so call the treetagger with a list of words instead
    tags_strs = tagger.tag_text(words, tagonly=True)
    return treetaggerwrapper.make_tags(tags_strs, exclude_nottags=False, allow_extra=True)


def _print_csv_line(no, word, pos, tag):
    _get_writer().writerow([no, word, pos, tag])


def _print_csv_header():
    _print_csv_line("Sentence #", "Word", "POS", "Tag")


def _words_ner_range_list(tag: bs4.Tag, lang: str, ners=None, result=None) -> [(str, [str])]:
    """
    Word-tokenizes the text in the tag and for each word also returns a list of
    ner-ranges, the word is contained in. If the word is the first in the range,
    the name is prepended with "B-", else with "I-".

    A word is contained in an ner-range if is part of a certain tag. Cf. the test
    below for an example.
    """

    # initialize accumulators
    if result is None:
        result = []
    if ners is None:
        ners = []

    # if we have encountered a tag, add possible ner ranges and descend
    if isinstance(tag, bs4.Tag):
        ner_name = _tag_to_ner_name_fn(tag, "")
        if ner_name != "":
            ners.append(Prefixed(ner_name))
        for child in tag.children:
            _words_ner_range_list(child, lang=lang, ners=ners.copy(), result=result)

    # if we encounter a text noder, chunk that text and assign the collected ner ranges
    elif isinstance(tag, bs4.NavigableString) and not(isinstance(tag, bs4.ProcessingInstruction)):
        words = word_tokenize(str(tag), language=languages[lang])
        for i, word in enumerate(words):
            names = [ner.get() for ner in ners]
            result.append((word, names))

    return result


def _handle_sentence(sentence: bs4.Tag, lang: str, sentence_no: int) -> [(str, str, str, str)]:
    words_to_ner_ranges = _words_ner_range_list(sentence, lang="en")
    words = [w for (w, _) in words_to_ner_ranges]
    pos_tags = _pos_tag(words, lang)

    assert(len(words) == len(pos_tags))
    assert(len(words_to_ner_ranges) == len(pos_tags))

    sentence_no_str = f"Sentence: {sentence_no}"

    # Print something for empty lines
    if len(words_to_ner_ranges) == 0:
        return [(sentence_no_str, ".", ".", "O")]

    result = []
    for i, (word, ner_ranges) in enumerate(words_to_ner_ranges):
        pos_tag = pos_tags[i].pos
        ner_tag = "O"

        # the first (outermost) ner range is preferred for nested tags
        if len(ner_ranges) > 0:
            ner_tag = ner_ranges[0]

        # only the first element in a sentence gets a sentence no printed
        if i > 0:
            sentence_no_str = ""
        result.append((sentence_no_str, word, pos_tag, ner_tag))

    return result


def _get_files_from_arg(arg_value: str):
    if os.path.isdir(arg_value):
        return glob.glob(os.path.join(arg_value, "*"))
    else:
        return [arg_value]


def main(args: argparse.Namespace):
    global _tag_to_ner_name_fn

    if args.literature:
        _tag_to_ner_name_fn = _tag_to_ner_name_literature
    elif args.nes_only:
        _tag_to_ner_name_fn = _tag_to_ner_name_only_non_timex
    elif args.timex_only:
        _tag_to_ner_name_fn = _tag_to_ner_name_only_time_stuff
    else:
        _tag_to_ner_name_fn = _tag_to_ner_name_default


    files = _get_files_from_arg(args.input)

    _print_csv_header()

    # sentences are incremented across files
    sentence_no = 1
    for file in files:
        basename = os.path.basename(file)
        doc = Document(path=file, basename=basename)
        text = " ".join([line.text for line in doc.lines])
        lang = langdetect.detect(text)

        for line in doc.lines:
            result = _handle_sentence(line._xml_repr, lang=lang, sentence_no=sentence_no)
            for no, word, ner, pos in result:
                _print_csv_line(no, word, ner, pos)
            sentence_no += 1


if __name__ == '__main__':

    description = """
        Output a csv file with the sentences in the text, containing POS-Tags as well as NER-tags
        according to the xml tags used.
    """
    description = "".join(map(str.lstrip, description.splitlines()))

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", type=str, help="A directory or single file to use as input.")
    parser.add_argument("--literature", action="store_true", help="If set, only mark <literature/> contents as nes.")
    parser.add_argument("--nes-only", action="store_true", help="If set, only mark named entity contents, not time expressions as nes.")
    parser.add_argument("--timex-only", action="store_true", help="If set, only mark time expression contents, not other nes.")

    main(parser.parse_args())


# TESTTS

def test_words_ner_range_list():
    doc = '<s>pre<temponym>abc<dne type="person">def ghi</dne></temponym>post</s>'
    doc = bs4.BeautifulSoup(doc, "lxml-xml")
    result = _words_ner_range_list(doc, "en")
    expected = [
        ('pre',  []),
        ('abc',  ['B-temponym']),
        ('def',  ['I-temponym', 'B-person']),
        ('ghi',  ['I-temponym', 'I-person']),
        ('post', [])
    ]
    assert(result == expected)

    doc = '<s>pre<temponym><dne type="person">abc <TIMEX3>def</TIMEX3></dne> ghi</temponym>post</s>'
    doc = bs4.BeautifulSoup(doc, "lxml-xml")
    result = _words_ner_range_list(doc, "en")
    expected = [
        ('pre', []),
        ('abc', ['B-temponym', 'B-person']),
        ('def', ['I-temponym', 'I-person', 'B-timex3']),
        ('ghi', ['I-temponym']),
        ('post', [])
    ]
    assert (result == expected)


def test_handle_sentence():
    doc = '<s>pre<temponym>abc<dne type="person">def ghi</dne></temponym>post</s>'
    doc = bs4.BeautifulSoup(doc, "lxml-xml")
    result = _handle_sentence(doc, "en", 0)
    expected = [
        ("Sentence: 0", "pre", "PRP", "O"),
        ("",            "abc", "NN1", "B-temponym"),
        ("",            "def", "NN1", "I-temponym"),
        ("",            "ghi", "NN1", "I-temponym"),
        ("",           "post", "NN1", "O")
    ]
    assert(result == expected)
