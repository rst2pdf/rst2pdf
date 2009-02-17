#!/bin/sh
for t in *.txt
do
    st=`basename $t .txt`.style
	if [ -f "$st" ]
    then
        python ../../createpdf.py $t -s $st 2> $t.err
    else
        python ../../createpdf.py $t 2> $t.err
    fi
	if [ $? ]
    then
		echo ERROR processing $t
    fi
done
