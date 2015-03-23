# author: Thomas Mayer
# email: thomas.mayer@uni-marburg.de
# created: 2013-10-01

import re
import collections
from scipy.sparse import lil_matrix
from scipy.io import mmwrite
import zipfile
import datetime
import sys, os
import io
import time
import traceback
from datapackage_settings import *


verseidByVersename = None

def datapackage(text, wordlist, matrix):
    """
    This method generates the datapackage for a given Bible text.
    """

    name = text[:-4]
    fh = open(BIBLEPATH + text).readlines()

    # get metadata info
    info = [l.strip() for l in fh if re.match("^# .+: .+$",l)]
    infodict = {i[2:].split(':',1)[0]:i.split(':',1)[1].strip() for i in info}
    infodict = collections.defaultdict(str, infodict)

    # open text file
    verses = [l.strip().split('\t') for l in fh if l[0].strip() != "#"]

    zip_file = zipfile.ZipFile(DATAPACKAGEPATH + name
        + ".zip",'w',zipfile.ZIP_DEFLATED)

    # get project description from file
    projdesc = open(PROJDESCFILE).read()
    projdesc = re.sub('\n+',' <br> ',projdesc)
    infodict['project_description'] = projdesc

    # create datapackage.json file
    packagestring = open(PACKAGESTRINGFILE).read().format(
        infodict['title'],
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
        'versenames-v1.txt',
        name + '.mtx',
        'datapackage.json',
        'README.md',
        infodict['project_description'])
    zip_file.writestr('datapackage.json',packagestring)

    # create README.md file
    readmestring = open(READMESTRINGFILE).read().format(
        infodict['title'],
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
        'versenames-v1.txt',
        name + '.mtx',
        'datapackage.json',
        'README.md',
        infodict['project_description'])
    zip_file.writestr('README.md',readmestring)

    # include matrix file
    zip_file.writestr(name + '.mtx', matrix)

    # include wordforms file
    zip_file.writestr(name + '.wordforms', wordlist)

    # include versename file
    zip_file.write(VERSENAMES, os.path.basename(VERSENAMES))

    # include Mark text file
    markverses = ["\t".join(v) for v in verses if v[0].lstrip()[:2] == "41"]
    markstring = "\n".join(info+markverses)
    zip_file.writestr(text,markstring)

    zip_file.close()


def wordlistmatrix(text):
    """
    This method generates the word list and matrix files for a given Bible text.
    """
    global verseidByVersename

    fh = open(BIBLEPATH + text).readlines()
    verses = [line.split("\t",1) for line in fh
        if line.lstrip()[0] != "#"]

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
            wordssentences[word].append(verse_name)

    if verseidByVersename is None:
        # get the versenames
        with open(VERSENAMES) as f :
            ohverse = f.readlines()
        verseidByVersename = {verse.strip():count
            for count,verse in enumerate(ohverse)}

    # create the wordforms
    wordforms = sorted(wordscount)
    wordlist = ''.join("{}\t{}\n".format(wf, wordscount[wf]) for wf in wordforms)

    # construct the matrix
    rows = len(wordforms)
    cols = len(verseidByVersename)
    print(rows,cols)

    sparse = lil_matrix((rows,cols), dtype="int8")

    for i, wf in enumerate(wordforms):
        for occ in wordssentences[wf]:
            sparse[i, verseidByVersename[occ]] = 1

    # create the matrix file
    matrix_buffer = io.BytesIO()
    mmwrite(matrix_buffer, sparse, field="pattern")

    return wordlist, matrix_buffer.getvalue()


def main():
    global verseidByVersename
    # prepare the versenames
    with open(VERSENAMES) as f:
        ohverse = f.readlines()
    verseidByVersename = {verse.strip():count
        for count,verse in enumerate(ohverse)}

    biblefiles = [f for f in os.listdir(BIBLEPATH) if f[-4:] == '.txt' and 'deprecated' not in f]
    failed = []
    for c,b in enumerate(biblefiles):
        print(c, b)
        try:
            start = time.time()
            wordlist, matrix = wordlistmatrix(b)
            datapackage(b, wordlist, matrix)
            print 'duration', time.time()-start
        except Exception:
            failed.append((b, traceback.format_exc()))
            traceback.print_exc()
    if failed:
        with open('failed', 'w') as f:
            for name, exc in failed:
                f.write('%s\n%s\n\n' % (name, exc))


if __name__ == "__main__":
    if '-p' in sys.argv:
        import cProfile
        cProfile.run('main()')
    else:
        main()



