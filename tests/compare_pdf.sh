#!/bin/bash
#
# Given two PDF files in the command line, create a visual diff of them in
# another PDF
set -x
if [ -z "$1" ] ; then
  echo "Usage: $(basename "$0") <file1.pdf> <file2.pdf> [temp_directory='/tmp/comppdf-"'$$'"']"
  exit 1
fi

f1=$1
f2=$2
flag=0

tmpdir="${3:-/tmp/comppdf-$$}"

mkdir -p "$tmpdir"
rm -f "$tmpdir"/*

convert -density 96x96 "$f1" "png24:$tmpdir/page.png"
convert -density 96x96 "$f2" "png24:$tmpdir/bpage.png"

pushd "$tmpdir" >/dev/null 2>&1

for page in page*.png; do
    result=$(compare -metric PSNR "$page" b"$page" "diff$page" 2>&1)
    if [ "$result" = "inf" ]; then
        true
    else
        echo "$page has ERRORs, see $tmpdir/diff$page"
        flag=1
    fi
done

popd >/dev/null 2>&1

exit $flag
