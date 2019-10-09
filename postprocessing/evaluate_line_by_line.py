#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import bs4
import enum
import glob
import os.path


class TaskType(enum.Enum):
    TAG_STRICT = 0
    TAG_RELAXED = 1
    ATTRIBUTE = 2


class ResultType(enum.Enum):
    TP = 0
    FP = 1
    FN = 2
    ATTR_MATCH_POSSIBLE = 3


class Result:

    def __init__(self, task_type: TaskType, result_type: ResultType, tags: [TagInContext], attr_name: str = ""):
        self.result_type = result_type
        self.task_type = task_type
        self.tags = tags
        if self.task_type == TaskType.ATTRIBUTE:
            self.attr_name = attr_name


class TaskEvaluation:

    def __init__(self, task_type: TaskType, results=None):
        self.types_to_results = {}
        self.task_type = task_type
        self.results = []
        if results:
            self.add_results(results)

    @staticmethod
    def _precision(tp: int, fp: int):
        return tp / (tp + fp)

    @staticmethod
    def _recall(tp: int, fn: int):
        return tp / (tp + fn)

    @staticmethod
    def _fn_score(precision: float, recall: float, weight: float = 1.0):
        return ((1 + weight ** 2) * precision * recall) / (weight ** 2 * precision + recall)

    @staticmethod
    def _add_to_dict_list(result_dict: dict, key, result):
        result_list = result_dict.get(key, [])
        result_list.append(result)
        result_dict[key] = result_list

    def add_result(self, result: Result):
        self._add_to_dict_list(self.types_to_results, result.result_type, result)

    def add_results(self, results: [Result]):
        for result in results:
            self.add_result(result)

    @staticmethod
    def _tab_print(name: str, value):
        template = "%20s: "
        template += "%8d" if type(value) == int else "%8.5f"
        print(template % (name, value))

    def print_evaluation(self, task_name):
        tp = len(self.types_to_results.get(ResultType.TP, []))
        fp = len(self.types_to_results.get(ResultType.FP, []))
        fn = len(self.types_to_results.get(ResultType.FN, []))
        precision = self._precision(tp=tp, fp=fp)
        recall = self._recall(tp=tp, fn=fn)
        f1 = self._fn_score(precision, recall, 1.0)

        infos = [
            ("TP", tp),
            ("FP", fp),
            ("FN", fn),
            ("precision", precision),
            ("recall", recall),
            ("F1", f1)
        ]

        if self.task_type == TaskType.ATTRIBUTE:
            max_matches = len(self.types_to_results.get(ResultType.ATTR_MATCH_POSSIBLE, []))
            accuracy = tp / max_matches
            infos.append(("max_matches", max_matches))
            infos.append(("accuracy", accuracy))

        print(f"~~~~TASK: {task_name}~~~~")
        for (k, v) in infos:
            self._tab_print(k, v)


class Comparator:

    def __init__(self, gold_doc: Document, system_doc: Document, tag_name: str, attributes: [str] = None):
        self.gold_doc = gold_doc
        self.system_doc = system_doc
        self.tag_name = tag_name
        self.attributes = attributes if attributes else []
        self.results = []

    def compare(self) -> [Result]:
        # TODO: Consistency checks for documents
        for idx, gold_line in enumerate(self.gold_doc.lines):
            self._compare_lines_at(idx)
        return self.results

    def _build_tags_in_context(self, doc: Document, line_idx: int):
        xml_doc = doc.line_xml_doc(line_idx)
        tags = xml_doc.find_all(self.tag_name)
        return list(map(lambda t: TagInContext(tag=t, doc=doc, line_idx=line_idx), tags))

    def _note_tag_relaxed(self, result_type: ResultType, tags: [TagInContext]):
        self.results.append(Result(TaskType.TAG_RELAXED, result_type, tags))

    def _note_tag_strict(self, result_type: ResultType, tags: [TagInContext]):
        self.results.append(Result(TaskType.TAG_STRICT, result_type, tags))

    def _note_attr_result(self, result_type: ResultType, tags: [TagInContext], attr_name: str):
        self.results.append(Result(TaskType.ATTRIBUTE, result_type, tags, attr_name))

    def _note_result_for_all_attribute_tasks(self, result_type: ResultType, tags: [TagInContext]):
        for attr_name in self.attributes:
            self._note_attr_result(result_type, tags, attr_name)

    def _compare_lines_at(self, line_idx: int):
        gold_tags = self._build_tags_in_context(self.gold_doc, line_idx)
        system_tags = self._build_tags_in_context(self.system_doc, line_idx)

        # collect overlapping tags, count them as true positives for
        # the relaxed tag matching task and as possible matches for the
        # attribute matching tasks, then trigger further comparison
        overlapping = set()
        for gold_tag in gold_tags:
            for system_tag in system_tags:
                if gold_tag.overlaps(system_tag):
                    overlapping.add((gold_tag, system_tag))
                    self._note_tag_relaxed(ResultType.TP, [gold_tag, system_tag])
                    self._note_result_for_all_attribute_tasks(ResultType.ATTR_MATCH_POSSIBLE, [])
                    self._compare_tags(gold_tag, system_tag)

        # the non-overlapping tags count as false positives or false negatives for
        # the relaxed tag matching task as well as the strict tag matching task
        # and all attribute matching tasks
        matched_gold = {g for (g, _) in overlapping}
        matched_system = {s for (_, s) in overlapping}
        for tag in {t for t in gold_tags if t not in matched_gold}:
            self._note_tag_relaxed(ResultType.FN, [tag])
            self._note_tag_strict(ResultType.FN, [tag])
            self._note_result_for_all_attribute_tasks(ResultType.FN, [tag])
        for tag in {t for t in system_tags if t not in matched_system}:
            self._note_tag_relaxed(ResultType.FP, [tag])
            self._note_tag_strict(ResultType.FP, [tag])
            self._note_result_for_all_attribute_tasks(ResultType.FP, [tag])

    def _compare_tags(self, gold_tag: TagInContext, system_tag: TagInContext):
        if gold_tag.text.strip() == system_tag.text.strip():
            self._note_tag_strict(ResultType.TP, [gold_tag, system_tag])
        else:
            # To reproduce the tempeval3 results, both recall and precision have
            # to be negatively impacted by a bad strict match
            self._note_tag_strict(ResultType.FP, [gold_tag, system_tag])
            self._note_tag_strict(ResultType.FN, [gold_tag, system_tag])

        for attr_name in self.attributes:
            self._compare_attribute_of_tags(attr_name, gold_tag, system_tag)

    def _compare_attribute_of_tags(self, attr_name: str, gold_tag: TagInContext, system_tag: TagInContext):
        gold_value = gold_tag.attr(attr_name)
        if not bool(gold_value):
            return
        else:
            if gold_value == system_tag.attr(attr_name):
                self._note_attr_result(ResultType.TP, [gold_tag, system_tag], attr_name)
            else:
                # To reproduce the tempeval3 results, both recall and precision have
                # to be negatively impacted by a bad attribute match
                self._note_attr_result(ResultType.FP, [gold_tag, system_tag], attr_name)
                self._note_attr_result(ResultType.FN, [gold_tag, system_tag], attr_name)


