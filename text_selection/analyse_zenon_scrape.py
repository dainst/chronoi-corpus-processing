#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import furl
import json
import re
import sys

from collections import defaultdict


def filter_records_without_url(records: []) -> []:
    return [r for r in records if any(r.get("urls"))]


def build_furl(url: str) -> furl.furl:
    try:
        furl_obj = furl.furl(url)
        if not furl_obj.host:
            furl_obj = furl.furl("http://" + url)
        return furl_obj
    except ValueError:
        return furl.furl("https://invalid-url.xyz")


def determine_host(url: str) -> str:
    furl_obj = build_furl(url)
    return re.sub(r"^www[0-9]*\.", "", furl_obj.host)


def build_hosts_to_urls(records: []) -> {str: {str}}:
    result = defaultdict(set)
    for record in records:
        for url in record.get("urls"):
            host = determine_host(url.get("url"))
            result[host].add(url.get("url"))
    return result


def print_most_common_url_hosts(hosts_to_urls: {}, n: int):
    hosts = [h for h in hosts_to_urls.keys() if len(hosts_to_urls[h]) > n]
    hosts = sorted(hosts, key=lambda h: len(hosts_to_urls[h]))
    for host in hosts:
        print("% 6d\t%s" % (len(hosts_to_urls[host]), host))


def print_urls_for_host(hosts_to_urls: {}, host: str):
    urls = hosts_to_urls.get(host, [])
    for url in urls:
        print(url)
    if not any(urls):
        print(f"No urls for host: '{host}'", file=sys.stderr)


def print_how_often_url_patterns_cooccur(records: [{}], pattern1: str, pattern2: str):
    # It should be ok, to only pattern match the hosts here...
    ids1 = {r.get("id") for r in records if record_has_matching_url(r, pattern1)}
    ids2 = {r.get("id") for r in records if record_has_matching_url(r, pattern2)}
    ids_both = ids1.intersection(ids2)
    for host, number in {pattern1: len(ids1), pattern2: len(ids2), "both": len(ids_both)}.items():
        print(f"{host}: {number}")


def record_has_matching_url(record: {}, pattern: str) -> bool:
    return any(record_get_urls_matching(record, pattern))


def record_get_urls_matching(record: {}, pattern: str) -> [{}]:
    result = []
    for url in record.get("urls"):
        if any(re.findall(pattern, url.get("url"))):
            result.append(url)
    return result


def record_remove_urls_not_matching(record: {}, pattern: str):
    record["urls"] = record_get_urls_matching(record, pattern)


def earliest_year(year_strings: [str]) -> str:
    years = []
    for year_s in year_strings:
        try:
            years.append(int(year_s))
        except ValueError:
            print(f"Not a string that is a year: '{year_s}'", file=sys.stderr)
            continue
    return str(sorted(years)[0]) if any(years) else ""


def main(args: argparse.Namespace):
    with open(args.scrape_file, "r") as file:
        records = json.load(file)

    records = filter_records_without_url(records)

    # filter urls by the user-provided filter list
    if args.desc_filters:
        with open(args.desc_filters, "r") as file:
            filters = file.read().splitlines()
        for record in records:
            record["urls"] = [url for url in record.get("urls") if url.get("desc") not in filters]
        records = filter_records_without_url(records)

    # print unique hosts or urls, then exit
    if args.print_host_urls or args.print_common_hosts >= 0:
        hosts_to_urls = build_hosts_to_urls(records)
        if args.print_common_hosts >= 0:
            print_most_common_url_hosts(hosts_to_urls, n=args.print_common_hosts)
        elif args.print_host_urls:
            print_urls_for_host(hosts_to_urls, host=args.print_host_urls)
        exit(0)

    # check in how many records the two given hosts co-occur, then exit
    if args.patterns_cooccur:
        host1, host2 = args.patterns_cooccur.split(",")
        print_how_often_url_patterns_cooccur(records, host1, host2)
        exit(0)

    # do some selection based on a url pattern, remove all non-matching urls from the record
    if args.select_by_url:
        pattern = args.select_by_url
        records = [r for r in records if record_has_matching_url(r, pattern)]
        for record in records:
            record_remove_urls_not_matching(record, pattern)

    # sort the records by id, to be extra sure, that we get the same order every time this is called
    # print each line as a csv column
    records = sorted(records, key=lambda r: r.get("id"))
    writer = csv.writer(sys.stdout, delimiter=",", quoting=csv.QUOTE_ALL)
    for record in records:
        to_print = []
        if args.print_id:
            to_print.append(record.get("id", ""))
        if args.print_url:
            to_print.append(record.get("urls")[0].get("url") if any(record.get("urls")) else "")
        if args.print_pub_date:
            to_print.append(earliest_year(record.get("publicationDates", [])))
        if args.print_languages:
            to_print.append("|".join(record.get("languages", [])))
        writer.writerow(to_print)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Process a file with zenon json records and print some information about them.")
    parser.add_argument("scrape_file", type=str, help="The file that contains the zenon dumps as json.")
    parser.add_argument("--desc-filters", type=str, help="A file to filter urls by. Excludes urls with 'desc' fields matching a line in the file.")

    # these are arguments to print some specific information
    parser.add_argument("--print-common-hosts", type=int, default=-1, help="Print hosts that appear more than n times in the records urls, then exit.")
    parser.add_argument("--print-host-urls", type=str, help="Print all urls for the host, then exit.")
    parser.add_argument("--patterns-cooccur", type=str, help="Format: 'pattern1,pattern2', print how often these occur in single records url fields, then exit.")

    # these are meant to work together select by a url pattern then print information about the records
    parser.add_argument("--select-by-url", type=str, help="Give a pattern for a url to select records by.")
    parser.add_argument("--print-url", action="store_true", help="Print the first of each urls for the selected records. (Ignores other urls present on the records if --select-url is given.)")
    parser.add_argument("--print-pub-date", action="store_true", help="Print the earliest publication year for each of the selected records.")
    parser.add_argument("--print-id", action="store_true", help="Print the selected records' ids")
    parser.add_argument("--print-languages", action="store_true", help="Print the selected records' languages")

    main(parser.parse_args())
