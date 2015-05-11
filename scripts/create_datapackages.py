#/usr/bin/env python2

# author: Thomas Mayer
# email: thomas.mayer@uni-marburg.de
# created: 2013-10-01

import re
import collections
import numpy as np
from scipy.sparse import coo_matrix
from scipy.io import mmwrite
import zipfile
import datetime
import sys, os
import io
import time
import traceback
from datapackage_settings import *


def datapackage(text, verseid_by_versename):
    """
    This method generates the datapackage for a given Bible text.
    """

    name = text[:-4]
    # get metadata info
    with open(BIBLEPATH + text) as file_handle:
        lines = file_handle.readlines()

    info = [l.strip() for l in lines if re.search("^# .+?: .", l)]
    infodict = {i[2:].split(':', 1)[0]:i.split(':', 1)[1].strip() for i in info}
    infodict = collections.defaultdict(str, infodict)

    # open text file
    verses = [l.strip().split('\t') for l in lines if l[0].strip() != "#"]

    zip_file = zipfile.ZipFile(DATAPACKAGEPATH + name + ".zip", 'w', zipfile.ZIP_DEFLATED)

    # get project description from file
    with open(PROJDESCFILE) as file_handle:
        infodict['project_description'] = re.sub('\n+', ' <br> ', file_handle.read())

    #collect info for datapackage.json and README.json
    format_spec = (infodict['title'],
                   name,
                   infodict['language_name'],
                   infodict['closest ISO 639-3'],
                   infodict['year_short'],
                   infodict['URL'],
                   infodict['copyright_short'],
                   infodict['copyright_long'],
                   'http://paralleltext.info/data/' + name,
                   name.split('-')[-1][1:],
                   datetime.datetime.now().strftime("%Y-%m-%d"),
                   name + '.txt',
                   name + '.wordforms',
                   os.path.basename(VERSENAMES),
                   name + '.mtx',
                   'datapackage.json',
                   'README.md',
                   infodict['project_description'])

    wordlist, matrix = wordlistmatrix(verses, verseid_by_versename)

    # create datapackage.json file
    with open(PACKAGESTRINGFILE) as file_handle:
        zip_file.writestr('datapackage.json', file_handle.read().format(*format_spec))

    # create README.md file
    with open(READMESTRINGFILE) as file_handle:
        zip_file.writestr('README.md', file_handle.read().format(*format_spec))

    # include matrix file
    zip_file.writestr(name + '.mtx', matrix)

    # include wordforms file
    zip_file.writestr(name + '.wordforms', wordlist)

    # include versename file
    zip_file.write(VERSENAMES, os.path.basename(VERSENAMES))

    # include Mark text file
    markverses = ["\t".join(v) for v in verses if v[0].lstrip()[:2] == "41"]
    markstring = "\n".join(info+markverses)
    zip_file.writestr(text, markstring)

    zip_file.close()


def wordlistmatrix(verses, verseid_by_versename):
    """
    This method generates the word list and matrix files for a given Bible text.
    """

    wordscount = collections.defaultdict(int)
    wordssentences = collections.defaultdict(list)

    # go through all verses
    for verse in verses:
        if len(verse) != 2:
            continue

        words = verse[1].split()
        verse_name = verse[0].strip()
        for word in words:
            wordscount[word] += 1
        for word in set(words):
            wordssentences[word].append(verse_name)

    # create the wordforms
    wordforms = sorted(wordscount)
    wordlist = ''.join("{}\t{}\n".format(wf, wordscount[wf]) for wf in wordforms)

    # construct the matrix
    rows = len(wordforms)
    cols = len(verseid_by_versename)
    print '\t', rows, cols

    def row_iter():
        """ Iterator function to create row data of the matrix"""
        for index, wordform in enumerate(wordforms):
            for _ in wordssentences[wordform]:
                yield index

    def column_iter():
        """ Iterator function to create column data of the matrix"""
        for wordform in wordforms:
            for occ in wordssentences[wordform]:
                yield verseid_by_versename[occ]

    row_data = np.fromiter(row_iter(), 'int32')
    col_data = np.fromiter(column_iter(), 'int32')
    data = np.ones(len(col_data), dtype='int8')

    sparse = coo_matrix((data, (row_data, col_data)), dtype='int8', shape=(rows, cols))

    # create the matrix file
    matrix_buffer = io.BytesIO()
    mmwrite(matrix_buffer, sparse, field="pattern")

    return wordlist, matrix_buffer.getvalue()


def main(args=None):
    """Entry point for this script."""
    if args is None:
        args = sys.argv[1:]
    # prepare the versenames
    with open(VERSENAMES) as file_handle:
        ohverse = file_handle.readlines()
    verseid_by_versename = {verse.strip():count for count, verse in enumerate(ohverse)}

    biblefiles = [f for f in os.listdir(BIBLEPATH) if f[-4:] == '.txt' and 'deprecated' not in f]
    if args:
        biblefiles = [f for f in biblefiles if f in args]
    failed = []
    for index, file_name in enumerate(biblefiles):
        print index, file_name
        try:
            start = time.time()
            datapackage(file_name, verseid_by_versename)
            print '\tduration:', time.time()-start
        except Exception:
            failed.append((file_name, traceback.format_exc()))
            traceback.print_exc()
    if failed:
        with open('failed', 'w') as file_handle:
            for name, exc in failed:
                file_handle.write('%s\n%s\n\n' % (name, exc))


if __name__ == "__main__":
    if '-p' in sys.argv:
        sys.argv.remove('-p')
        import cProfile
        cProfile.run('main()')
    else:
        main()
