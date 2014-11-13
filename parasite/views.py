import sys
import os
import os.path
import codecs
import re
import collections
import json
import traceback

from werkzeug.routing import BaseConverter
from flask import Flask, render_template, url_for, redirect, request, g
from zipfile import ZipFile,ZIP_DEFLATED

import reader, cooccurrence


# Use the RegexConverter function as a converter method for mapped urls
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app = Flask(__name__,static_url_path='/static', static_folder = "static")
app.config.from_pyfile('config.py')
app.url_map.converters['regex'] = RegexConverter


# URL path for displaying all data
full = 'full/' # URL for full access

@app.route('/',defaults={'full': ''})
@app.route('/full/',defaults={'full': full})
def index(full):
    """
    URL: /
    Preprocesses all textfiles in the folder and gathers all information
    for the languages that are included in that folder so that all 
    translations will be shown on the world map.
    """

    # gather information for json file for map display with geo coords 
    # for all languages
    translations = sorted(list({'-'.join(f[:-4].split('-')[:-1]) for f in 
        os.listdir(app.config['TEXTFILES_FOLDER']) 
        if f[-4:] == ".txt"}))
    codesbytranslations = collections.defaultdict(list)
    for t in translations:
        codesbytranslations[t[:3]].append(t)
    fh = codecs.open(app.config['DATA_FOLDER'] + 
        'lang_coords_all.txt','r','utf-8').readlines()
    codebygeo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh[1:]}
    
    # create the list of language objects
    languages = list()
    for c in codesbytranslations:
        currdict = dict()
        # if ISO code is available in lang coords file
        if c in codebygeo:
            currinfo = codebygeo[c]
            currdict["latitude"] = currinfo[2]
            currdict["longitude"] = currinfo[1]
            currdict["name"] = currinfo[0]
        else:
            currdict["latitude"] = 88
            currdict["longitude"] = 160
            currdict["name"] = ""
        currdict["code"] = c
        currdict["texts"] = codesbytranslations[c]
        languages.append(currdict)
        
    outdict = {"languages": languages}
        
    # create json file
    oh = codecs.open(app.config['DATA_FOLDER'] + 'languages.json','w','utf-8')
    json.dump(outdict,oh)
    oh.close()
    
    return render_template('index.html', full=full,
                           nrtranslations=len(translations),nrlanguages=len(codesbytranslations))
    
@app.route('/all/',defaults={'full': ''})
@app.route('/full/all/',defaults={'full': full})
def listtranslations(full):
    """
    URL: /all/
    Gathers all translations from the textfile folder and gets the information
    about their genealogy to be shown in the tabular representation.
    """
    translations = sorted(list({'-'.join(f[:-4].split('-')[:-1]) for f in 
            os.listdir(app.config['TEXTFILES_FOLDER']) 
            if f[-4:] == ".txt"}))

    # get genealogy
    fh = codecs.open(app.config['DATA_FOLDER'] 
        + 'lang2fam.csv','r','utf-8').readlines()
    codebyinfo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh}

    # get language name
    fh2 = codecs.open(app.config['DATA_FOLDER'] 
        + 'lang_coords_all.txt','r','utf-8').readlines()
    codebygeo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh2[1:]}

    # combine everything for the tabular representation
    #translations2 = [(t,codebygeo[t[:3]][0],
    #    codebyinfo[t[:3]][1]) if t[:3] in codebygeo else (t,"","") for t in translations]
    translations2 = list()
    for t in translations:
        if t[:3] in codebygeo and t[:3] in codebyinfo and len(codebyinfo[t[:3]]) > 1:
            translations2.append((t,codebygeo[t[:3]][0],codebyinfo[t[:3]][1]))
        else:
            translations2.append((t,"",""))

    return render_template('list.html', full=full, translations=translations2)
    
@app.route('/search/',methods=['POST', 'GET'],defaults={'full': ''})
@app.route('/full/search/',methods=['POST', 'GET'],defaults={'full': full})
def search(full):
    """
    URL: /search/
    Provides either search form with all translations with GET or redirects
    to the respective GET search URL with POST
    """

    # for POST redirect to respective GET URL
    if request.method == "POST":
        if request.form['target'] == "None":
            return redirect('/' + app.config['BASE_URL'] + full + 'search/' 
                + request.form['source'] + '/'
                + request.form['query'] + '/')
        else:
            return redirect('/' + app.config['BASE_URL'] + full + 'search/' 
                + request.form['source'] + '/' 
                + request.form['target'] + '/' 
                + request.form['query'] + '/')
    # for GET show the search form
    else:
        translations = sorted([f[:-4] for f in 
        os.listdir(app.config['TEXTFILES_FOLDER']) 
        if f[-4:] == ".txt"])
        
        return render_template('search.html', full=full, translations=translations)
            
