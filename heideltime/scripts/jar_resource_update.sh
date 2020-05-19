#!/bin/bash

# Update the resources for our languages in place instead of having to build
# the whole jar again.
cd /srv/app/heideltime/resources
jar uf ../target/de.unihd.dbs.heideltime.standalone.jar german english french italian spanish
