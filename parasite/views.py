#from parasite import app
from flask import Flask, render_template, url_for, redirect, g, request
from werkzeug.routing import BaseConverter
#from werkzeug.contrib.cache import SimpleCache
import os
import codecs
import re
import collections
import json
import reader, cooccurrence

# Use the RegexConverter function as a converter method for mapped urls
class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


# for caching the matrices
#cache = SimpleCache()

# Defining some constants for handling relative URLs on the server
BASE_URL = "data/"
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
TEXTFILES_FOLDER = BASE_PATH + '/static/files/textfiles/'
DATA_FOLDER = BASE_PATH + '/static/data/'
ZIPFILES_FOLDER = BASE_PATH + '/static/files/zipfiles/'

app = Flask(__name__,static_url_path='/static', static_folder = "static")
app.debug = True
app.config['TEXTFILES_FOLDER'] = TEXTFILES_FOLDER
app.config['ZIPFILES_FOLDER'] = ZIPFILES_FOLDER
app.config['DATA_FOLDER'] = DATA_FOLDER
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
    g.full = full
    
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
        currinfo = codebygeo[c]
        currdict["latitude"] = currinfo[2]
        currdict["longitude"] = currinfo[1]
        currdict["name"] = currinfo[0]
        currdict["code"] = c
        currdict["texts"] = codesbytranslations[c]
        languages.append(currdict)
        
    outdict = {"languages": languages}
        
    # create json file
    oh = codecs.open(app.config['DATA_FOLDER'] + 'languages.json','w','utf-8')
    json.dump(outdict,oh)
    oh.close()
    
    return render_template('index.html')
    
@app.route('/all/',defaults={'full': ''})
@app.route('/full/all/',defaults={'full': full})
def listtranslations(full):
    """
    URL: /all/
    Gathers all translations from the textfile folder and gets the information
    about their genealogy to be shown in the tabular representation.
    """
    g.full = full
    g.baseurl = BASE_URL
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
    translations2 = [(t,codebygeo[t[:3]][0],
        codebyinfo[t[:3]][1]) for t in translations]

    return render_template('list.html', translations = translations2)
    
@app.route('/search/',methods=['POST', 'GET'],defaults={'full': ''})
@app.route('/full/search/',methods=['POST', 'GET'],defaults={'full': full})
def search(full):
    """
    URL: /search/
    Provides either search form with all translations with GET or redirects
    to the respective GET search URL with POST
    """
    g.full = full

    # for POST redirect to respective GET URL
    if request.method == "POST":
        if request.form['target'] == "None":
            return redirect('/' + BASE_URL + g.full + 'search/' 
                + request.form['source'] + '/' 
                + request.form['query'] + '/')
        else:
            return redirect('/' + BASE_URL + g.full + 'search/' 
                + request.form['source'] + '/' 
                + request.form['target'] + '/' 
                + request.form['query'] + '/')
    # for GET show the search form
    else:
        translations = sorted([f[:-4] for f in 
        os.listdir(app.config['TEXTFILES_FOLDER']) 
        if f[-4:] == ".txt"])
        
        return render_template('search.html',translations=translations)
            
@app.route('/search/<text1>/<text2>/<query>/',defaults={'full': ''})
@app.route('/full/search/<text1>/<text2>/<query>/',defaults={'full': full})
def searchcompare(full,text1,text2,query):
    """
    URL: search/text1/text2/query/
    Search a term in one translation and return all verses in which it occurs
    together with the parallel verses in the second translation.
    """
    g.full = full

    # clean up query term
    query = query.replace('+',' ')

    # open both files
    fh1 = codecs.open(app.config['TEXTFILES_FOLDER'] + text1 
        + '.txt','r','utf-8').readlines()
    fh2 = codecs.open(app.config['TEXTFILES_FOLDER'] + text2 
        + '.txt','r','utf-8').readlines()

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
            
    return render_template("compare.html",query=query,
        verses=verses,
        text1=text1,text2=text2)
        
