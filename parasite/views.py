from parasite import parasite
from flask import render_template, url_for, redirect, g
from werkzeug.routing import BaseConverter
import os
import codecs
import re

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
        
# Use the RegexConverter function as a converter
# method for mapped urls
parasite.url_map.converters['regex'] = RegexConverter

full = 'full/' # URL for full access

@parasite.route('/')
@parasite.route('/index')
def index():
    g.full = ''
    return render_template('index.html')
    
@parasite.route('/all/')
def listtranslations():
    g.full = ''
    translations = sorted(list({'-'.join(f[:-4].split('-')[:-1]) for f in 
			os.listdir(os.path.dirname(__file__) + '/static/files/textfiles/') 
			#os.listdir(url_for('static') + 'files/textfiles/')
			if f[-4:] == ".txt"}))
    fh = codecs.open(os.path.dirname(__file__) + '/static/data/codesfamilies.csv','r','utf-8').readlines()
    codebyinfo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh}
    translations2 = [(t,codebyinfo[t[:3]][0],codebyinfo[t[:3]][1]) for t in translations]
    return render_template('list.html', translations = translations2)
    
@parasite.route('/search/')
def search():
		g.full = ''
		translations = sorted([f[:-4] for f in 
		os.listdir(os.path.dirname(__file__) + '/static/files/textfiles/') 
		if f[-4:] == ".txt"])
		
		return render_template('search.html',translations=translations)
    
# /eng-x-bible-engkj-v0.zip/
@parasite.route('/<translation>-v<translationversion>.zip')
def zipfile(translation,translationversion):
		g.full = ''
		return redirect('/static/files/zipfiles/' + translation + "-v" + translationversion + '.zip')

# /eng-x-bible-engkj/
@parasite.route('/<translation>/')
def listtranslation(translation):
		g.full = ''
		try:
			versions = [f for f in os.listdir(os.path.dirname(__file__) + '/static/files/textfiles/') 
				if str(translation) in f]
			versionnumbers = sorted([int(v[:-4].split('-')[-1][1:]) for v in versions],reverse=True)
			return redirect('/' + translation + '-v' + str(versionnumbers[0]) + '/')
		except:
			return render_template('error.html',error="Bible text not available")

# /eng-x-bible-engkj-v0/	
@parasite.route('/<translation>-v<translationversion>/')
def listtranslationversion(translation,translationversion):
		g.full = ''
		try:
			fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + "-v" + translationversion + '.txt',
			'r','utf-8').readlines()
			books = []
			info = [l[1:].split(":",1) for l in fh if l[0] == "#"]
			return render_template('translation.html',translation=translation+ "-v" + translationversion,info=info,books=books)
		except:
			return render_template('error.html',error="Bible version not available")
	

# /eng-x-bible-engkj-v0/41/		
@parasite.route('/<translation>/<regex("\d{2}"):book>/')
def listbook(translation,book):
		g.full = ''
		if book != '41':
			return render_template("error.html",error="Book not available")
		fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
			'r','utf-8').readlines()
		verses = [l.split('\t',1)[0] for l in fh if l[0] != "#" and l[:2] == book]
		rel_verses = sorted(list({v[2:5] for v in verses}))
		if verses:
			return render_template('book.html',translation=translation,book=book,chapters=rel_verses)
		else:
			return render_template("error.html",error="No verses available")

# /eng-x-bible-engkj-v0/41/001/			
@parasite.route('/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/')
def listchapter(translation,book,chapter):
		g.full = ''
		if book != '41':
			return render_template("error.html",error="Chapter not available")
		fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
			'r','utf-8').readlines()
		verses = [l.split('\t',1) for l in fh if l[0] != "#" and l[:5] == book + chapter]
		rel_verses = sorted(verses)
		
		if verses:
			return render_template("chapter.html",translation=translation,book=book,chapter=chapter,verses=rel_verses)
		else:
			return render_template("error.html",error="No verses available")
			
# /eng-x-bible-engkj-v0/41/001/001/ 
@parasite.route('/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/<regex("\d{3}"):verse>/')
def listverse(translation,book,chapter,verse):
		g.full = ''
		if book != '41':
			return render_template("error.html",error="Verse not available")
		else:
			fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
			'r','utf-8').readlines()
			verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
		
		if book+chapter+verse in verses:
			return render_template("verse.html",translation=translation,book=book,
			chapter=chapter,verse=verse,versetext=verses[book+chapter+verse])
		else:
			return render_template("error.html",error="No verses available")
			
# /eng-x-bible-engkj-v0/41001001/ 
@parasite.route('/<translation>/<regex("\d{8}"):verse>/')
def listverseflat(translation,verse):
		g.full = ''
		if verse[:2] != '41':
			return render_template("error.html",error="Verse not available")
		else:
			fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
			'r','utf-8').readlines()
			verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
		
		if verse in verses:
			return render_template("verse.html",translation=translation,book=verse[:2],
			chapter=verse[2:5],verse=verse[5:],versetext=verses[verse])
		else:
			return render_template("error.html",error="No verses available")
			
			
