#!/bin/bash

# Processes a csv file produced by the evaluation script (evaluat_line_by_line.py)
# and displays information on the text areas that produced negative results
eval_csv="$1"

build_query() {
    local fieldnames="$1"
    local conditions="$2"
    echo "select ${fieldnames} from eval where ${conditions} order by tag1_basename"
}

do_query() {
    local query="$1"
    local input_file="$2"
    csvsql --query "$query" "$input_file" \
        | csvformat --quoting 1 --out-quotechar '"' --out-delimiter "|" \
        | tablign \
        | tr -d '"'
}

# we generally select from the first tag (normally the gold version unless for false positives)
common_taglist="tag1_basename, tag1_before_text, tag1_text, tag1_after_text, tag1_is_gold"

echo "FALSE NORMALIZED"
echo "~~~~~~~~~~~~~~~~"
taglist="${common_taglist}, tag1_attr_value, tag2_attr_value"
conditions="task_type = 'ATTRIBUTE' and attr_name = 'value' and result_type = 'FN' and tag1_attr_value != tag2_attr_value"
do_query "$(build_query "$taglist" "$conditions")" "$eval_csv"


echo ""
echo ""
echo "FALSE_POSITIVES"
echo "~~~~~~~~~~~~~~~"
taglist="${common_taglist}"
conditions="task_type = 'TAG_RELAXED' and result_type = 'FP'"
do_query "$(build_query "$taglist" "$conditions")" "$eval_csv"


echo ""
echo ""
echo "FALSE_NEGATIVES"
echo "~~~~~~~~~~~~~~~"
taglist="${common_taglist}"
conditions="task_type = 'TAG_RELAXED' and result_type = 'FN'"
do_query "$(build_query "$taglist" "$conditions")" "$eval_csv"
