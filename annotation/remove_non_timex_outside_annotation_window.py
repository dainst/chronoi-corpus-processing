#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import bs4
import sys

def remove_elems(elem: bs4.Tag):
    # Descend first so that changes are carried from bottom to the top
    for child in elem.children:
        if isinstance(child, bs4.Tag):
            remove_elems(child)

    parent_names = [e.name for e in elem.parents]

    if elem.name != "TIMEX3" \
            and ("sentence" in parent_names) \
            and ("annotation-window" not in parent_names):
        print("Removing elem:", elem, file=sys.stderr)
        elem.unwrap()


def main(file):
    doc = bs4.BeautifulSoup(file, "lxml-xml", from_encoding="utf-8")
    root = doc.find("TimeML")
    remove_elems(root)
    print(str(doc), file=sys.stdout)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Remove non-timex3 elements from any document that are not contained in the <annotation-window/> ")
    parser.add_argument("input", type=argparse.FileType(mode="r"), help="The file to read from.")
    args = parser.parse_args()
    main(args.input)
