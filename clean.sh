#!/usr/bin/sh

# remove everything except *.pdf from ./data
for f in $(ls ./data/*); do
    is_pdf_ext=$(echo $f | grep -Pc ".*\.pdf$")
    if [ $is_pdf_ext -eq 0 ]; then
        echo "rm $f"
        rm $f
    fi
done
