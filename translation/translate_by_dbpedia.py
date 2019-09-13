#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import SPARQLWrapper


def sparql_resource_query_str(resource_name: str):
    template = """
        PREFIX owl:  <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX :     <http://dbpedia.org/resource/> 
        
        SELECT ?label
        WHERE { 
            { ?subject rdfs:label ?label } .
            { ?subject rdfs:label "%s"@en }
        }
    """
    return template % escape_quotes(resource_name)


def escape_quotes(input: str):
    return input.replace('"', '\\"')


def main():

    parser = argparse.ArgumentParser(description="Translate an input string by looking up DBpedia entries with that name.")
    parser.add_argument("input", type=str, help="The temponym to translate")
    args = parser.parse_args()

    query = sparql_resource_query_str(args.input)

    sparql = SPARQLWrapper.SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(SPARQLWrapper.JSON)
    results = sparql.query().convert()

    tuples = set()

    if "results" in results and "bindings" in results["results"]:
        for result in results["results"]["bindings"]:
            label = result["label"]
            translation = label["value"]
            language = label["xml:lang"]
            tuples.add((language, translation))

    print(sorted(list(tuples)))


if __name__ == "__main__":
    main()