@app.route('/search/<text1>/<query>/',defaults={'full': ''})
@app.route('/full/search/<text1>/<query>/',defaults={'full': full})
def searchresults(full,text1,query):
    """
    URL: /search/text1/query/
    Lists all the verses containing the given search query for the given 
    translation
    """
    g.full = full

    # clean up query term
    query = query.replace('+',' ')

    # collect all verses containing the query term
    fh1 = codecs.open(app.config['TEXTFILES_FOLDER'] + text1 
        + '.txt','r','utf-8').readlines()
    verses1 = [v.strip().split('\t') for v in fh1 if query in v and 
        not v.strip().startswith('#')]
    
    return render_template("searchresult.html",translation=text1,
        query=query,verses=verses1)
        
    
# /eng-x-bible-engkj-v0.zip/
@app.route('/<translation>-v<regex("\d+"):translationversion>.zip')
def zipfile(translation,translationversion):
    """
    URL: /translation.zip/
    Redirects to the respective zip datapackage for download
    """
    g.full = ''

    return redirect('static/files/zipfiles/' + translation + "-v" 
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
    g.full = full
    g.baseurl = BASE_URL

    try:
        # search for all available versions of the translation
        versions = [f for f in os.listdir(app.config['TEXTFILES_FOLDER']) 
            if str(translation) in f]

        # get the highest version number for this translation
        versionnumbers = sorted([int(v[:-4].split('-')[-1][1:]) 
            for v in versions],reverse=True)

        return redirect(url_for('.listtranslationversion',full=g.full,
            translation=translation,
            translationversion=str(versionnumbers[0])))
    except:
        return render_template('error.html',
            error="Bible text not available")

# /eng-x-bible-engkj-v0/    
@app.route('/<translation>-v<regex("\d+"):translationversion>/',defaults={'full': ''})
@app.route('/full/<translation>-v<regex("\d+"):translationversion>/',defaults={'full': full})
def listtranslationversion(full,translation,translationversion):
    """
    URL: /translationversion/
    Lists all metadata for the respective translation version together with
    links to the datapackage and (sample) text.
    """
    g.full = full
    g.baseurl = BASE_URL
    try:
        fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation 
            + "-v" + translationversion + '.txt',
            'r','utf-8').readlines()

        # get all books for this translation version  
        books = []
        if g.full != '':
            books = sorted(list({l[:2] for l in fh if l[0] != "#" 
                and re.match('\d{2}',l[:2])}))

        # extract all metadata from the file
        info = [l[2:].split(":",1) for l in fh if re.match("# [a-zA-Z]",l)]
        urlsinfo = [l[1] for l in info if l[0] == "URL"]
        urls = urlsinfo[0].split("<br>")

        return render_template('translation.html',
            translation=translation,info=info,books=books,urls=urls,
            translationversion=translation+ "-v" + translationversion,
            version=translationversion)
    except:
        return render_template('error.html',error="Bible version not available")
    

# /eng-x-bible-engkj-v0/41/        
@app.route('/<translation>/<regex("\d{2}"):book>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{2}"):book>/',defaults={'full': full})
def listbook(full,translation,book):
    """
    URL: /translationversion/book/
    Lists all chapters of the translation's book
    """
    g.full = full
    g.baseurl = BASE_URL

    # only show books's chapters when full access (except Mark)
    if g.full == '' and book != '41':
        return render_template("error.html",error="Book not available")

    # get all chapters for the respective book
    fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
        'r','utf-8').readlines()
    verses = [l.split('\t',1)[0] for l in fh if l[0] != "#" and l[:2] == book]
    rel_verses = sorted(list({v[2:5] for v in verses}))

    if verses:
        return render_template('book.html',translation=translation,book=book,
            chapters=rel_verses)
    else:
        return render_template("error.html",error="No verses available")

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
    g.full = full
    g.baseurl = BASE_URL

    # only show chapter's verses when full access (except Mark)
    if g.full == '' and book != '41':
        return render_template("error.html",error="Chapter not available")

    # get all verses for the respective chapter
    fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
        'r','utf-8').readlines()
    verses = [l.split('\t',1) for l in fh if l[0] != "#" 
        and l[:5] == book + chapter]
    rel_verses = sorted(verses)
    
    if verses:
        return render_template("chapter.html",translation=translation,
            book=book,chapter=chapter,verses=rel_verses)
    else:
        return render_template("error.html",error="No verses available")
            
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
    g.full = full
    g.baseurl = BASE_URL

    # only show the verse when full access (except Mark)
    if g.full == '' and book != '41':
        return render_template("error.html",error="Verse not available")
    else:
        fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
        'r','utf-8').readlines()
        verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() 
            for l in fh if l[0] != "#"}
    
    if book+chapter+verse in verses:
        return render_template("verse.html",translation=translation,book=book,
        chapter=chapter,verse=verse,versetext=verses[book+chapter+verse])
    else:
        return render_template("error.html",error="No verses available")
            
