# -*- encoding:utf-8 -*-
__author__="Thomas Mayer"
__date__="2014-04-22"

import collections
# commented out for the time being
try:
    from scipy.sparse import lil_matrix, csc_matrix, coo_matrix
    from scipy.io import mmread, mmwrite
    import scipy.special
    import numpy as np
    import pandas as pd
except:
    pass
import re
import os
import codecs

class ParText():
    """Reads a file in the BibleText format and provides several ways to access the text.
    Parameters:
    =============
    filename: name of the file to be read (first three letters must indicate ISO 639-3 code)
    commentmarker: character that marks a comment line 
    separator: character that separates Bible IDs from the actual text
    enc: encoding of the file (default: UTF-8)
    """
    
    def __init__(self,filename,commentmarker="#",sep="\t",enc="utf-8",portions=None):
        
        self.iso = filename[:3]
        self.filename = filename
        
        # get shortcuts
        if re.match('^[a-zA-Z]{3}$',filename):
            bible_files = [f for f in os.listdir(settings._data_dir) if not f.startswith('.')]
            iso_by_bible = {f[:3]:f for f in bible_files}
            filename = iso_by_bible[filename]
        
        # open file
        fh = [line for line in codecs.open(filename,'r',encoding=enc).readlines()
              if not line.lstrip().startswith(commentmarker)]

        self.raw_verses = [(int(items[0]),items[1].split()) 
            for line in fh
            for items in [line.split(sep,1)]
            if portions == None or int(line.lstrip()[:2]) in portions]
        
        # clean up all punctuation marks TODO: find a better method to remove all non-letters!
        pat = re.compile("[“”‘’`´“”‘’`´‚<>.;,:?¿‹›!()\[\]—\"„§$%&\/\=_{}]")
        fh = "\t\t".join(fh)
        fh = re.sub(pat,'',fh).lower()
        fh = fh.split("\t\t")
        
        # collect all verses    
        self.verses = [(int(items[0]),items[1].split()) for line in fh 
                    for items in [line.split(sep,1)] 
                    if portions == None or int(line.lstrip()[:2]) in portions] 
                    
        self.versedict = dict(self.verses)
                    
    def __getitem__(self,id):
        """Returns the text of the verse given by the verse id.
        """
        return self.versedict[id]

    def get_raw_verses(self):

        return {v[0]:v[1] for v in self.raw_verses}
        
    def __len__(self):
        """Returns the length of the parallel text in number of verses.
        """
        return len(self.verses)
    
    def get_verses(self,format="dict"):
        """Returns the verses of the parallel text
        Parameters:
        ==============
        format: either as a list of tuples [format='tuple'] (40001001,"bla...bla") 
            or as a dictionary [format='dict'] {400010001: "bla...bla"}
        """
        if format == "tuple":
            return self.verses
        else:
            return self.versedict
            
    def get_verses_strings(self):
        """
        Returns a list of tuples with verse ID and verse text as string (ID,text).
        """
        
        return [(v[0],' '.join(v[1])) for v in self.verses]
            
    def get_lexicon(self):
        """Returns the wordforms of the text together with the information in which verses they
        occur. 
        """
        
        lex = collections.defaultdict(set)
        for id,verse in self.verses:
            for word in verse:
                lex[word].add(id)
                
        for l in lex:
            lex[l] = sorted(list(lex[l]))
                
        return lex
            
    def get_wordforms(self,format="types"):
        """Returns the wordforms (types or tokens) of the parallel text.
        Parameters:
        ===========
        format: either as a dict of types [format='types'] (with frequency as value) 
            or a list of tokens [format='tokens']
        """
        if format == 'types':
            # collect all wordforms (types and tokens)
            wordforms = collections.defaultdict(int)
            for id,verse in self.verses:
                for word in verse:
                    wordforms[word] += 1
            return wordforms
        else: # tokens
            words = set()
            for id, verse in self.verses:
                words.update(verse)
            return sorted(words)
            
    def wordforms_verses_count(self):
        """Returns a two-dimensional dictionary of wordforms and verses and how often the
        wordform occurs in the verse."""
        
        wordforms_verses_counter = collections.defaultdict(lambda: collections.defaultdict(int))
        wordforms_by_verses = self.wordforms_verses()
        for wordform in wordforms_by_verses:
            for verse in wordforms_by_verses[wordform]:
                wordforms_verses_counter[wordform][verse] += 1
                
        return wordforms_verses_counter
        
            
    def wordforms_verses(self):
        """Returns a dictionary of wordforms in which verses they occur.
        """
        
        wordforms_by_verses = collections.defaultdict(list)
        
        for id,verse in self.verses:
            for word in verse:
                wordforms_by_verses[word.lower()].append(id)
                
        return wordforms_by_verses
        
    def substrings_wordforms(self):
        """Returns a dictionary of substrings in which wordforms they occur.
        """
        
        substrings_by_wordforms = collections.defaultdict(set)
        wordforms = self.get_wordforms()
        
        for word in wordforms:
            word = word.lower()
            for i in range(len(word)+1):
                for j in range(i+1,len(word)+1):
                    substrings_by_wordforms[word[i:j]].add(word)
                    
        return substrings_by_wordforms
            
    def get_verseids(self):
        """Returns the verse Ids for this parallel text."""
        
        return sorted([v[0] for v in self.verses])

    def get_max_verseid(self):
        return self.verses[-1][0]

    def get_matrix(self, matrix_width=99999999):
        """Returns a sparse matrix with verse IDs as row names and words as column names where
        each cell indicates how many times the word occurs in the respective verse."""

        def row_iter(verses, wordforms_by_number):
            for id, verse in verses:
                for word in verse:
                    yield wordforms_by_number[word]

        def column_iter(verses):
            for id, verse in verses:
                for _ in verse:
                    yield id

        wordforms = self.get_wordforms(format="tokens")
        wordforms_by_number = {w: i for i,w in enumerate(wordforms)}

        rowdata = np.fromiter(row_iter(self.verses, wordforms_by_number), 'int32')
        coldata = np.fromiter(column_iter(self.verses), 'int32')
        data = np.ones(len(coldata), dtype='int32')
        sparse = coo_matrix((data,(rowdata,coldata)),dtype="int32",shape=(len(wordforms),matrix_width))

        return sparse,wordforms,wordforms_by_number
        

        
        
            
if __name__ == "__main__":
    pass
    
    
    
   
    

    
    