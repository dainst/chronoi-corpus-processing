#!/bin/bash

gold_dir="$1"
eval_file="$2"
num_bins="$3"
output_dir="$4"
additional_sql_conditions="$5"

query_single_column_values() {
    # Query all values in the column where sql-conditions are met
    # sorts the output and removes duplicates
    local column="$1"
    local conditions="$2"
    local csv_file="$3"
    local table=$(basename -s ".csv" "$csv_file")

    if [ -n "$additional_sql_conditions" ]; then
        conditions="${conditions} and ${additional_sql_conditions}"
    fi

    local query="select ${column} from ${table} where ${conditions}"
    csvsql --query "$query" "$eval_file" | tail -n +2 | sort -n | uniq
}

histogram_table() {
    # Build a histogram of the text occurences by
    # awk    - finding the relative text positions and sorting them into $num_bins bins
    # uniq   - producing a histogram table
    # awk    - switching the table columns
    local text_positions="$1"
    local char_count=$2
    echo "$text_positions" \
         | awk '{print int('$num_bins'*($1/'$char_count'))}' \
         | uniq -c \
         | awk '{print $2"\t"$1}'
}

plot_histogram() {
    # plot histogram data of the form
    #       1           23
    #       2           64
    #       ...
    #       $num_bins   n
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

mkdir -p "$output_dir"

num_texts=0
all_histograms=""
for f in $(find "$gold_dir" -type f | sort -n)
do
    num_texts=$(($num_texts + 1))

    # get the total text count without xml annotations
    py_count="import bs4; import sys; doc = bs4.BeautifulSoup(open(sys.argv[1]), 'xml'); print(len(doc.text))"
    char_count=$(python3 -c "$py_count" "$f")
    
    # query the evaluation file for text positions and create a histogram
    base_name=$(basename -s ".xml" "$f")
    occurences=$(query_single_column_values "tag1_text_pos_start" "tag1_basename ='${base_name}' and tag1_is_gold" "$eval_file")
    histogram=$(histogram_table "$occurences" "$char_count")

    # make a graphical plot from the histogram
    plot_histogram "$histogram" "$base_name" > "${output_dir}/${base_name}_distribution.png"

    # append the number of occurences into a third column of the histogram table
    hist_with_occ_count=$(paste <(echo "$histogram") <(echo "$occurences" | wc -l))

    # append to the total number of histograms
    all_histograms="${all_histograms}\n${hist_with_occ_count}"
done

# replace newline symbols by real newlines and do not leave a blank at the start
all_histograms=$(echo -e "$all_histograms" | tail -n +2)

# combine all histograms into one
hist_sums=$(echo "$all_histograms" \
                     | awk '{ if ($2 > 0) counts[$1] += $2 } END { for (idx in counts) print idx"\t"counts[idx] }' )
plot_histogram "$hist_sums" "all, ${additional_sql_conditions}" > "${output_dir}/00_all_texts_distribution.png"

# weigh by count of occurences in each text
hist_sums=$(echo "$all_histograms" \
    | awk '{ if ($3 > 0) n=$3; printf("%d\t%.4f\n", $1, ($2 / n))} ' \
    | awk '{ if ($2 > 0) counts[$1] += $2 } END { for (idx in counts) printf("%d\t%.4f\n", idx, (counts[idx] / '$num_texts')) }' )
plot_histogram "$hist_sums" "all (means, ${additional_sql_conditions})" > "${output_dir}/00_all_texts_distribution_weighed.png"
