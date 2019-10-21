#!/bin/bash

gold_dir="$1"
eval_file="$2"
num_bins="$3"
output_dir="$4"

query_histogram() {
    # Build a histogram of the relative occurences in the text by
    # csvsql - querying the evaluation file for text position
    # tail   - omitting the column name
    # awk    - finding the relative text positions and sorting them into $num_bins bins
    # uniq   - producing a histogram table
    # awk    - switching the table columns
    local query="$1"
    local char_count=$2
    csvsql --query "$sql" "$eval_file" \
         | tail -n +2 \
         | awk '{print int('$num_bins'*($1/'$char_count'))}' \
         | uniq -c \
         | awk '{print $2"\t"$1}'
}

plot_histogram() {
    # plot histogram data of the form
    #       1           23
    #       2           64
    #       ...
    #       $num_bins   (count)
    # by drawing  a graph with plotutils. (First line of the graph options is x- and y- dimenstions,
    # second is display options, the following are axes and graph descriptions)
    local data=$1
    local plot_name=$2
    echo "$data" | graph -x 0 $(($num_bins - 1)) 1 -y 0 \
            -C -m 1 -S 4 0.05 -T png \
            -X "Relative position in text (${num_bins} regions)." \
            -Y "Occurences" \
            -L "$plot_name"
}

all_histograms=""
for f in $(find "$gold_dir" -type f | sort -n)
do
    # get the total text count without xml annotations
    py_count="import bs4; import sys; doc = bs4.BeautifulSoup(open(sys.argv[1]), 'xml'); print(len(doc.text))"
    char_count=$(python3 -c "$py_count" "$f")
    
    # query the evaluation file for text positions and create a histogram
    base_name=$(basename -s ".xml" "$f")
    sql="select distinct(tag1_text_pos_start) from eval where tag1_basename ='${base_name}' and tag1_is_gold"
    histogram=$(query_histogram "$sql" "$char_count")
    
    # make a graphical plot from the histogram
    plot_histogram "$histogram" "$base_name" > "${output_dir}/${base_name}_distribution.png"

    # append to the total number of histograms
    all_histograms="${all_histograms}\n${histogram}"
done

# combine all histograms into one
combined_histogram=$(echo -e "$all_histograms" \
                     | awk '{ if ($2 > 0) counts[$1] += $2 } END { for (idx in counts) print idx"\t"counts[idx] }' )
plot_histogram "$combined_histogram" "all" > "${output_dir}/00_all_texts_distribution.png"
