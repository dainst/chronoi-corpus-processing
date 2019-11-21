#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import random
import sys
import yaml

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Process a file with zenon json records and select texts for annotation.")
    parser.add_argument("scrape_file", type=str, help="The file that contains the zenon dumps as json.")
    parser.add_argument("-s", "--sample_size", type=int, default=1, help="Number of records to randomly select.")
    args = parser.parse_args()

    with open(args.scrape_file, "r") as file:
        records = json.load(file)

    records_with_urls = list(filter(lambda r: len(r.get("urls")) > 0, records))

    outputs = []
    for record in random.sample(records_with_urls, args.sample_size):
        output = {}
        output["id"] = record.get("id")
        output["primary_autor"] = record.get("authors", {}).get("primary", {})
        output["title"] = record.get("title", "")
        output["publicationDates"] = record.get("publicationDates", [])
        output["thesaurus"] = record.get("thesaurus")
        output["urls"] = list(map(lambda url: f"{url['url']} ({url.get('desc', '')})", record.get("urls")))
        outputs.append(output)

    yaml.dump(outputs, sys.stdout, encoding="utf-8", default_flow_style=False)


    # json.dump(with_urls, sys.stdout, indent=4)

    # choose some texts at random and display their urls

