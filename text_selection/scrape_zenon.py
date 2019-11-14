#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import requests
import sys

_ZENON_URL="http://zenontest.dainst.org"

class ZenonSearch:

    def __init__(self, records_per_page = 20):
        self.url = f"{_ZENON_URL}/api/v1/search"
        self.params = {
            "type": "AllFields",
            "filter[]": [],
            "page": 0,
            "limit": records_per_page,
        }

    def add_language_filter(self, language):
        self.params["filter[]"].append('language:"%s"' % language)

    def add_url_present_filter(self):
        self.params["filter[]"].append('url:[* TO *]')

    def fetch(self):
        r = requests.get(self.url, self.params)
        print(f"Query: {r.url}", file=sys.stderr)
        if 199 < r.status_code < 300:
            return r.json()
        else:
            print(f"Bad request, got {r.status_code} on:" + r.url, file=sys.stderr)
            return {}

    def next(self):
        self.params["page"] += 1
        return self.fetch()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=f"Scrapes ${_ZENON_URL} for records with urls.")
    parser.add_argument("--language", type=str, help="The language to facet filter by, e.g.: 'Italian'")
    parser.add_argument("--out_file", type=str, help="The file to save the json results to.")
    args = parser.parse_args()

    search = ZenonSearch(records_per_page=100)

    search.add_url_present_filter()

    if args.language:
        search.add_language_filter(args.language)

    records = []
    result = search.fetch()

    while "records" in result.keys():
        records += result["records"]
        result = search.next()

    out_file = sys.stdout
    if args.out_file:
        out_file = open(args.out_file, "w")

    print("writing to:", out_file.name, file=sys.stderr)
    json.dump(records, out_file, indent=4)

    out_file.close()