@app.route('/search/<text1>/<text2>/<query>/',defaults={'full': ''})
@app.route('/full/search/<text1>/<text2>/<query>/',defaults={'full': full})
def searchcompare(full,text1,text2,query):
    """
    URL: search/text1/text2/query/
    Search a term in one translation and return all verses in which it occurs
    together with the parallel verses in the second translation.
    """

    # clean up query term
    query = query.replace('+',' ')

    path1 = app.config['TEXTFILES_FOLDER'] + text1 + '.txt'
    path2 = app.config['TEXTFILES_FOLDER'] + text2 + '.txt'
    if not (os.path.isfile(path1) and os.access(path1, os.R_OK) and \
            os.path.isfile(path2) and os.access(path2, os.R_OK)):
        return render_template('error.html', full=full, error="One of the bibles is not available"), 404

    # open both files
    fh1 = codecs.open(path1,'r','utf-8').readlines()
    fh2 = codecs.open(path2,'r','utf-8').readlines()

    # check whether query term is a valid verse ID
    # if verse ID => search for respective verse
    if re.match(re.compile("\d{8}"),query):
        verses1 = {v.split('\t')[0]:v.split("\t")[1].strip() for v in fh1 
        if not v.strip().startswith("#") and v.split('\t')[0] == query}

    # otherwise search for query term in first translation
    else:
        verses1 = {v.split('\t')[0]:v.split('\t')[1].strip() for v in fh1 
          if not v.strip().startswith('#') and query in v.split('\t')[1]}

    # collect all verses with the IDs that are relevant for the query
    verseids = sorted(verses1.keys())
    verses2t = {v.split('\t')[0]:v.split('\t')[1].strip() for v in fh2 
        if v.strip()[:8] in verseids}
    verses2 = list()
    verses1rel = list()
    for v in verseids:
        if v in verses2t:
            verses2.append([v,verses2t[v]])
            verses1rel.append([v,verses1[v]])

    verses = zip(verses1rel,verses2)
            
    return render_template("compare.html", full=full, query=query, verses=verses,
                           text1=text1, text2=text2)
        
@app.route('/search/<text1>/<query>/',defaults={'full': ''})
@app.route('/full/search/<text1>/<query>/',defaults={'full': full})
def searchresults(full,text1,query):
    """
    URL: /search/text1/query/
    Lists all the verses containing the given search query for the given 
    translation
    """

    # clean up query term
    query = query.replace('+',' ')

    path1 = app.config['TEXTFILES_FOLDER'] + text1 + '.txt'
    if not (os.path.isfile(path1) and os.access(path1, os.R_OK)):
        return render_template('error.html', full=full, error="Bible text is not available."), 404

    # collect all verses containing the query term
    fh1 = codecs.open(path1,'r','utf-8').readlines()
    verses1 = [v.strip().split('\t') for v in fh1 if query in v and 
        not v.strip().startswith('#')]
    
    return render_template("searchresult.html", full=full, translation=text1,
        query=query, verses=verses1)
        
    
# /eng-x-bible-engkj-v0.zip/
@app.route('/<translation>-v<regex("\d+"):translationversion>.zip')
def zipfile(translation,translationversion):
    """
    URL: /translation.zip/
    Redirects to the respective zip datapackage for download
    """
    return redirect(app.config["ZIPFILES_FOLDER"] + translation + "-v"
        + translationversion + '.zip')

# /eng-x-bible-engkj/
@app.route('/<translation>/',defaults={'full': ''})
@app.route('/full/<translation>/',defaults={'full': full})
def listtranslation(full,translation):
    """
    URL: /translation/
    Searches for the highest version number for the respective translation
    and redirects to its listtranslationversion.
    """
    try:
        # search for all available versions of the translation
        versions = [f for f in os.listdir(app.config['TEXTFILES_FOLDER']) 
            if str(translation) in f]

        # get the highest version number for this translation
        versionnumbers = sorted([int(v[:-4].split('-')[-1][1:]) 
            for v in versions],reverse=True)

        return redirect(url_for('.listtranslationversion',full=full,
            translation=translation,
            translationversion=str(versionnumbers[0])))
    except Exception, e:
        app.logger.warn(traceback.format_exc())
        return render_template('error.html', full=full, error="Bible text not available"), 404

