#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import bs4
import os
import glob
import re


class Config:

    def __init__(self):
        self.remove_tags = [
            {"tag": "temponym-fn"},
            {"tag": "TIMEX3", "attrs": {"check": "false-positive"}}
        ]
        self.lstrip_lines = True
        self.add_fake_dct = True
        self.strip_attrs = [ "check", "literature-time", "exploration-time" ]


def tag_matches_definition(elem: bs4.Tag, tag_def: dict) -> bool:
    result = False

    if elem.name == tag_def.get("tag"):
        result = True
        # if an attribute does not match,
        attrs = tag_def.get("attrs", {})
        for (k, v) in attrs.items():
            if elem.attrs.get(k, "") != v:
                result = False
    return result


def correct_tid_attr_if_needed(elem) -> None:
    if not(isinstance(elem, bs4.Tag) and elem.has_attr("tid")):
        return
    # in the annotation correction special ids prefixed with "C" were
    # used for corrections. This is not valid timeml according to the
    # xsd (though it is after the dtd...) we "correct" them
    match = re.compile(r"[cC](\d*)").match(elem.attrs.get("tid"))
    if match:
        new_id = "t00000000" + match[1]
        elem.attrs["tid"] = new_id


def correct_value_attr_if_needed(elem) -> None:
    if not(isinstance(elem, bs4.Tag) and elem.has_attr("value")):
        return
    # removes a minus sign from the type attribute and replaces it
    # with a "BC" at the end of the expression
    match = re.compile(r"-(.*)").match(elem.attrs.get("value"))
    if match:
        elem.attrs["value"] = "BC" + match[1]
    # also correct a leading plus sign by just removing it
    match = re.compile(r"\+(.*)").match(elem.attrs.get("value"))
    if match:
        elem.attrs["value"] = match[1]


def recursively_cleanup_element(elem: bs4.Tag, config: Config) -> None:
    if type(elem) == bs4.NavigableString:
        # text nodes are ignored
        return

    # Recurse to the child elements first so that changes in the
    # lower nodes are done first and do not cause trouble when
    # changing higher nodes later
    for child_elem in elem.children:
        recursively_cleanup_element(child_elem, config)

    # remove attributes if they fit one of the removal definitions
    for definition in config.remove_tags:
        if tag_matches_definition(elem, definition):
            elem.unwrap()
            break

    # handle attributes (should only be in TIMEX3s)
    correct_tid_attr_if_needed(elem)
    correct_value_attr_if_needed(elem)
    for attr_name in config.strip_attrs:
        elem.attrs.pop(attr_name, None)


def add_timeml_namespace_info(timeml_tag: bs4.Tag):
    new_attrs = {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://timeml.org/timeMLdocs/TimeML_1.2.1.xsd"
    }
    for k, v in new_attrs.items():
        timeml_tag.attrs[k] = v


def add_fake_dct_tag(timeml_tag: bs4.Tag):
    dct_str = '<DCT><TIMEX3 functionInDocument="CREATION_TIME" temporalFunction="false" tid="t0" type="DATE" value="1970-01-01">Fake time</TIMEX3></DCT>'
    dct_tag = bs4.BeautifulSoup(dct_str, "lxml-xml").findChild("DCT")
    timeml_tag.insert(0, dct_tag)


def wrap_contents_in_new_tag(elem: bs4.Tag, tag_name: str) -> bs4.Tag:
    new_tag = bs4.Tag(name=tag_name)
    new_tag.contents = elem.contents
    elem.contents = [new_tag]
    return elem


def cleanup_document(doc: bs4.BeautifulSoup, config: Config) -> bs4.BeautifulSoup:
    # cleanup the main document tags
    timeml_root = doc.findChild("TimeML")
    for child in timeml_root.children:
        if type(child) == bs4.Tag:
            recursively_cleanup_element(child, config)

    # work on the header-like elements adding valid namespace info and removing
    # the doctype if there is one
    doctype_tag = doc.find(string=lambda tag: isinstance(tag, bs4.Doctype))
    if doctype_tag:
        doctype_tag.extract()
    # add_timeml_namespace_info(timeml_root)
    wrap_contents_in_new_tag(timeml_root, "TEXT")

    if config.add_fake_dct:
        add_fake_dct_tag(timeml_root)

    return doc


def trim_whitespace_at_start_of_each_line(text: str):
    return "".join(map(str.lstrip, text.splitlines(keepends=True)))


def handle_cleanup(input_path: str, output_path: str, config: Config):
    # read the original
    with open(input_path, "r") as input_file:
        doc = bs4.BeautifulSoup(input_file, "lxml-xml", from_encoding="utf-8")

    # do the cleanup and convert to a utf-8 string
    doc = cleanup_document(doc, config)
    xml_str = str(doc)

    # do some cleanup on the string itself
    if config.lstrip_lines:
        xml_str = trim_whitespace_at_start_of_each_line(xml_str)

    # write the new file
    with open(output_path, "w") as output_file:
        output_file.write(xml_str)


def build_config(args) -> Config:
    config = Config()
    if not args.keep_intervals:
        config.remove_tags.append({"tag": "TIMEX3INTERVAL"})
    if not args.keep_temponyms:
        config.remove_tags.append({"tag": "TIMEX3", "attrs": {"type": "TEMPONYM"}})
    for attr in args.keep_attr:
        if attr in config.strip_attrs:
            config.strip_attrs.remove(attr)
    config.lstrip_lines = not args.no_lstrip_lines
    config.add_fake_dct = not args.no_fake_dct
    return config


def main(args):
    config = build_config(args)

    os.makedirs(args.output_dir, exist_ok=True)
    for path in glob.glob(args.input_path):
        new_path = os.path.join(args.output_dir, os.path.basename(path))
        new_path = new_path.replace("_DONE", "")
        handle_cleanup(path, new_path, config)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Prepare a directory of files for evaluation by the tempeval scripts.")
    parser.add_argument("input_path", type=str, help="A glob expression used for searching input files, e.g.: '../data/*.xml'")
    parser.add_argument("output_dir", type=str, help="A directory to put the prepared files into. Will be created if needed.")
    parser.add_argument("--keep-attr", type=str, action="append", default=[], help="Keep timex3 attributes, that would otherwise be removed. Can be given multiple times.")
    parser.add_argument("--keep-intervals", action="store_true", help="If present, TIMEX3INTERVAL tags are not removed")
    parser.add_argument("--keep-temponyms", action="store_true", help="If present, TIMEX3 with TEMPONYM are not removed")
    parser.add_argument("--no-lstrip-lines", action="store_true", help="If present, do not clean whitespace starting each line.")
    parser.add_argument("--no-fake-dct", action="store_true", help="If present, do not add a fake DCT tag.")

    main(parser.parse_args())
