#!/bin/bash

dir="$(dirname $0)"

zenon_scrape_file="$1"

patterns="
arachne.uni-koeln.de/books
journals.ub.uni-heidelberg.de/index.php/[^/]*/article/download
bmcr.brynmawr.edu/[0-9]{4}/[0-9]
loc.gov/catdir/sample
doi.org/10.1111/
doi.org/10.1017/
e-periodica.ch/cntmng
digi.ub.uni-heidelberg.de/diglit/
publications.dainst.org/journals/index.php/efb/article/download
"

echo "id,url,pubdate,languages"
for pattern in $patterns; do
  $dir/analyse_zenon_scrape.py --desc-filters $dir/../resources/zenon-useless-urls.txt "$zenon_scrape_file" \
      --select-by-url "$pattern" \
      --print-id --print-url --print-pub-date --print-languages
done
