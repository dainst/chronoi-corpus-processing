#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import icu
import json
import os
import re


def sorted_strings(strings, locale=None):
    if locale is None:
        return sorted(strings)
    collator = icu.Collator.createInstance(icu.Locale(locale))
    return sorted(strings, key=collator.getSortKey)


def write_file_with_permissions(path: str, content: str, chmod_mode=0o776, open_mode='w', encoding='utf-8'):
    with open(path, open_mode, encoding=encoding) as f:
        f.write(content)
    os.chmod(path, chmod_mode)


def write_lines_to_resource_file(strings: list, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_file_with_permissions(path=path, content="\n".join(strings), chmod_mode=0o644)


class TemponymTransformer:
    """
    This gathers some methods to transform the names used  for temponyms during input
    (where they are cleaned from additions that are unlikely to appear in texts
    """

    # Matches explanatory parens as in "Terra sigillata (pottery style)"
    re_paren_after_whitespace = re.compile(r"\s+\([^\)]*\)")

    # Matches explanatory additions as in "Third Crusade, 1189-1192"
    re_comma_to_end = re.compile(r", .*$")

    @classmethod
    def clean(cls, name: str) -> str:
        name = re.sub(cls.re_paren_after_whitespace, "", name)
        name = re.sub(cls.re_comma_to_end, "", name)
        return name.strip()


class EpochBorder:
    """
    Represents a time at the start OR the end of an epoch, never both. This can be:
    1. A defined year.
    2. A range of years: earliest, latest
    """

    def __init__(self):
        self.earliest = None
        self.latest = None

    @staticmethod
    def __parse_chronontology_year(s):
        try:
            return int(s)
        except (ValueError, TypeError):
            return None

    def is_underspecified(self):
        return self.earliest is None or self.latest is None

    @classmethod
    def from_chronontology_timespan_part(cls, part) -> "EpochBorder":
        eb = EpochBorder()
        if "at" in part:
            val = cls.__parse_chronontology_year(part["at"])
            eb.earliest = val
            eb.latest = val
        elif "notBefore" in part and "notAfter" in part:
            eb.earliest = cls.__parse_chronontology_year(part["notBefore"])
            eb.latest = cls.__parse_chronontology_year(part["notAfter"])
        return eb


class Epoch:
    """
    "Epoch" is shorthand for any resource identified by a chronontology
    it. It can have mutlitple names in different languages, but has a
    single timespan.
    (Contrast this with a temponym that has a single name, but multiple
    epochs.)
    """

    def __init__(self, id_string: str, names: dict):
        """
        :param id_string: The chronontology id, e.g. "0VAfjnmGoXFj"
        :param names: The possible names mapped to languages, e.g. {"en": "hellenistic"}
        """
        self.id = id_string
        self.names = names
        self.begin = EpochBorder()
        self.end = EpochBorder()
        self.parent_ids = set()

    @staticmethod
    def from_chronontology_query_result(result: dict):
        res = result["resource"]

        id_string = res["id"]
        names: dict = res["names"]
        epoch = Epoch(id_string, names)

        if "hasTimespan" in res:
            # NOTE: This assumes that for each chronontology resource
            #   there is only one timespan with a definite begin and end.
            for timespan in res["hasTimespan"]:
                if "begin" in timespan and "end" in timespan:
                    epoch.begin = EpochBorder.from_chronontology_timespan_part(timespan["begin"])
                    epoch.end = EpochBorder.from_chronontology_timespan_part(timespan["end"])
                elif "timeOriginal" in timespan:
                    continue
                else:
                    print("Timespan not parsable: ", timespan)

        for key in ["isListedIn", "isPartOf", "fallsWithin", "isSenseOf"]:
            if "relations" in res and key in res["relations"]:
                epoch.parent_ids = epoch.parent_ids.union(set(res["relations"][key]))
        # an epoch must never be listed as its own parent
        assert epoch.id not in epoch.parent_ids

        return epoch

    def has_begin(self) -> bool:
        return self.begin is not None

    def has_end(self) -> bool:
        return self.end is not None

    def has_begin_and_end(self) -> bool:
        return self.has_begin() and self.has_end()

    def begin_and_end_are_specified(self):
        return self.has_begin() and self.has_end()\
               and not (self.begin.is_underspecified() or self.end.is_underspecified())

    def supports_language(self, lang_code):
        return lang_code in self.names.keys()

    def supports_any_of_languages(self, lang_codes):
        return not set(lang_codes).isdisjoint(self.names.keys())

    def get_names(self, lang_code):
        return self.names.get(lang_code, [])

    def is_usable(self, lang_codes) -> bool:
        if len(lang_codes) > 0:
            return self.begin_and_end_are_specified()
        else:
            return self.begin_and_end_are_specified() and self.supports_any_of_languages(lang_codes)

    def years_covered(self) -> int:
        if self.begin_and_end_are_specified():
            return self.end.latest - self.begin.earliest
        else:
            return 0

    def __str__(self):
        return f"<{self.id}, {self.names}>"


class Temponym:
    """
    A temponym is a single name, in one language, that might be shared
    by multiple epochs.
    """

    def __init__(self, name: str, lang: str):
        self.name = name
        self.lang = lang
        self.epochs = []

    def add_epoch(self, epoch: Epoch):
        # make sure that the epochs name is really present
        assert self.name in [TemponymTransformer.clean(n) for n in epoch.get_names(self.lang)]
        # add to the own collection only if isn't already present
        # (a few cases have the same name twice)
        if epoch.id not in [e.id for e in self.epochs]:
            self.epochs.append(epoch)

    def choose_representative_epoch(self) -> Epoch:
        assert len(self.epochs) > 0
        if len(self.epochs) == 1:
            return self.epochs[0]
        # Remove candidate epochs that have parents who are also candidates
        candidates = self.epochs.copy()
        for epoch in self.epochs:
            if any({e.id for e in candidates}.intersection(epoch.parent_ids)):
                candidates.remove(epoch)
        # If there are still candidates, just assume the epoch with the
        # greatest amount of years covered as the most general one
        if len(candidates) > 1:
            candidates = sorted(candidates, key=lambda e: e.years_covered(), reverse=True)
        return candidates[0]


class HeidelTimeWriter:

    locales = {
        "en": "en_US.utf8",
        "de": "de_DE.utf8",
    }

    def __init__(self, temponym: Temponym):
        self.temponym = temponym
        self.epoch = temponym.choose_representative_epoch()

    def write_epoch_range(self) -> str:
        begin = self._write_epoch_border(self.epoch.begin)
        end = self._write_epoch_border(self.epoch.end)
        return f"[{begin}, {end}]"

    def _write_epoch_border(self, eb: EpochBorder) -> str:
        if eb is None:
            return str(None)
        else:
            return f"{self._write_year(eb.earliest)}, {self._write_year(eb.latest)}"

    def _write_name(self) -> str:
        return self.temponym.name

    @staticmethod
    def _write_year(int_or_none) -> str:
        return str(None) if int_or_none is None else "%+05d" % int_or_none

    def _write_links(self) -> str:
        # currently only writes a single link
        return f"['http://chronontology.dainst.org/period/{self.epoch.id}']"

    def _pattern_line(self) -> str:
        return self._write_name()

    def _norm_line(self) -> str:
        return '"%s","%s,%s"' % (self._write_name(), self.write_epoch_range(), self._write_links())

    @classmethod
    def _collect_lines(cls, temponyms: [Temponym], lang_code: str, callback) -> list:
        lines = []
        for temponym in temponyms:
            writer = cls(temponym)
            lines.append(callback(writer))
        return sorted_strings(lines, cls.locales[lang_code])

    @classmethod
    def collect_norm_lines(cls, epochs: list, lang_code: str) -> list:
        return cls._collect_lines(epochs, lang_code, cls._norm_line)

    @classmethod
    def collect_pattern_lines(cls, epochs: list, lang_code: str) -> list:
        return cls._collect_lines(epochs, lang_code, cls._pattern_line)


def do_chronontology_export(export_file, output_directory):

    # read the export file
    with open(export_file, encoding="utf-8") as file:
        response = json.load(file)

    assert len(response["results"]) == int(response["total"]), \
        "Reported result length doesn't match actual result length"

    supported_languages = ["en", "de"]

    # actually create resources from the chronontology dump
    epochs = {}
    for idx, query_result in enumerate(response["results"]):
        epoch = Epoch.from_chronontology_query_result(query_result)
        epochs[epoch.id] = epoch
    usable = [e for e in epochs.values() if e.is_usable(supported_languages)]

    # transform the usable chronontology resources into temponyms
    temponyms = {lang: {} for lang in supported_languages}
    for epoch in usable:
        for lang in supported_languages:
            if epoch.supports_language(lang):
                for name in epoch.get_names(lang):
                    name = TemponymTransformer.clean(name)
                    temponym = temponyms[lang].get(name, Temponym(lang=lang, name=name))
                    temponym.add_epoch(epoch)
                    temponyms[lang][name] = temponym

    # write pattern and norm files for all supported languages
    for lang in supported_languages:
        ts = temponyms[lang].values()
        print(f"usable ({lang}): {len(ts)}")

        write_lines_to_resource_file(
            HeidelTimeWriter.collect_pattern_lines(ts, lang),
            os.path.join(output_directory, f"{lang}_repattern.txt")
        )
        write_lines_to_resource_file(
            HeidelTimeWriter.collect_norm_lines(ts, lang),
            os.path.join(output_directory, f"{lang}_norm.txt")
        )


if __name__ == '__main__':
    # by default the chronontology dump is expected to be in the same directory as this
    # script under "resources/chronontology.json"
    script_dir = os.path.dirname(os.path.realpath(__file__))
    default_chronontology_dump_path = os.path.join(script_dir, "resources", "chronontology.json")

    # by default the output goes into a new directory in the containers output directory
    corpus_out_dir = os.path.realpath(os.environ.get("OUTPUT_DIR", "."))
    default_out_dir = os.path.join(corpus_out_dir, "heideltime_temponym_files")

    parser = argparse.ArgumentParser(
        description="Reads a chronontology json dump and exports temponym definitions (pattern and rule files) for use with heideltime.")
    parser.add_argument("-i", "--in-file", default=default_chronontology_dump_path,
        type=str, help="A json export of the chronontology data (defaults to: %(default)s).")
    parser.add_argument("-o", "--out-dir", default=default_out_dir,
        type=str, help="The directory to put the generated files into (defaults to: %(default)s).")
    args = parser.parse_args()

    print("Input file:", args.in_file)
    print("Output dir:", args.out_dir)

    do_chronontology_export(args.in_file, args.out_dir)

