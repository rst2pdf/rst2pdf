#!/bin/sh

run_test() {
    st=`basename $1 .txt`.style
	if [ -f "$st" ]
    then
        python ../../createpdf.py $1 -s $st 2> $1.err || echo ERROR processing $1
    else
        python ../../createpdf.py $1 2> $1.err || echo ERROR processing $1
    fi
}

if [ $# -eq 0 ]
then
	for t in *.txt
	do
		run_test $t
	done
else
	while [ ! -z $1 ]
	do
		run_test $1
		shift
	done

fi
