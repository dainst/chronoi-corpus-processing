#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bs4
import os
import glob


def recursively_clean_element(elem: bs4.Tag):
    # text nodes are ignored
    if type(elem) == bs4.NavigableString:
        return

    if elem.name == "temponym-fn":
        # temponym false negatives are just replaced with the text they contain
        replace_element_with_its_text(elem)
    elif elem.name == "TIMEX3":
        # normal timexes get the attributes removed that were added in annotation
        elem.attrs.pop("check", None)
        elem.attrs.pop("literature-time", None)
        elem.attrs.pop("exploration-time", None)
        # treat timex temponyms like temponym false negatives
        if elem.attrs.get("type", "") == "TEMPONYM":
            replace_element_with_its_text(elem)
    else:
        # recurse if we hit any other element (like a TIMEX3INTERVAL)
        for child_elem in elem.children:
            recursively_clean_element(child_elem)


def replace_element_with_its_text(elem: bs4.Tag):
    elem.replace_with(elem.string)


if __name__ == "__main__":
    # input and output dirs
    dir_output = os.environ["OUTPUT_DIR"]
    dir_annotated = os.path.join(dir_output, "A02_manual_correction", "en")
    dir_timex3 = os.path.join(dir_output, "A03_pilot_standard", "en")

    files = glob.glob(os.path.join(dir_annotated, "**_DONE.xml"))
    for file_path in files:
        # read the original
        with open(file_path, "r") as file:
            doc = bs4.BeautifulSoup(file, "lxml-xml")

        # remove additional information
        root = doc.findChild("TimeML")
        for child in root.children:
            if type(child) == bs4.element.Tag:
                recursively_clean_element(child)

        # write the new file
        new_path = os.path.join(dir_timex3, os.path.basename(file_path))
        new_path = new_path.replace("_DONE", "")
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        with open(new_path, "w") as new_file:
            new_file.write(str(doc))

            # Write two empty lines (easier checking if lengths are okay)
            # Not strictly necessary. Remove this if you like.
            new_file.write("\n\n")
