#!/bin/bash

# Given two PDF files in the command line, create a visual diff of them in another PDF

function compare_pdfs {
  f1=$PWD/$1
  f2=$PWD/$2
  flag=0

  tmpdir=/tmp/comppdf-$$/$1
  mkdir -p $tmpdir
  convert -density 96x96 $f1 $tmpdir/page.png
  convert -density 96x96 $f2 $tmpdir/bpage.png

  pages=$(find $tmpdir -name page*.png | wc -l)
  bpages=$(find $tmpdir -name bpage*.png | wc -l)
  if [[ $pages != $bpages ]]; then
    echo Page count mismatch \($pages != $bpages\)
  else
    pushd $tmpdir >/dev/null 2>&1
    for page in page*.png
    do
        result=`compare -metric PSNR $page b$page diff$page 2>&1`
        if [ "$result" = "inf" ]
        then
          echo "$page is OK"
        else
          echo "$page has ERRORs, see $tmpdir/diff$page"
          display $tmpdir/diff$page
    	    flag=1
        fi
    done
    popd >/dev/null 2>&1
    if [[ $flag == 1 ]]; then
      read -p "Replace expected output? " replace;
      if [[ $replace == "y" ]]; then
        cp -fv $f1 $f2;
      elif [[ $replace == "q" ]]; then
        exit 1;
      fi
    fi
  fi
}

for fname in $(find expected_output -iname *.pdf -printf "%f\n"); do
  if [[ -e output/$fname ]]; then
    compare_pdfs output/$fname expected_output/$fname
  else
    echo "Skipping $fname"
  fi
done