# /eng-x-bible-engkj-v0/    
@app.route('/<translation>-v<regex("\d+"):translationversion>/',defaults={'full': ''})
@app.route('/full/<translation>-v<regex("\d+"):translationversion>/',defaults={'full': full})
def listtranslationversion(full,translation,translationversion):
    """
    URL: /translationversion/
    Lists all metadata for the respective translation version together with
    links to the datapackage and (sample) text.
    """
    try:
        path = app.config['TEXTFILES_FOLDER'] + translation + "-v" + translationversion + '.txt'
        if not (os.path.isfile(path) and os.access(path, os.R_OK)):
            return render_template('error.html', full=full, error="Bible text does not exist."), 404
        with codecs.open(path, 'r','utf-8') as f:
            fh = f.readlines()

        # get all books for this translation version  
        books = []
        if full != '':
            books = sorted(list({l[:2] for l in fh if l[0] != "#" 
                and re.match('\d{2}',l[:2])}))

        # extract all metadata from the file
        info = [l[2:].split(":",1) for l in fh if re.match("# [a-zA-Z]",l)]
        urlsinfo = [l[1] for l in info if l[0] == "URL"]
        urls = urlsinfo[0].split("<br>")

        return render_template('translation.html', full=full,
            translation=translation,info=info,books=books,urls=urls,
            translationversion=translation+ "-v" + translationversion,
            version=translationversion)
    except Exception, e:
        app.logger.warn(traceback.format_exc())
        return render_template('error.html', full=full, error="Bible version not available"), 500
    

# /eng-x-bible-engkj-v0/41/        
@app.route('/<translation>/<regex("\d{2}"):book>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{2}"):book>/',defaults={'full': full})
def listbook(full,translation,book):
    """
    URL: /translationversion/book/
    Lists all chapters of the translation's book
    """

    # only show books's chapters when full access (except Mark)
    path = app.config['TEXTFILES_FOLDER'] + translation + '.txt'
    if full == '' and book != '41' or not (os.path.isfile(path) and os.access(path, os.R_OK)):
        return render_template("error.html", full=full, error="Book not available"), 404

    # get all chapters for the respective book
    fh = codecs.open(path,'r','utf-8').readlines()
    verses = [l.split('\t',1)[0] for l in fh if l[0] != "#" and l[:2] == book]
    rel_verses = sorted(list({v[2:5] for v in verses}))

    if verses:
        return render_template('book.html', full=full, translation=translation, book=book,
            chapters=rel_verses)
    else:
        return render_template("error.html", full=full, error="No verses available"), 404

# /eng-x-bible-engkj-v0/41/001/            
@app.route('/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/',
    defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/'
    ,defaults={'full': full})
def listchapter(full,translation,book,chapter):
    """
    URL: /translationversion/book/chapter/
    Lists all verses of the translation's chapter
    """

    # only show chapter's verses when full access (except Mark)
    if full == '' and book != '41':
        return render_template("error.html",error="Chapter not available"), 404

    # get all verses for the respective chapter
    path = app.config['TEXTFILES_FOLDER'] + translation + '.txt'
    if not (os.path.isfile(path) and os.access(path, os.R_OK)):
        return render_template("error.html", full=full, error="Bible not available"), 404
    fh = codecs.open(path,'r','utf-8').readlines()
    verses = [l.split('\t',1) for l in fh if l[0] != "#" 
        and l[:5] == book + chapter]
    rel_verses = sorted(verses)
    
    if verses:
        return render_template("chapter.html", full=full, translation=translation,
            book=book,chapter=chapter,verses=rel_verses)
    else:
        return render_template("error.html", full=full, error="No verses available"), 404
            
# /eng-x-bible-engkj-v0/41/001/001/ 
@app.route('/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/<regex("\d{3}"):verse>/',
    defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/<regex("\d{3}"):verse>/',
    defaults={'full': full})
def listverse(full,translation,book,chapter,verse):
    """
    URL: /translationversion/book/chapter/verse
    Shows the given verse
    """
    path = app.config['TEXTFILES_FOLDER'] + translation + '.txt'
    # only show the verse when full access (except Mark)
    if full == '' and book != '41' or not (os.path.isfile(path) and os.access(path, os.R_OK)):
        return render_template("error.html",error="Verse not available"), 404

    fh = codecs.open(path,'r','utf-8').readlines()
    verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
    
    if book+chapter+verse in verses:
        return render_template("verse.html", full=full, translation=translation,book=book,
                               chapter=chapter,verse=verse,versetext=verses[book+chapter+verse])
    else:
        return render_template("error.html", full=full, error="No verses available"), 404
            
# /eng-x-bible-engkj-v0/41001001/ 
@app.route('/<translation>/<regex("\d{8}"):verse>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{8}"):verse>/',
    defaults={'full': full})
