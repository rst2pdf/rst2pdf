#!/bin/sh
for t in *.txt
do
    st=`basename $t .txt`.style
	if [ -f "$st" ]
    then
        python ../../createpdf.py $t -s $st 2> $t.err || echo ERROR processing $t
    else
        python ../../createpdf.py $t 2> $t.err || echo ERROR processing $t
    fi
done
