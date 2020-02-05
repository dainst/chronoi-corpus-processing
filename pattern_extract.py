import argparse
from collections.abc import Iterable
import pickle
import re
import sys


class PositionedText(object):
    window = 10

    def __init__(self):
        self.text = ""
        self.span = None
        self.text_before = ""
        self.text_after = ""

    def __eq__(self, other):
        return self.text == other.text and self.span == other.span

    def overlaps(self, other):
        s, o = (self.span, other.span)
        if len(s) == 0 or len(o) == 0:
            return False
        return ((s.start < o.stop and s.stop > o.start) or
                (s.stop > o.start and o.stop > s.start))

    @classmethod
    def create_from_text_and_match(cls, text: str, match: re.Match):
        result = PositionedText()
        result.text = match.group(0)

        start, end = match.span()
        result.span = range(start, end)
        result.text_before = _safe_slice(text, start - cls.window, start)
        result.text_after = _safe_slice(text, end, end + cls.window)

        return result

    def is_empty(self):
        return (len(self.text) == 0) or (len(self.span) == 0)


def _safe_slice(text, start, end):
    if start < 0:
        start = 0
    if end <= start:
        end = start
    if end >= len(text):
        end = len(text)
    return text[start:end]


def extract(text, patterns):
    """
    Removes patterns from the text and returns it together with the
    ExtractedText objects. If pattern matches overlap in the text, both
    are extracted.

    :param text: String The text to remove patterns from
    :param patterns: [RegExp] The patterns to remove.
    :return: (new_text: string, snippets: [ExtractedText]) A pair,
        with new_text and snippets such that new_text
        is the old text with all occurences of text removed and snippets
        is a list of ExtractedText objects, that can later be inserted to
        restitute the original text.
    """
    if not isinstance(text, str):
        raise ValueError("Input is not a string, but: ", type(text))
    if not isinstance(patterns, Iterable):
        raise ValueError("patterns is not a list of strings or re.Patterns.")
    pts = []
    for pattern in patterns:
        pts += _create_positioned_texts(text, _make_pattern(pattern))
    pts = [pt for pt in pts if not pt.is_empty()]
    ranges = [pt.span for pt in pts]
    new_text = _remove_text_within_ranges(text, ranges)
    return new_text, pts


def _make_pattern(pattern: object):
    if isinstance(pattern, re.Pattern):
        return pattern
    elif isinstance(pattern, str):
        return re.compile(pattern)
    else:
        raise ValueError(f"Not a string or re.Pattern: '{pattern}'")


def _create_positioned_texts(text, pattern: re.Pattern):
    matches = pattern.finditer(text)
    return [PositionedText.create_from_text_and_match(text, match) for match in matches]


def _remove_text_within_ranges(text, ranges):
    result = ""
    for pos, char in enumerate(text):
        should_skip = False
        for r in ranges:
            if pos in r:
                should_skip = True
                break
        if not should_skip:
            result += char
    return result


def integrate(xml_text, positioned_texts):
    """
    Changes the xml document by integrating the positioned texts
    at the relevant places.

    If the provided xml document's text was the result of an extract(),
    this operation reverses that extraction.

    :param xml_text: str The xml to integrate the positioned_texts into
    :param positioned_texts: The texts to integrate.
    :return: An xml text with the content of the positioned texts inserted
             at the correct places.
    """
    targets = _sort_positioned_texts_by_span_begin(positioned_texts)
    target = targets.pop(0)
    result = ""
    inside_tag = False
    text_pos = 0

    for c in xml_text.strip():
        # First check if we should insert text from one or more of the targets
        while target is not None and text_pos in target.span:
            # as targets overlap, we need to calculate the insertion begin
            start = text_pos - target.span.start
            to_insert = target.text[start:]
            # do insert the text in the result
            result += to_insert
            text_pos += len(to_insert)
            assert (text_pos == target.span.stop)
            # pull the next target from the list, disregard the ones that
            # were covered by a previous insert
            while target is not None and target.span.stop <= text_pos:
                try:
                    target = targets.pop(0)
                except IndexError:
                    target = None
        # No further insertions should be necessary now
        assert (target is None or (text_pos < target.span.start))

        # Each char gets copied.
        result += c

        # Do a simple check if we are inside an xml tag
        if c == '<':
            inside_tag = True
        elif c == '>':
            inside_tag = False

        # Only increment the text position outside of tags
        if inside_tag or c == '>':
            continue
        else:
            text_pos += 1

    # at the end of the loop all targets should have been handled
    assert (target is None)
    assert (targets == [])

    return result


def _sort_positioned_texts_by_span_begin(positioned_texts):
    return sorted(positioned_texts, key=(lambda pt: pt.span.start))


def main_integrate(args: argparse.Namespace):
    extracts = pickle.load(args.extracts_file)

    xml_str = args.xml_file.read()
    new_text = integrate(xml_str, extracts)

    print(new_text, file=sys.stdout)


def main_extract(args: argparse.Namespace):
    if args.pattern is not None:
        patterns = [args.pattern]
    elif args.pattern_file is not None:
        patterns = args.pattern_file.read().splitlines(keepends=False)
    else:
        raise ValueError("No pattern or pattern file given.")

    text = args.text_file.read()
    new_text, positioned_texts = extract(text, patterns)

    pickle.dump(positioned_texts, args.extracts_file)
    print(new_text, file=sys.stdout)


def main_enumerate(args: argparse.Namespace):
    patterns = pickle.load(args.extracts_file)
    for pattern in patterns:
        print(pattern.text, file=sys.stdout)


if __name__ == "__main__":
    desc = """
    This program has two modes. In extraction-mode is deletes a bunch of patterns from a textfile and saves them
    in a separate file. In integration mode it reads a pattern file and an xml file and inserts the patterns at the
    right places in the text regardless of where the xml tags have been added.
    """

    parser = argparse.ArgumentParser(description=desc)

    subparsers = parser.add_subparsers(title="commands", help="extract, integrate or enumerate")
    parser_extract = subparsers.add_parser("extract", help="Extract patterns from a text file")
    parser_extract.add_argument("-f", "--pattern-file", type=argparse.FileType('r', encoding="utf-8"),
                                help="A file to read patterns from for extraction.")
    parser_extract.add_argument("-p", "--pattern", type=str,
                                help="Give a single pattern for extraction.")
    parser_extract.add_argument("text_file", type=argparse.FileType('r', encoding="utf-8"),
                                help="The file containing the text to extract from.")
    parser_extract.add_argument("extracts_file", type=argparse.FileType('wb'),
                                help="The .pickle file to write the extracted patterns into")
    parser_extract.set_defaults(func=main_extract)

    parser_integrate = subparsers.add_parser("integrate", help="Integrate patterns into an xml file.")
    parser_integrate.add_argument("xml_file", type=argparse.FileType('r', encoding="utf-8"),
                                  help="The file containing the xml to integrate extracted patterns into.")
    parser_integrate.add_argument("extracts_file", type=argparse.FileType('rb'),
                                  help="The .pickle file with extracted texts to read from.")
    parser_integrate.set_defaults(func=main_integrate)

    parser_enumerate = subparsers.add_parser("enumerate", help="Enumerate extracts from an extracts file.")
    parser_enumerate.add_argument("extracts_file", type=argparse.FileType('rb'),
                                  help="The .pickle file with extracts to enumerate.")
    parser_enumerate.set_defaults(func=main_enumerate)

    args = parser.parse_args()
    args.func(args)
