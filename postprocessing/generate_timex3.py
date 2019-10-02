#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bs4
import os
import glob
import re


def tag_should_be_removed(elem: bs4.Tag) -> bool:
    if elem.name in ["temponym-fn", "TIMEX3INTERVAL"]:
        return True
    elif elem.name == "TIMEX3":
        return (elem.attrs.get("check", "") == "false-positive"
                or elem.attrs.get("type", "") == "TEMPONYM")
    else:
        print("WARN: Non-standard element: " + str(elem))


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
        elem.attrs["value"] = match[1] + "BC"
    # also correct a leading plus sign by just removing it
    match = re.compile(r"\+(.*)").match(elem.attrs.get("value"))
    if match:
        elem.attrs["value"] = match[1]


def recursively_cleanup_element(elem: bs4.Tag) -> None:
    if type(elem) == bs4.NavigableString:
        # text nodes are ignored
        return

    # Recurse to the child elements first so that changes in the
    # lower nodes are done first and do not cause trouble when
    # changing higher nodes later
    for child_elem in elem.children:
        recursively_cleanup_element(child_elem)

    # remove tags that should not be included in the output
    if tag_should_be_removed(elem):
        elem.unwrap()

    # handle attributes (should only be in TIMEX3s)
    correct_tid_attr_if_needed(elem)
    correct_value_attr_if_needed(elem)
    elem.attrs.pop("check", None)
    elem.attrs.pop("literature-time", None)
    elem.attrs.pop("exploration-time", None)


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


def cleanup_document(doc: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    # cleanup the main document tags
    timeml_root = doc.findChild("TimeML")
    for child in timeml_root.children:
        if type(child) == bs4.Tag:
            recursively_cleanup_element(child)

    # work on the header-like elements adding valid namespace info and removing
    # the doctype if there is one
    doctype_tag = doc.find(string=lambda tag: isinstance(tag, bs4.Doctype))
    if doctype_tag:
        doctype_tag.extract()
    # add_timeml_namespace_info(timeml_root)
    wrap_contents_in_new_tag(timeml_root, "TEXT")
    add_fake_dct_tag(timeml_root)

    return doc


def trim_whitespace_at_start_of_each_line(text: str):
    return "".join(map(str.lstrip, text.splitlines(keepends=True)))


def handle_cleanup(input_path, output_path):
    # read the original
    with open(input_path, "r") as input_file:
        doc = bs4.BeautifulSoup(input_file, "lxml-xml", from_encoding="utf-8")

    # do the cleanup and convert to a utf-8 string
    doc = cleanup_document(doc)
    xml_str = str(doc)

    # do some cleanup on the string itself
    xml_str = trim_whitespace_at_start_of_each_line(xml_str)

    # write the new file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as output_file:
        output_file.write(xml_str)


if __name__ == "__main__":
    # the output dir for the whole application (also has inputs for this)
    dir_output = os.environ["OUTPUT_DIR"]

    # handle the manually corrected files serving as the de-facto gold-standard
    dir_annotated = os.path.join(dir_output, "A02_manual_correction", "en")
    dir_timex3 = os.path.join(dir_output, "A03_test_evaluation", "bronze", "en")
    files = glob.glob(os.path.join(dir_annotated, "**_DONE.xml"))
    for file_path in files:
        new_path = os.path.join(dir_timex3, os.path.basename(file_path))
        new_path = new_path.replace("_DONE", "")
        handle_cleanup(file_path, new_path)

    # input and output dirs for the system annotation
    dir_annotated = os.path.join(dir_output, "A01_annotated", "en")
    dir_system = os.path.join(dir_output, "A03_test_evaluation", "system", "en")
    files = glob.glob(os.path.join(dir_annotated, "**.xml"))

    for file_path in files:
        # ignore that one file we never got around to correctly annotate
        if "09_Ber" in file_path:
            continue

        new_path = os.path.join(dir_system, os.path.basename(file_path))
        handle_cleanup(file_path, new_path)
