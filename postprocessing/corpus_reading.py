#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import bs4


class DocumentLine:

    def __init__(self, doc: Document, line: str, previous: DocumentLine = None):
        self.doc = doc
        self.line = line
        self.idx = previous.idx + 1 if previous else 0
        self._xml_repr = self._build_xml_repr(line)
        self.length = len(self._xml_repr.text)
        self.start = previous.end + 1 if previous else 0
        self.end = self.start + self.length - 1

    @property
    def text(self):
        return self._xml_repr.text

    @property
    def is_gold(self):
        return self.doc.is_gold

    def _bounds_check_text_idx(self, idx: int) -> int:
        if idx < 0:
            idx = 0
        if idx > len(self.text):
            idx = len(self.text)
        return idx

    def text_at(self, start: int, end: int):
        start = self._bounds_check_text_idx(start)
        end = self._bounds_check_text_idx(end)
        return self.text[start:end]

    def get_tags_with_name(self, tag_name: str):
        tags = self._xml_repr.find_all(tag_name)
        return list(map(lambda t: TagInContext(tag=t, doc_line=self), tags))

    @staticmethod
    def _build_xml_repr(line: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(line, "lxml")


class Document:

    def __init__(self, path: str, basename: str, is_gold: bool):
        self.path = path
        self.basename = basename
        self.is_gold = is_gold
        self.lines = self._read_lines()

    def _read_lines(self) -> [DocumentLine]:
        with open(self.path) as f:
            lines = f.read().splitlines(keepends=True)
        return self._lines_to_doc_lines(lines)

    def _lines_to_doc_lines(self, lines: [str]) -> [DocumentLine]:
        result = []
        previous = None
        for line in lines:
            doc_line = DocumentLine(doc=self, line=line, previous=previous)
            result.append(doc_line)
            previous = doc_line
        return result

    def line_at(self, idx: int) -> DocumentLine:
        return self.lines[idx]


class TagInContext:

    def __init__(self, tag: bs4.Tag, doc_line: DocumentLine):
        self.tag = tag
        self.doc_line = doc_line
        self._span = self._determine_line_pos()

    def _determine_line_pos(self) -> range:
        start = self._count_chars_preceding(self.tag)
        return range(start, start + len(self.text))

    def _count_chars_preceding(self, tag: bs4.Tag, count: int = 0) -> int:
        previous = tag.previous
        if type(previous) == bs4.NavigableString:
            return self._count_chars_preceding(previous, count + len(previous))
        elif previous is None:
            return count
        else:
            return self._count_chars_preceding(previous, count)

    @property
    def doc(self) -> Document:
        return self.doc_line.doc

    @property
    def idx_of_line(self):
        return self.doc_line.idx

    @property
    def text(self) -> str:
        return self.tag.text

    @property
    def line(self) -> str:
        return self.doc_line.line

    @property
    def is_gold(self) -> bool:
        return self.doc_line.is_gold

    @property
    def start_in_line(self):
        return self._span[0]

    @property
    def end_in_line(self):
        return self._span[-1]

    @property
    def start_in_doc_text(self) -> int:
        return self.doc_line.start + self.start_in_line

    @property
    def end_in_doc_text(self) -> int:
        return self.doc_line.end + self.end_in_line

    def text_before(self, length: int) -> str:
        return self.doc_line.text_at(self.start_in_line - length, self.start_in_line)

    def text_after(self, length: int) -> str:
        return self.doc_line.text_at(self.end_in_line + 1, self.end_in_line + length)

    def attr(self, k: str) -> str:
        return self.tag.attrs.get(k, "")

    def overlaps(self, other: TagInContext) -> bool:
        return bool(set(self._span).intersection(set(other._span)))
