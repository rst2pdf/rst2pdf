#!/usr/bin/env python

import glob
import shutil

from autotest import checkmd5

# First, let's check that the existing artifacts are "good"

artifacts = glob.glob('reference/*.pdf')

for artifact in artifacts:
    md5_path = artifact.replace('.pdf', '.json').replace('reference/', 'md5/')
    res, _ = checkmd5(artifact, md5_path, [], False)
    if res != 'good':
        print 'BAD ARTIFACT: %s ' % res, artifact

for new_artifact in glob.glob('output/*.pdf'):
    artifact = new_artifact.replace('output/', 'reference/')
    md5_path = artifact.replace('.pdf', '.json').replace('reference/', 'md5/')
    if artifact in artifacts:
        continue  # We already have an artifact for this test
    else:
        res, _ = checkmd5(new_artifact, md5_path, [], False)
        if res == 'good':
            print 'GOOD ARTIFACT: %s ' % res, new_artifact
            shutil.copy(new_artifact, artifact)
