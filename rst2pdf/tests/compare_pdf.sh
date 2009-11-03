#!/bin/bash

# Given two PDF files in the command line, create a visual diff of them in another PDF

f1=$1
f2=$2

tmpdir=/tmp/comppdf-$$
mkdir $tmpdir
convert $f1 $tmpdir/page.png
convert $f2 $tmpdir/bpage.png
pushd $tmpdir

for page in page*.png
do
    result=`compare -metric PSNR $page b$page diff$page 2>&1`
    if [ "$result" = "inf" ]
    then
            #echo "$page is OK"
            true
    else
            echo "$page has ERRORs, see $tmpdir/diff$page"
    fi    
done
popd

convert $tmpdir/diff*png diff-$$.pdf
