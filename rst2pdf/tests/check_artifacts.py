#!/usr/bin/env python

"""Hacky script to validate testing artifacts.

* If there is a reference artifact that doesn't have a known-good checksum
  it will print 'BAD ARTIFACT'.

* If there is a testing artifact in output/ that has a known-good checksum
  for a test that has no known reference artifact:

  It will print 'GOOD ARTIFACT', and then copy that file into reference/
"""

import glob
import shutil

from autotest import checkmd5

# First, let's check that the existing artifacts are "good"

artifacts = glob.glob('reference/*.pdf')

for artifact in artifacts:
    md5_path = artifact.replace('.pdf', '.json').replace('reference/', 'md5/')
    res, _ = checkmd5(artifact, md5_path, [], False)
    if res != 'good':
        print('BAD ARTIFACT: %s ' % res, artifact)

# Check if any output file is good and has no matching artifact

for new_artifact in glob.glob('output/*.pdf'):
    artifact = new_artifact.replace('output/', 'reference/')
    if artifact in artifacts:
        continue  # We already have an artifact for this test
    else:
        md5_path = artifact.replace('.pdf', '.json').replace('reference/', 'md5/')
        res, _ = checkmd5(new_artifact, md5_path, [], False)
        if res == 'good':
            print('GOOD ARTIFACT: %s ' % res, new_artifact)
            shutil.copy(new_artifact, artifact)
