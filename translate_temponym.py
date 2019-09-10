#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import furl
import json
import Levenshtein
import requests


class IdaiVocab(object):

    @classmethod
    def _evaluate_response(cls, response: requests.Response):
        result = {}
        if response.status_code != 200:
            print(f"WARN: Bad response, got {response.status_code} on {response.url}")
        elif not response.text:
            print(f"WARN: Empty response on {response.url}")
        else:
            # Weirdly, we sometimes get a bad response from vocab
            # where the text does not directly starts with json
            # this might be an encoding issue.
            json_begin = response.text.find("{")
            if json_begin < 0:
                print(f"WARN: Response is not json, from {response.url}")
            else:
                body = json.loads(response.text[json_begin:])
                if "result" in body:
                    result = body["result"]
        return result

    @classmethod
    def _request(cls, lang: str, task: str, arg: any):
        url = f"https://archwort.dainst.org/{lang}/vocab/services.php"
        params = {"task": task, "arg": arg, "output": "json"}
        return cls._evaluate_response(requests.get(url, params))

    @classmethod
    def fetch_similar(cls, lang: str, term: str):
        """
        Query idai.vocab for a matching term in the given language.
        :return: A string. The next best term as suggested by the API.
        """
        response = cls._request(lang, "fetchSimilar", term)
        if "string" in response:
            return response["string"]
        else:
            print(f"WARN: Bad response when retrieving similar for'{term}'")
            return ""

    @classmethod
    def fetch_matching(cls, lang: str, term: str):
        """
        Ask idai.vocab fo details on a term.
        :return: A list of pairs: [(term_id, term), ...]
        """
        response = cls._request(lang, "suggestDetails", term)
        return [(int(term_id), term["string"]) for term_id, term in response.items()]

    @classmethod
    def fetch_translations(cls, lang: str, source_term_id: int):
        """
        Ask idai.vocab for "target terms", (i.e. translations) for the term
        with the given id.
        :return: A list of 3-tuples: [(term_id, language, term) ...]
        """
        response = cls._request(lang, "fetchTargetTerms", source_term_id)
        result = []
        for _, term in response.items():
            term_id = cls._get_id_from_term_uri(term["uri"])
            item = (term_id, term["target_vocabulary_tag"], term["string"])
            result.append(item)
        return result

    @staticmethod
    def _get_id_from_term_uri(uri: str) -> int:
        # Hacky, but I really don't want to do another request here, so just
        # parse the id from the provided uri and raise an error if there is none
        return int(furl.furl(uri).args["arg"])

    @classmethod
    def recursively_fetch_translations(cls, lang: str, start_id: int, max_depth=3, accu=None, depth=0):
        if accu is None:
            accu = []
        if max_depth < 0 or depth < max_depth:
            results = cls.fetch_translations(lang, start_id)
            for result in results:
                term_id, new_lang, _ = result
                if result not in accu:
                    accu.append(result)
                    cls.recursively_fetch_translations(new_lang, term_id, max_depth, accu, depth + 1)
        return accu


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Translate an input temponym by calling some APIs.")
    parser.add_argument("temponym", type=str, help="The temponym to translate")
    parser.add_argument("-s", "--source-language", type=str, default="en",
                        help="The source language used for input as a two letter code.")
    parser.add_argument("-l", "--max-levenshtein", type=int, default=4,
                        help="Maximum levenshtein distance to consider when querying for similar terms.")
    args = parser.parse_args()

    # Try to lookup a similar term in case the spelling is slightly off
    # we do a levenshtein comparison to not include results, that are
    # far from the mark.
    input_term = args.temponym
    actual_term = IdaiVocab.fetch_similar(args.source_language, input_term)
    distance = Levenshtein.distance(input_term, actual_term)
    if distance > args.max_levenshtein:
        print(f"No similar term found for '{input_term}'. Best was: '{actual_term}'")
        exit(1)

    # Now that we have a term that is guaranteed to be in the database
    # at least once, query for that and get some ids of matching terms.
    details = IdaiVocab.fetch_matching(args.source_language, actual_term)

    # for each of the details, retrieve all translations
    translations = set()
    for id, _ in details:
        found = IdaiVocab.recursively_fetch_translations(args.source_language, id)
        for (_, lang_code, term) in found:
            translations.add((lang_code, term))

    # Get all the translations that are in the source language, put them in
    # front, prepend the input, then output the complete list
    source_ts = [t for t in translations if t[0] == args.source_language]
    for t in source_ts:
        translations.remove(t)
    output = [(args.source_language, input_term)] + source_ts + sorted(list(translations))
    print(output)
