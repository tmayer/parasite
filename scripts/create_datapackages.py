# author: Thomas Mayer
# email: thomas.mayer@uni-marburg.de
# created: 2013-10-01
# last modified: 2013-11-11

import re
import collections
from scipy.sparse import lil_matrix
from scipy.io import mmwrite
import zipfile
import datetime
import os
from datapackage_settings import *


def datapackage(text):
    """
    This method generates the datapackage for a given Bible text.
    """

    name = text[:-4]
    fh = open(BIBLEPATH + text).readlines()

    # get metadata info
    info = [l.strip() for l in fh if re.match("^# .+: .+$",l)]
    infodict = {i[2:].split(':',1)[0]:i.split(':',1)[1].strip() for i in info}

    # open text file
    verses = [l.strip().split('\t') for l in fh if l[0].strip() != "#"]

    zip = zipfile.ZipFile(DATAPACKAGEPATH + name
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
    zip.writestr('datapackage.json',packagestring)

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
    zip.writestr('README.md',readmestring)

    # include matrix file
    zip.write(MATRIXPATH + name + '.mtx', name + '.mtx')

    # include wordforms file
    zip.write(WORDFORMSPATH + name + '.wordforms', name + '.wordforms')

    # include versename file
    zip.write(VERSENAMES, os.path.basename(VERSENAMES))

    # include Mark text file
    markverses = ["\t".join(v) for v in verses if v[0].strip()[:2] == "41"]
    markstring = "\n".join(info+markverses)
    zip.writestr(text,markstring)

    zip.close()



def wordlistmatrix(text):
    """
    This method generates the word list and matrix files for a given Bible text.
    """

    name = text[:-4]

    fh = open(BIBLEPATH + text).readlines()
    verses = [line.strip().split("\t",1) for line in fh
        if line.strip()[0] != "#"]

    wordscount = collections.defaultdict(int)
    wordssentences = collections.defaultdict(list)

    # go through all verses
    for verse in verses:
        if len(verse) != 2:
            continue

        words = verse[1].split()
        for word in words:
            wordscount[word] += 1
            wordssentences[word].append(verse[0])

    # get the versenames
    ohverse = open(VERSENAMES).readlines()
    verseidByVersename = {verse.strip():count
        for count,verse in enumerate(ohverse)}

    # create the wordforms file
    ohword = open(WORDFORMSPATH + name + '.wordforms','w')

    wordforms = sorted(wordscount)

    # construct the matrix
    rows = len(wordforms)
    cols = len(verseidByVersename)
    print(rows,cols)

    sparse = lil_matrix((rows,cols), dtype="int8")

    for i in range(0,len(wordforms)):
        ohword.write("{}\t{}\n".format(wordforms[i],wordscount[wordforms[i]]))
        for occ in wordssentences[wordforms[i]]:
            sparse[i,int(verseidByVersename[occ[:8]])] = 1

    ohword.close()

    # create the matrix file
    mmwrite(MATRIXPATH + name + '.mtx', sparse, field="pattern")


if __name__ == "__main__":

    biblefiles = [f for f in os.listdir(BIBLEPATH) if f[-4:] == '.txt']
    setc = 0
    for c,b in enumerate(biblefiles[setc:]):
        print(c+setc,b)

        wordlistmatrix(b)
        datapackage(b)


