#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This program is designed to migrate checksums to new versions of software,
when it is known that all the checksum changes are irrelevant to the visual
aspects of the PDF.  An example of this is when the PDF version number is
incremented from 1.3 to 1.4 for no good reason :-)

Old Usage:

1) Clean the output directory -- rm -Rf output/*
2) Run autotest with the old version of the software, to populate
   the output directory with known good, known bad, etc. versions.
3) Run parselogs and save the results:
      ./parselogs.py > oldlog.txt
4) Make the change to the software which is known not to affect the
   output visually.
5) Run this script.  It should rerun autotest, updating checksums to
   the same as they were previously.
6) Re-clean the output directory -- rm -Rf output/*
7) Re-run autotest for all the files --same as in step 2, but with new
   software version.
8) Run parselogs and save the results:
      ./parselogs.py > newlog.txt
9) Check the logs to make sure no files moved to a different category:
      tkdiff oldlog.txt newlog.txt
10) Check in the fixed checksums

New Usage:

1) Clean the output directory -- rm -Rf output/*
2) Run this script. It runs all the tests.
   - if a test passes, Yay!
   - if a test fails, it compares the output against the reference PDF and
    if they are visually similar, adds this as a known good MD5
   - if the PDFs are not similar, the difference is stored as an image and
    information about it added to a log

'''

import os
import glob
import subprocess
import sys
import glob


def mark_test_good(testname):
    cmd = './autotest.py -u good %s' %  ('input/' + testname + ".txt")
    # print cmd

    try:
        devnull = open(os.devnull, 'w')
        result = subprocess.check_call(cmd.split(), stdout=devnull, stderr=devnull)
    except subprocess.CalledProcessError as e:
        print e.output

def compare_output_and_reference(testname):
    devnull = open(os.devnull, 'w')
    rfile = "reference/" + testname + ".pdf"
    ofile = "output/" + testname + ".pdf"
    diffimg = "output/" + testname + "-differences.jpg"

    # requires image magick, this command is for v6.9
    cmd = 'compare ' + rfile + ' ' + ofile + ' -compose src -fuzz 5% -metric PHASH ' + diffimg
    # print cmd

    # run the command and capture the output
    p = subprocess.Popen(cmd.split(), stderr=subprocess.PIPE)
    output = p.communicate()

    try:
        score = float(output[1])
        if score == 0:
            print testname + " PDFs are identical: update hash";
            mark_test_good(testname)
        else:
            print testname + " PDFs differ with score: " + str(score)
    except ValueError:
        # it wasn't a number, just print the output
        print testname + " comparison failed with error: " + output[1]

def checkalltests(testfiles = None):
    i=0

    # what should we test? Start with input/*.txt
    if testfiles is None:
        testfiles = [os.path.basename(x) for x in glob.glob(os.path.join("input", '*.txt'))]

    for filename in testfiles:
        testname = os.path.splitext(filename)[0]

        # run the test once, see what happens
        cmd = './autotest.py %s' %  ('input/' + testname + ".txt")
        # print cmd
        try:
            devnull = open(os.devnull, 'w')
            result = subprocess.check_call(cmd.split(), stdout=devnull, stderr=devnull)
            print "*** " + testname + " test passes"
        except subprocess.CalledProcessError as e:
            # something to react to
            if(e.returncode == 3):
                # The result was unknown. This is where it gets interesting
                differences = compare_output_and_reference(testname)
            else:
                print testname + " returned status " + str(e.returncode)

        i = i+1
    

if __name__ == '__main__':
    if len(sys.argv) > 1:  # we have a list of tests
        checkalltests(sys.argv[1:])
