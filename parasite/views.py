#from parasite import app
from flask import Flask, render_template, url_for, redirect, g, request
from werkzeug.routing import BaseConverter
import os
import codecs
import re
import collections
import json

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

BASE_URL = "data/"
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
TEXTFILES_FOLDER = BASE_PATH + '/static/files/textfiles/'
DATA_FOLDER = BASE_PATH + '/static/data/'
ZIPFILES_FOLDER = BASE_PATH + '/static/files/zipfiles/'
#TEXTFILES_FOLDER = '/var/www/paralleltext.info/flask/parasite/static/files/textfiles'
#DATA_FOLDER = '/var/www/paralleltext.info/flask/parasite/static/data/'

# Use the RegexConverter function as a converter
# method for mapped urls
app = Flask(__name__,static_url_path='/static', static_folder = "static")
app.debug = True
app.config['TEXTFILES_FOLDER'] = TEXTFILES_FOLDER
app.config['ZIPFILES_FOLDER'] = ZIPFILES_FOLDER
app.config['DATA_FOLDER'] = DATA_FOLDER
app.url_map.converters['regex'] = RegexConverter


full = 'full/' # URL for full access

@app.route('/',defaults={'full': ''})
@app.route('/full/',defaults={'full': full})
def index(full):
    g.full = full

    #abspath = app.config['TEXTFILES_FOLDER']
    #return render_template("error.html",error=abspath)
    
    # create json file for map display
    translations = sorted(list({'-'.join(f[:-4].split('-')[:-1]) for f in 
    	os.listdir(app.config['TEXTFILES_FOLDER']) 
    	if f[-4:] == ".txt"}))
    codesbytranslations = collections.defaultdict(list)
    for t in translations:
    	codesbytranslations[t[:3]].append(t)
    fh = codecs.open(app.config['DATA_FOLDER'] + 'lang_coords_all.txt','r','utf-8').readlines()
    codebygeo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh[1:]}
    
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
    	
    oh = codecs.open(app.config['DATA_FOLDER'] + 'languages.json','w','utf-8')
    json.dump(outdict,oh)
    oh.close()
    
    return render_template('index.html')
    
@app.route('/all/',defaults={'full': ''})
@app.route('/full/all/',defaults={'full': full})
def listtranslations(full):
    g.full = full
    g.baseurl = BASE_URL
    translations = sorted(list({'-'.join(f[:-4].split('-')[:-1]) for f in 
			os.listdir(app.config['TEXTFILES_FOLDER']) 
			if f[-4:] == ".txt"}))
    fh = codecs.open(app.config['DATA_FOLDER'] + 'lang2fam.csv','r','utf-8').readlines()
    codebyinfo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh}
    fh2 = codecs.open(app.config['DATA_FOLDER'] + 'lang_coords_all.txt','r','utf-8').readlines()
    codebygeo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh2[1:]}
    translations2 = [(t,codebygeo[t[:3]][0],codebyinfo[t[:3]][0]) for t in translations]
    return render_template('list.html', translations = translations2)
    
@app.route('/search/',methods=['POST', 'GET'],defaults={'full': ''})
@app.route('/full/search/',methods=['POST', 'GET'],defaults={'full': full})
def search(full):
		g.full = full
		if request.method == "POST":
			if request.form['target'] == "None":
				return redirect('/' + BASE_URL + g.full + 'search/' + request.form['source'] + '/' + request.form['query'] + '/')
			else:
				return redirect('/' + BASE_URL + g.full + 'search/' + request.form['source'] + '/' + request.form['target'] + '/' + \
				request.form['query'] + '/')
		else:
			translations = sorted([f[:-4] for f in 
			os.listdir(app.config['TEXTFILES_FOLDER']) 
			if f[-4:] == ".txt"])
			
			return render_template('search.html',translations=translations)
			
@app.route('/search/<text1>/<text2>/<query>/',defaults={'full': ''})
@app.route('/full/search/<text1>/<text2>/<query>/',defaults={'full': full})
def searchcompare(full,text1,text2,query):
		g.full = full
		query = query.replace('+',' ')
		fh1 = codecs.open(app.config['TEXTFILES_FOLDER'] + text1 + '.txt','r','utf-8').readlines()
		fh2 = codecs.open(app.config['TEXTFILES_FOLDER'] + text2 + '.txt','r','utf-8').readlines()
		verses1 = [v.strip().split('\t') for v in fh1 if query in v and not v.strip().startswith('#')]
		verseids = [v[0] for v in verses1]
		verses2t = {v.split('\t')[0]:v.strip().split('\t')[1] for v in fh2 if v.strip()[:8] in verseids}
		verses2 = list()
		for v in verseids:
			if v in verses2t:
				verses2.append([v,verses2t[v]])
			else:
				verses2.append([v,''])
		
		return render_template("compare.html",query=query,verses=zip(verses1,verses2))
		
@app.route('/search/<text1>/<query>/',defaults={'full': ''})
@app.route('/full/search/<text1>/<query>/',defaults={'full': full})
def searchresults(full,text1,query):
		g.full = full
		query = query.replace('+',' ')
		fh1 = codecs.open(app.config['TEXTFILES_FOLDER'] + text1 + '.txt','r','utf-8').readlines()
		verses1 = [v.strip().split('\t') for v in fh1 if query in v and not v.strip().startswith('#')]
		
		return render_template("searchresult.html",query=query,verses=verses1)
		
    