######################################## FULL PART ########################################

@parasite.route('/full/')
@parasite.route('/full/index')
def indexfull():
		g.full = full
		return render_template('index.html')
		
@parasite.route('/full/all/')
def listtranslationsfull():
    translations = sorted(list({'-'.join(f[:-4].split('-')[:-1]) for f in 
			os.listdir(os.path.dirname(__file__) + '/static/files/textfiles/') 
			#os.listdir(url_for('static') + 'files/textfiles/')
			if f[-4:] == ".txt"}))
    fh = codecs.open(os.path.dirname(__file__) + '/static/data/codesfamilies.csv','r','utf-8').readlines()
    codebyinfo = {l.split('\t')[0]:l.strip().split('\t')[1:] for l in fh}
    translations2 = [(t,codebyinfo[t[:3]][0],codebyinfo[t[:3]][1]) for t in translations]
    g.full = full
    return render_template('list.html', translations = translations2)
    
# /full/eng-x-bible-engkj-v0.txt/
@parasite.route('/full/<translation>-v<translationversion>.txt')
def textfilefull(translation,translationversion):
		g.full = ''
		return redirect('/static/files/textfiles/' + translation + "-v" + translationversion + '.txt')

# /full/eng-x-bible-engkj/
@parasite.route('/full/<translation>/')
def listtranslationfull(translation):
		g.full = full
		try:
			versions = [f for f in os.listdir(os.path.dirname(__file__) + '/static/files/textfiles/') 
				if str(translation) in f]
			versionnumbers = sorted([int(v[:-4].split('-')[-1][1:]) for v in versions],reverse=True)
			return redirect('/' + g.full + translation + '-v' + str(versionnumbers[0]) + '/')
		except:
			return render_template('error.html',error="Bible text not available")

# /full/eng-x-bible-engkj-v0/	
@parasite.route('/full/<translation>-v<translationversion>/')
def listtranslationversionfull(translation,translationversion):
		g.full = full
		try:
			fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + "-v" + translationversion + '.txt',
			'r','utf-8').readlines()
			books = sorted(list({l[:2] for l in fh if l[0] != "#" and re.match('\d{2}',l[:2])}))
			info = [l[1:].split(":",1) for l in fh if l[0] == "#"]
			return render_template('translation.html',translation=translation+ "-v" + translationversion,info=info,books=books)
		except:
			return render_template('error.html',error="Bible version not available")
	

# /full/eng-x-bible-engkj-v0/41/		
@parasite.route('/full/<translation>/<regex("\d{2}"):book>/')
def listbookfull(translation,book):
		g.full = full
		fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
			'r','utf-8').readlines()
		verses = [l.split('\t',1)[0] for l in fh if l[0] != "#" and l[:2] == book]
		rel_verses = sorted(list({v[2:5] for v in verses}))
		if verses:
			return render_template('book.html',translation=translation,book=book,chapters=rel_verses)
		else:
			return render_template("error.html",error="No verses available")

# /full/eng-x-bible-engkj-v0/41/001/			
@parasite.route('/full/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/')
def listchapterfull(translation,book,chapter):
		g.full = full
		fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
			'r','utf-8').readlines()
		verses = [l.split('\t',1) for l in fh if l[0] != "#" and l[:5] == book + chapter]
		rel_verses = sorted(verses)
		
		if verses:
			return render_template("chapter.html",translation=translation,book=book,chapter=chapter,verses=rel_verses)
		else:
			return render_template("error.html",error="No verses available")
			
# /full/eng-x-bible-engkj-v0/41/001/001/ 
@parasite.route('/full/<translation>/<regex("\d{2}"):book>/<regex("\d{3}"):chapter>/<regex("\d{3}"):verse>/')
def listversefull(translation,book,chapter,verse):
		g.full = full
		fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
		'r','utf-8').readlines()
		verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
	
		if book+chapter+verse in verses:
			return render_template("verse.html",translation=translation,book=book,
			chapter=chapter,verse=verse,versetext=verses[book+chapter+verse])
		else:
			return render_template("error.html",error="No verses available")
			
# /full/eng-x-bible-engkj-v0/41001001/ 
@parasite.route('/full/<translation>/<regex("\d{8}"):verse>/')
def listverseflatfull(translation,verse):
		g.full = full
		fh = codecs.open(os.path.dirname(__file__) + '/static/files/textfiles/' + translation + '.txt',
		'r','utf-8').readlines()
		verses = {l.split('\t',1)[0]:l.split('\t',1)[1].strip() for l in fh if l[0] != "#"}
	
		if verse in verses:
			return render_template("verse.html",translation=translation,book=verse[:2],
			chapter=verse[2:5],verse=verse[5:],versetext=verses[verse])
		else:
			return render_template("error.html",error="No verses available")
			