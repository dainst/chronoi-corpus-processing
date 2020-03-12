#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import enum
import glob
import os.path

from corpus_reading import TagInContext, Document, DocumentLine


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
        self.attr_name = attr_name

    def involves_tag_with(self, attr: str, value: str) -> bool:
        result = False
        for tag in self.tags:
            if tag.attr(attr) and tag.attr(attr) == value:
                result = True
                break
        return result


class TaskEvaluation:

    NAN = float('nan')

    def __init__(self, task_type: TaskType, results=None):
        self.types_to_results = {}
        self.task_type = task_type
        self.results = []
        if results:
            self.add_results(results)

    @property
    def tp(self) -> int:
        return self.no_of_results(ResultType.TP)

    @property
    def fp(self) -> int:
        return self.no_of_results(ResultType.FP)

    @property
    def fn(self) -> int:
        return self.no_of_results(ResultType.FN)

    @property
    def max_matches(self) -> int:
        return self.no_of_results(ResultType.ATTR_MATCH_POSSIBLE)

    @property
    def precision(self) -> float:
        if self.tp == 0 and self.fp == 0:
            return self.NAN
        return self.tp / (self.tp + self.fp)

    @property
    def recall(self) -> float:
        if self.tp == 0 and self.fn == 0:
            return self.NAN
        return self.tp / (self.tp + self.fn)

    @property
    def f1_score(self) -> float:
        return self.fn_score(1.0)

    def fn_score(self, weight: float = 1.0) -> float:
        p, r = (self.precision, self.recall)
        if p == 0 and r == 0:
            return self.NAN
        return ((1 + weight ** 2) * p * r) / (weight ** 2 * p + r)

    @property
    def accuracy(self):
        if self.max_matches == 0:
            return self.NAN
        return self.tp / self.max_matches

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

    def no_of_results(self, result_type: ResultType) -> int:
        return len(self.get_results(result_type))

    def get_results(self, result_type: ResultType) -> [Result]:
        return self.types_to_results.get(result_type, [])


class Comparator:

    def __init__(self, gold_doc: Document, system_doc: Document, tag_name: str, attributes: [str] = None):
        self.gold_doc = gold_doc
        self.system_doc = system_doc
        self.tag_name = tag_name
        self.attributes = attributes if attributes else []
        self.results = []

    def _note_tag_relaxed(self, result_type: ResultType, tags: [TagInContext]):
        self.results.append(Result(TaskType.TAG_RELAXED, result_type, tags))

    def _note_tag_strict(self, result_type: ResultType, tags: [TagInContext]):
        self.results.append(Result(TaskType.TAG_STRICT, result_type, tags))

    def _note_attr_result(self, result_type: ResultType, tags: [TagInContext], attr_name: str):
        self.results.append(Result(TaskType.ATTRIBUTE, result_type, tags, attr_name))

    def _note_result_for_all_attribute_tasks(self, result_type: ResultType, tags: [TagInContext]):
        for attr_name in self.attributes:
            self._note_attr_result(result_type, tags, attr_name)

    def compare(self) -> [Result]:
        # TODO: Consistency checks for documents
        for idx, gold_line in enumerate(self.gold_doc.lines):
            self._compare_lines(gold_line, self.system_doc.line_at(idx))
        return self.results

    def _compare_lines(self, gold_line: DocumentLine, system_line: DocumentLine):
        gold_tags = gold_line.get_tags_with_name(self.tag_name)
        system_tags = system_line.get_tags_with_name(self.tag_name)

        # collect overlapping tags, count them as true positives for
        # the relaxed tag matching task and as possible matches for the
        # attribute matching tasks, then trigger further comparison
        overlapping = set()
        for gold_tag in gold_tags:
            for system_tag in system_tags:
                if gold_tag.overlaps(system_tag):
                    overlapping.add((gold_tag, system_tag))
                    self._note_tag_relaxed(ResultType.TP, [gold_tag, system_tag])
                    self._note_result_for_all_attribute_tasks(ResultType.ATTR_MATCH_POSSIBLE, [gold_tag, system_tag])
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