# /eng-x-bible-engkj-v0/41001001/ 
@app.route('/<translation>/<regex("\d{8}"):verse>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{8}"):verse>/',
    defaults={'full': full})
def listverseflat(full,translation,verse):
    """
    URL: /translationversion/verse/
    Shows the given verse with flat ID
    """
    g.full = full
    g.baseurl = BASE_URL

    # only show the verse when full access (except Mark)
    if g.full == '' and verse[:2] != '41':
        return render_template("error.html",error="Verse not available")
    else:
        fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
        'r','utf-8').readlines()
        verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() 
            for l in fh if l[0] != "#"}
    
    if verse in verses:
        return render_template("verse.html",translation=translation,
            book=verse[:2],chapter=verse[2:5],verse=verse[5:],
            versetext=verses[verse])
    else:
        return render_template("error.html",error="No verses available")

# /full/eng-x-bible-engkj-v0.txt/
@app.route('/full/<translation>-v<regex("\d+"):translationversion>.txt')
def textfilefull(translation,translationversion):
    """
    URL: /translationversion.txt
    Redirects to the text file of the given translationversion
    """
    g.full = full
    g.baseurl = BASE_URL

    return redirect('/' + g.baseurl + 'static/files/textfiles/' 
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
    g.full = full
    g.baseurl = BASE_URL

    """
    # version with SimpleCache (not fast enough as it is)
    assoc = cache.get(translation1 + "_" + translation2)
    if assoc is None:

        text1 = reader.ParText(app.config['TEXTFILES_FOLDER'] + translation1 + '.txt')
        text2 = reader.ParText(app.config['TEXTFILES_FOLDER'] + translation2 + '.txt')
        poisson = cooccurrence.Cooccurrence(text1,text2,method="poisson")

        pack = poisson

        assoc = cache.set(translation1 + "_" + translation2, pack, timeout= 5 * 60)

    else:
        poisson = assoc
    """

    # read texts in ParText objects
    text1 = reader.ParText(app.config['TEXTFILES_FOLDER'] 
        + translation1 + '.txt')
    text2 = reader.ParText(app.config['TEXTFILES_FOLDER'] 
        + translation2 + '.txt')

    # create cooccurrence object
    poisson = cooccurrence.Cooccurrence(text1,text2,method="poisson")

    # extract words and association measures from the objects
    raw_words1 = poisson.text1.get_raw_verses()[int(verse)]
    raw_words2 = poisson.text2.get_raw_verses()[int(verse)]
    verse1 = poisson.text1[int(verse)]
    verse2 = poisson.text2[int(verse)]

    words12 = [[poisson.get_assoc(w1.lower(),w2.lower()) 
        for w1 in raw_words1] for w2 in raw_words2]
    words21 = [[poisson.get_assoc(w1.lower(),w2.lower()) 
        for w2 in raw_words2] for w1 in raw_words1]
    words1 = [re.sub('"',"'",w) for w in raw_words1] 
    words2 = [re.sub('"',"'",w) for w in raw_words2] 

    # create alignment array for JavaScript
    alignment = [[[poisson.get_assoc(w1.lower(),w2.lower()),c2,c1] 
        for c1,w1 in enumerate(raw_words1)] for c2,w2 in enumerate(raw_words2)]

    return render_template('compareverse.html',words1=words1,words2=words2,
        words12=str(words12),words21=str(words21),alignment=str(alignment),
        verse=verse,translation1=translation1,translation2=translation2)



if __name__ == "__main__":
    app.run(debug=True)