class Document:

    def __init__(self, path: str, basename: str):
        self.path = path
        self.basename = basename
        self.lines = self._read_lines()
        self._line_xml_docs = {}

    def _read_lines(self) -> [str]:
        with open(self.path) as f:
            return f.read().splitlines()

    def _build_line_xml_doc(self, idx) -> bs4.BeautifulSoup:
        doc = bs4.BeautifulSoup(self.lines[idx], "lxml")
        self._line_xml_docs[idx] = doc
        return doc

    def line_xml_doc(self, idx: int):
        if idx in self._line_xml_docs:
            return self._line_xml_docs[idx]
        else:
            return self._build_line_xml_doc(idx)


class TagInContext:

    def __init__(self, tag: bs4.Tag, doc: Document, line_idx: int):
        self.tag = tag
        self.doc = doc
        self.line_idx = line_idx
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
    def text(self) -> str:
        return self.tag.text

    @property
    def line(self) -> str:
        return self.doc.lines[self.line_idx]

    def attr(self, k: str) -> str:
        return self.tag.attrs.get(k, "")

    def overlaps(self, other: TagInContext) -> bool:
        return bool(set(self._span).intersection(set(other._span)))


def process_files(gold_file: str, system_file: str, basename: str) -> [Result]:
    gold_doc = Document(path=gold_file, basename=basename)
    system_doc = Document(path=system_file, basename=basename)
    comparator = Comparator(gold_doc=gold_doc, system_doc=system_doc, tag_name="timex3", attributes=["type", "value"])
    return comparator.compare()


def get_files_from_arg(arg_value: str):
    if os.path.isdir(arg_value):
        return glob.glob(os.path.join(arg_value, "*"))
    else:
        return [arg_value]


def basename_without_extension(path: str) -> str:
    path = os.path.basename(path)
    return ".".join(path.split(".")[:-1])


def find_file_containing_basename_of(basename: str, list_of_paths: str):
    matches = list(filter(lambda s: basename in s, list_of_paths))
    return matches[0] if len(matches) > 0 else None


def main(args):
    gold_files = get_files_from_arg(args.gold)
    system_files = get_files_from_arg(args.system)

    results = []
    for system_file in system_files:
        basename = basename_without_extension(system_file)
        try:
            gold_file = next(p for p in gold_files if basename in p)
        except StopIteration:
            print("WARN: No matching gold file for: " + basename)
            continue
        results += process_files(gold_file=gold_file, system_file=system_file, basename=basename)

    relaxed_results = filter(lambda r: r.task_type == TaskType.TAG_RELAXED, results)
    evaluation = TaskEvaluation(TaskType.TAG_RELAXED, relaxed_results)
    evaluation.print_evaluation("RELAXED TAG")

    strict_results = filter(lambda r: r.task_type == TaskType.TAG_STRICT, results)
    evaluation = TaskEvaluation(TaskType.TAG_STRICT, strict_results)
    evaluation.print_evaluation("STRICT TAG")

    for attr in ["type", "value"]:
        rs = filter(lambda r: r.task_type == TaskType.ATTRIBUTE and r.attr_name == attr, results)
        evaluation = TaskEvaluation(TaskType.ATTRIBUTE, rs)
        evaluation.print_evaluation("ATTR MATCHING: " + attr)


if __name__ == '__main__':

    description = """
        Evaluate two annotation directories, one with the gold standard and one with the system files.
        Assumes that both files have the same text (without xml tags) on each line and that no tag spans more than
        one line.
        Assumes that files in the gold dir have a name containing the basename of the respective system file.
    """
    description = "".join(map(str.lstrip, description.splitlines()))

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("gold", type=str, help="The directory with the gold standard files or one such file.")
    parser.add_argument("system", type=str, help="The directory with system annotation files or one such file.")

    main(parser.parse_args())