def listverseflat(full,translation,verse):
    """
    URL: /translationversion/verse/
    Shows the given verse with flat ID
    """
    path = app.config['TEXTFILES_FOLDER'] + translation + '.txt'
    # only show the verse when full access (except Mark)
    if full == '' and verse[:2] != '41' or not (os.path.isfile(path) and os.access(path, os.R_OK)):
        return render_template("error.html", full=full, error="Verse not available"), 404
    fh = codecs.open(path, 'r','utf-8').readlines()
    verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
    
    if verse in verses:
        return render_template("verse.html", full=full, translation=translation,
            book=verse[:2],chapter=verse[2:5],verse=verse[5:],
            versetext=verses[verse])
    else:
        return render_template("error.html", full=full, error="No verses available"), 404

# /full/eng-x-bible-engkj-v0.txt/
@app.route('/full/<translation>-v<regex("\d+"):translationversion>.txt')
def textfilefull(translation,translationversion):
    """
    URL: /translationversion.txt
    Redirects to the text file of the given translationversion
    """
    return redirect('/' + app.config['BASE_URL'] + 'static/files/bible_corpus/corpus/'
        + translation + "-v" + translationversion + '.txt')

# /compare/eng-x-bible-engkj-v1/deu-x-bible-luther-v1/
@app.route('/compare/<translation1>/<translation2>/<verse>/',
    defaults={'full': ''})
@app.route('/full/compare/<translation1>/<translation2>/<verse>/',
    defaults={'full': full})
def compare(full,translation1,translation2,verse):
    """
    URL: /translation1/translation2/verse
    Compares two parallel verses from different translations and computes
    the association measure (Poisson) of each word pair
    """
    path1 = app.config['TEXTFILES_FOLDER'] + translation1 + '.txt'
    path2 = app.config['TEXTFILES_FOLDER'] + translation2 + '.txt'
    
    if not (os.path.isfile(path1) and os.access(path1, os.R_OK) and \
            os.path.isfile(path2) and os.access(path2, os.R_OK)):
        return render_template('error.html', full=full, error="One of the bibles is not available"), 404

    # read texts in ParText objects
    text1 = reader.ParText(path1)
    text2 = reader.ParText(path2)

    # create cooccurrence object
    poisson = cooccurrence.Cooccurrence(text1,text2,method="poisson")

    # extract words and association measures from the objects
    try:
        verse = int(verse)
        raw_words1 = poisson.text1.get_raw_verses()[verse]
        raw_words2 = poisson.text2.get_raw_verses()[verse]
    except (KeyError, ValueError):
        return render_template('error.html', full=full, error="The verse is not available"), 404
        

    words12 = [[poisson.get_assoc(w1.lower(),w2.lower()) 
        for w1 in raw_words1] for w2 in raw_words2]
    words21 = [[poisson.get_assoc(w1.lower(),w2.lower()) 
        for w2 in raw_words2] for w1 in raw_words1]
    words1 = [re.sub('"',"'",w) for w in raw_words1] 
    words2 = [re.sub('"',"'",w) for w in raw_words2] 

    # create alignment array for JavaScript
    alignment = [[[poisson.get_assoc(w1.lower(),w2.lower()),c2,c1] 
        for c1,w1 in enumerate(raw_words1)] for c2,w2 in enumerate(raw_words2)]

    # add additional global associated words
    additional = [poisson.nbest2(w.lower(),c) for c,w in enumerate(raw_words2)]

    return render_template('compareverse.html', full=full, words1=words1,words2=words2,
        words12=str(words12),words21=str(words21),alignment=str(alignment),
        verse=verse,translation1=translation1,translation2=translation2,
        additional = str(additional))

@app.route("/full/zipall/", defaults={'full':full})
def zipall(full):
    reltranslations = list()

    translations = ['-'.join(f.split("-")[:-1]) for f in
        os.listdir(app.config['TEXTFILES_FOLDER'])
        if f[-4:] == ".txt"]

    for translation in translations:

        # search for all available versions of the translation
        versions = [f for f in os.listdir(app.config['TEXTFILES_FOLDER'])
            if str(translation) in f]

        # get the highest version number for this translation
        versionnumbers = sorted([int(v[:-4].split('-')[-1][1:])
            for v in versions],reverse=True)

        reltranslations.append(translation + '-v' + str(versionnumbers[0]) + '.txt')

    zip = ZipFile(app.config['STATIC_FOLDER'] + '/files/bible_corpus.zip','w',ZIP_DEFLATED)

    for f in reltranslations[:100]:
        zip.write(app.config['TEXTFILES_FOLDER'] + f,f)

    zip.close()

    return redirect('/' + app.config['BASE_URL'] + 'static/files/bible_corpus.zip')

if __name__ == "__main__":
    app.run(debug=True)