# /eng-x-bible-engkj-v0.zip/
@app.route('/<translation>-v<translationversion>.zip')
def zipfile(translation,translationversion):
		g.full = ''
		return redirect('static/files/zipfiles/' + translation + "-v" + translationversion + '.zip')

# /eng-x-bible-engkj/
@app.route('/<translation>/',defaults={'full': ''})
@app.route('/full/<translation>/',defaults={'full': full})
def listtranslation(full,translation):
		g.full = full
		g.baseurl = BASE_URL
		try:
		
			versions = [f for f in os.listdir(app.config['TEXTFILES_FOLDER']) 
				if str(translation) in f]
			versionnumbers = sorted([int(v[:-4].split('-')[-1][1:]) for v in versions],reverse=True)
			#return redirect('/' + g.full + translation + '-v' + str(versionnumbers[0]) + '/')
			return redirect(url_for('.listtranslationversion',full=g.full,translation=translation,
			    translationversion=str(versionnumbers[0])))
		except:
			return render_template('error.html',error="Bible text not available")

# /eng-x-bible-engkj-v0/	
@app.route('/<translation>-v<translationversion>/',defaults={'full': ''})
@app.route('/full/<translation>-v<translationversion>/',defaults={'full': full})
def listtranslationversion(full,translation,translationversion):
		g.full = full
		g.baseurl = BASE_URL
		#try:
		if True:
			fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + "-v" + translationversion + '.txt',
			'r','utf-8').readlines()
			books = []
			if g.full != '':
				books = sorted(list({l[:2] for l in fh if l[0] != "#" and re.match('\d{2}',l[:2])}))
			info = [l[2:].split(":",1) for l in fh if re.match("# [a-zA-Z]",l)]
			urlsinfo = [l[1] for l in info if l[0] == "URL"]
			urls = urlsinfo[0].split("<br>")
			return render_template('translation.html',
			translation=translation,info=info,books=books,urls=urls,
			translationversion=translation+ "-v" + translationversion,version=translationversion)
		#except:
		#	return render_template('error.html',error="Bible version not available")
	

# /eng-x-bible-engkj-v0/41/		
@app.route('/<translation>/<regex("\d{2}"):book>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{2}"):book>/',defaults={'full': full})
def listbook(full,translation,book):
		g.full = full
		g.baseurl = BASE_URL
		if g.full == '' and book != '41':
			return render_template("error.html",error="Book not available")
		fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
			'r','utf-8').readlines()
		verses = [l.split('\t',1)[0] for l in fh if l[0] != "#" and l[:2] == book]
		rel_verses = sorted(list({v[2:5] for v in verses}))
		if verses:
			return render_template('book.html',translation=translation,book=book,chapters=rel_verses)
		else:
			return render_template("error.html",error="No verses available")

# /eng-x-bible-engkj-v0/41/001/			
@app.route('/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/',defaults={'full': full})
def listchapter(full,translation,book,chapter):
		g.full = full
		g.baseurl = BASE_URL
		if g.full == '' and book != '41':
			return render_template("error.html",error="Chapter not available")
		fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
			'r','utf-8').readlines()
		verses = [l.split('\t',1) for l in fh if l[0] != "#" and l[:5] == book + chapter]
		rel_verses = sorted(verses)
		
		if verses:
			return render_template("chapter.html",translation=translation,book=book,chapter=chapter,verses=rel_verses)
		else:
			return render_template("error.html",error="No verses available")
			
# /eng-x-bible-engkj-v0/41/001/001/ 
@app.route('/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/<regex("\d{3}"):verse>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/<regex("\d{3}"):verse>/',defaults={'full': full})
def listverse(full,translation,book,chapter,verse):
		g.full = full
		g.baseurl = BASE_URL
		if g.full == '' and book != '41':
			return render_template("error.html",error="Verse not available")
		else:
			fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
			'r','utf-8').readlines()
			verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
		
		if book+chapter+verse in verses:
			return render_template("verse.html",translation=translation,book=book,
			chapter=chapter,verse=verse,versetext=verses[book+chapter+verse])
		else:
			return render_template("error.html",error="No verses available")
			
# /eng-x-bible-engkj-v0/41001001/ 
@app.route('/<translation>/<regex("\d{8}"):verse>/',defaults={'full': ''})
@app.route('/full/<translation>/<regex("\d{8}"):verse>/',defaults={'full': full})
def listverseflat(full,translation,verse):
		g.full = full
		g.baseurl = BASE_URL
		if g.full == '' and verse[:2] != '41':
			return render_template("error.html",error="Verse not available")
		else:
			fh = codecs.open(app.config['TEXTFILES_FOLDER'] + translation + '.txt',
			'r','utf-8').readlines()
			verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
		
		if verse in verses:
			return render_template("verse.html",translation=translation,book=verse[:2],
			chapter=verse[2:5],verse=verse[5:],versetext=verses[verse])
		else:
			return render_template("error.html",error="No verses available")

# /full/eng-x-bible-engkj-v0.txt/
@app.route('/full/<translation>-v<translationversion>.txt')
def textfilefull(translation,translationversion):
		g.full = full
		g.baseurl = BASE_URL
		return redirect('/' + g.baseurl + 'static/files/textfiles/' + translation + "-v" + translationversion + '.txt')

if __name__ == "__main__":
    app.run(debug=True)
