
import json
import os
import icu


def increments_count_in_dict(dictionary: dict, k):
    count = dictionary.setdefault(k, 0)
    dictionary[k] = count + 1


def sorted_strings(strings, locale=None):
    if locale is None:
        return sorted(strings)
    collator = icu.Collator.createInstance(icu.Locale(locale))
    return sorted(strings, key=collator.getSortKey)


def write_file_with_permissions(path: str, content: str, chmod_mode=0o776, open_mode='w'):
    with open(path, open_mode) as f:
        f.write(content)
    os.chmod(path, chmod_mode)


def write_lines_to_resource_file(strings: list, file_name: str):
    out_dir = os.path.realpath(os.environ["OUTPUT_DIR"])
    path = os.path.join(out_dir, "heideltime_temponym_files", file_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_file_with_permissions(path=path, content="\n".join(strings))


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
        else:
            print("----> ", part)
        return eb


class Temponym:

    def __init__(self, id_string: str, names: dict):
        """
        :param id_string: The chronontology id, e.g. "0VAfjnmGoXFj"
        :param names: The possible names mapped to languages, e.g. {"en": "hellenistic"}
        """
        self.id = id_string
        self.names = names
        self.begin = EpochBorder()
        self.end = EpochBorder()

    @staticmethod
    def from_chronontology_query_result(result: dict):
        res = result["resource"]

        id_string = res["id"]
        names: dict = res["names"]
        temponym = Temponym(id_string, names)

        if "hasTimespan" not in res:
            print(f"Resource without a Timespan: {id} (%s)" % names)
        else:
            for timespan in res["hasTimespan"]:
                if "begin" in timespan and "end" in timespan:
                    temponym.begin = EpochBorder.from_chronontology_timespan_part(timespan["begin"])
                    temponym.end = EpochBorder.from_chronontology_timespan_part(timespan["end"])
                elif "timeOriginal" in timespan:
                    continue
                else:
                    print("Timespan not parsable: ", timespan)
        return temponym

    def has_begin(self) -> bool:
        return self.begin is not None

    def has_end(self) -> bool:
        return self.end is not None

    def has_begin_and_end(self) -> bool:
        return self.has_begin() and self.has_end()

    def begin_and_end_are_specified(self):
        return not (self.begin.is_underspecified() or self.end.is_underspecified())

    def supports_language(self, lang_code):
        return lang_code in self.names.keys()

    def supports_any_of_languages(self, lang_codes):
        return not set(lang_codes).isdisjoint(self.names.keys())

    def get_names(self, lang_code):
        return self.names.get(lang_code, [])

    def is_usable(self, lang_codes) -> bool:
        border_is_defined = self.has_begin_and_end() and self.begin_and_end_are_specified()
        if len(lang_codes) > 0:
            return border_is_defined
        else:
            return border_is_defined and self.supports_any_of_languages(lang_codes)

    def __str__(self):
        return f"<{self.id}, {self.names} {HeidelTimeWriter(self).write_epoch_range()}>"


class HeidelTimeWriter:

    locales = {
        "en": "en_US.utf8",
        "de": "de_DE.utf8",
    }

    def __init__(self, temponym: Temponym):
        self.temponym = temponym

    def write_epoch_range(self) -> str:
        begin = self.__write_epoch_border(self.temponym.begin)
        end = self.__write_epoch_border(self.temponym.end)
        return f"[{begin}, {end}]"

    @staticmethod
    def __write_year(int_or_none) -> str:
        return str(None) if int_or_none is None else "%+05d" % int_or_none

    def __write_epoch_border(self, eb: EpochBorder) -> str:
        if eb is None:
            return str(None)
        else:
            return f"{self.__write_year(eb.earliest)}, {self.__write_year(eb.latest)}"

    def pattern_lines(self, lang_code: str) -> list:
        return [self.__pattern_line(name) for name in self.temponym.get_names(lang_code)]

    def __pattern_line(self, name) -> str:  # nopep8: Method cannot be static, used as callback
        return f"{name}"

    def norm_lines(self, lang_code: str):
        return [self.__norm_line(name) for name in self.temponym.get_names(lang_code)]

    def __norm_line(self, name) -> str:
        return '"%s","%s"' % (name, self.write_epoch_range())

    @classmethod
    def __collect_lines(cls, temponyms: list, lang_code: str, callback) -> list:
        lines = []
        for temponym in temponyms:
            writer = cls(temponym)
            for name in temponym.get_names(lang_code):
                lines.append(callback(writer, name))
        return sorted_strings(lines, cls.locales[lang_code])

    @classmethod
    def collect_norm_lines(cls, temponyms: list, lang_code: str) -> list:
        return cls.__collect_lines(temponyms, lang_code, cls.__norm_line)

    @classmethod
    def collect_pattern_lines(cls, temponyms: list, lang_code: str) -> list:
        return cls.__collect_lines(temponyms, lang_code, cls.__pattern_line)


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))
    export_file = os.path.join(script_dir, "resources", "chronontology.json")

    # read the export file
    with open(export_file) as file:
        response = json.load(file)

    assert len(response["results"]) == int(response["total"]), \
        "Reported result length doesn't match actual result length"

    disregard_counts = {"Language not supported": 0}
    language_keys_count = {"en": 0}
    supported_languages = ["en", "de"]

    # collect some statistics and initiate temponyms for each entry
    for query_result in response["results"]:
        resource = query_result["resource"]

        assert (resource is not None)
        assert ("names" in resource)

        for key in resource["names"]:
            if key not in supported_languages:
                increments_count_in_dict(disregard_counts, "Language not supported")
            else:
                increments_count_in_dict(language_keys_count, key)

    for key, value in disregard_counts.items():
        print(key, value)

    for key, value in language_keys_count.items():
        print(key, value)

    ts = {}
    for idx, query_result in enumerate(response["results"]):
        t = Temponym.from_chronontology_query_result(query_result)
        ts[t.id] = t

    usable = [t for _, t in ts.items() if t.is_usable(supported_languages)]
    unusable = [t for _, t in ts.items() if not t.is_usable(supported_languages)]

    print("usable/unusable/total: %d/%d/%d" % (len(usable), len(unusable), len(ts)))

    # write pattern and norm files for german and english
    combinations = {
        'de': ("de_repattern.txt", "de_norm.txt"),
        'en': ("en_repattern.txt", "en_norm.txt")
    }
    for lc, file_names in combinations.items():
        ts = [t for t in usable if t.supports_language(lc)]

        print(f"usable ({lc}): {len(ts)}")

        write_lines_to_resource_file(
            HeidelTimeWriter.collect_pattern_lines(ts, lc),
            file_names[0]
        )

        write_lines_to_resource_file(
            HeidelTimeWriter.collect_norm_lines(ts, lc),
            file_names[1]
        )