class PrintUtil:

    @staticmethod
    def _tab_print(name: str, value):
        template = "%20s: "
        template += "%8d" if type(value) == int else "%8.5f"
        print(template % (name, value))

    @classmethod
    def print_evaluation(cls, evaluation: TaskEvaluation, task_name: str):
        infos = [
            ("TP", evaluation.tp),
            ("FP", evaluation.fp),
            ("FN", evaluation.fn),
            ("precision", evaluation.precision),
            ("recall", evaluation.recall),
            ("F.5", evaluation.fn_score(0.5)),
            ("F1", evaluation.f1_score),
            ("F2", evaluation.fn_score(2.0)),
        ]

        if evaluation.task_type == TaskType.ATTRIBUTE:
            infos.append(("max_matches", evaluation.max_matches))
            infos.append(("accuracy", evaluation.accuracy))

        print(f"~~~~{task_name}~~~~")
        for (k, v) in infos:
            cls._tab_print(k, v)

    @classmethod
    def print_results_csv(cls, file, results: [Result]):
        writer = csv.writer(file, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator=os.linesep)
        cls._print_results_csv_header(writer)
        for result in results:
            cls._print_result_csv_line(writer, result)

    @staticmethod
    def _print_results_csv_header(csv_writer):
        header_row = [
            "task_type", "attr_name", "result_type",
        ]
        tag_headers = [
            "basename", "lineno", "is_gold", "text_pos_start", "text_pos_end",
            "attr_tid", "attr_type", "attr_value", "attr_literature_time",
            "before_text", "text", "after_text",
        ]
        for tag_no in [1, 2]:
            header_row += map(lambda col_name: f"tag{tag_no}_{col_name}", tag_headers)
        csv_writer.writerow(header_row)

    @staticmethod
    def _print_result_csv_line(csv_writer, result: Result):
        row = [result.task_type.name, result.attr_name, result.result_type.name]
        for idx, tag in enumerate(result.tags):
            row += [
                tag.doc.basename,
                tag.idx_of_line + 1,
                tag.is_gold,
                tag.start_in_doc_text,
                tag.end_in_doc_text,
                tag.attr("tid"),
                tag.attr("type"),
                tag.attr("value"),
                tag.attr("literature-time"),
                tag.text_before(30),
                tag.text,
                tag.text_after(30).rstrip()
            ]
            if idx > 1:
                break
        csv_writer.writerow(row)


def process_files(gold_file: str, system_file: str, basename: str) -> [Result]:
    gold_doc = Document(path=gold_file, basename=basename, is_gold=True)
    system_doc = Document(path=system_file, basename=basename, is_gold=False)
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

    if args.only_with_attr:
        attr, value = args.only_with_attr.split(":", maxsplit=1)
        results = [r for r in results if r.involves_tag_with(attr=attr, value=value)]

    if args.disregard_with_attr:
        attr, value = args.disregard_with_attr.split(":", maxsplit=1)
        results = [r for r in results if not r.involves_tag_with(attr=attr, value=value)]

    if args.print_results_csv:
        import sys
        PrintUtil.print_results_csv(sys.stdout, results)
    else:
        to_print = [
            ("RELAXED TAG", TaskType.TAG_RELAXED, filter(lambda r: r.task_type == TaskType.TAG_RELAXED, results)),
            ("STRICT TAG", TaskType.TAG_STRICT, filter(lambda r: r.task_type == TaskType.TAG_STRICT, results)),
        ]
        for attr in ["type", "value"]:
            attr_results = filter(lambda r: r.task_type == TaskType.ATTRIBUTE and r.attr_name == attr, results)
            name = f"ATTR MATCHING: \"{attr}\""
            to_print.append((name, TaskType.ATTRIBUTE, list(attr_results)))
        for (name, task_type, rs) in to_print:
            evaluation = TaskEvaluation(task_type=task_type, results=rs)
            PrintUtil.print_evaluation(evaluation, name)


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
    parser.add_argument("--only_with_attr", type=str, default="",
                        help="Format: 'attr:value'. Only include results involving tags with an attribute equal to the value.")
    parser.add_argument("--disregard_with_attr", type=str, default="",
                        help="Format: 'attr:value'. Disregard results involving tags with an attribute equal to the value.")
    parser.add_argument("--print_results_csv", action="store_true",
                        help="Instead of printing evaluation results, output detailed csv records for each decision.")

    main(parser.parse_args())
