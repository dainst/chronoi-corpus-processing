#!/bin/bash

# the file to prepare for tagging
file_to_prepare="$1"

# the directory where this file is
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# add header information including the stylesheet and type definition
cat <<- EOF
<?xml version="1.0"?>
<!DOCTYPE TimeML SYSTEM "${DIR}/chronoi.dtd">
<?xml-stylesheet type="text/css" href="${DIR}/chronoi.css"?>
<TimeML>
EOF

# wrap each line into sentence tags so
awk '{ printf("<sentence no=\"%d\">%s</sentence>\n", NR, $0) }' "$file_to_prepare"

# close the document
echo "</TimeML>"
