__author__="Thomas Mayer"
__date__="2014-04-22"

import reader
import collections
try:
    from scipy.sparse import lil_matrix, csc_matrix, coo_matrix, diags
    import numpy as np
except:
    pass

def cooccurrence(text1,text2):
    """Counts the frequency of cooccurrence for all wordforms in the two texts.

    :param text1: first text (dictionary of verse IDs as keys and verse texts 
            as values)
    :param text2: second text (dictionary of verse IDs as keys and verse texts 
            as values)
    """
    
    translation = collections.defaultdict(lambda: collections.defaultdict(int))
    verses1 = text1.get_verses()
    verses2 = text2.get_verses()
    
    for id,verse1 in verses1:
        #print(id,text2.verses[id])
        if id in verses2:
            words1 = list({s for s in verse1.split() if s.strip() != ''})
            words2 = list({s for s in text2[id].split() if s.strip() != ''})
            print(words1,words2)
            for word1 in words1:
                for word2 in words2:
                    translation[word1][word2] += 1
            
    return translation

class Cooccurrence():
    """Makes a scipy-based cooccurrence matrix of words from two texts together
    with an association measure (Poisson or Pearson residuals).

    :param text1: first text to be compared
    :param text2: second text to be compared
    :param method: association measure (Poisson or Pearson residuals)
    """

    def __init__(self,text1,text2,method="residuals"):

        self.text1 = text1
        self.text2 = text2

        self.matrix1,self.wf1,self.wfdict1 = text1.get_matrix()
        self.matrix2,self.wf2,self.wfdict2 = text2.get_matrix()
        
        # get common verses
        verseids1 = text1.get_verseids()
        verseids2 = text2.get_verseids()
        common_verseids = list(set(verseids1).intersection(set(verseids2)))
        
        cv = np.array(common_verseids)
        m1 = csc_matrix(self.matrix1,dtype="int32")[:,cv]
        m2 = csc_matrix(self.matrix2,dtype="int32")[:,cv]
        
        # get observed matrix
        O = m1 * m2.T
        
        # get expected matrix
        N = O.sum(1).sum()
        
        R = O.copy()
        R.data = np.ones(len(R.data))
        R.data = R.data / N
        
        Fx_old = np.array(O.sum(1)).flatten()
        Fy_old = np.array(O.sum(0)).flatten()
        
        Fx = diags(Fx_old,0)
        Fy = diags(Fy_old,0)
        
        Fx = Fx.tocsc()
        Fy = Fy.tocsc()
  
        E = Fx * R * Fy
        E = E.tocsc()

        # get association counts

        # Pearson residuals
        if method == "residuals":
            res = E.copy()
            res.data = np.ones(len(res.data))
            res.data = O.data - E.data
            res.data = res.data / np.sqrt(E.data)
            self.assoc = res

        # Pointwise Mutual Information
        elif method == "pmi":
            pmi = O.copy()
            pmi.data = np.log(O.data / E.data)
            self.assoc = pmi

        # Cramer's phi  
        elif method == "phi":
            Ezero = E.copy()
            Ezero.data = np.ones(len(Ezero.data))
            Ezero.data = Ezero.data / N
            Fxneg = Fx.copy()
            Fxneg.data = 1-Fxneg.data
            Fyneg = Fy.copy()
            Fyneg.data = 1-Fyneg.data
            Ezero = Fx * Ezero * Fy
            phi = (O - E)
            phi.data = phi.data / np.sqrt(E.data.dot(Ezero.data))
            self.assoc = phi

        # Cosine similarity
        elif method == "cosine":
            Ezero = E.copy()
            Ezero.data = np.ones(len(Ezero.data))
            Ezero.data = Ezero.data / N
            Fxneg = Fx.copy()
            Fxneg.data = 1-Fxneg.data
            Fyneg = Fy.copy()
            Fyneg.data = 1-Fyneg.data
            Ezero = Fx * Ezero * Fy
            cos = O.copy()
            cos.data = cos.data / np.sqrt(E.data * N)
            self.assoc = cos

        # Poisson as the default
        else:
            poi = E.copy()
            #poi.data = np.ones(len(poi.data))
            poi.data = np.sign(O.data - E.data) * \
                (O.data * np.log(O.data/E.data) - (O.data - E.data))
            self.assoc = poi

    def get_assoc(self,word1,word2):
        
        try:
            index1 = self.wfdict1[word1]
        except KeyError as k:
            #print("The word {} does not occur in text 1.".format(k))
            return 0
        try:
            index2 = self.wfdict2[word2]
        except KeyError as k:
            #print("The word {} does not occur in text 2.".format(k))
            return 0
        return self.assoc[index1,index2]

    def get_max(self,word1):

        m = self.assoc.tocsr()
        try:
            row = m[self.wfdict1[word1],:]
            max_index = row.indices[row.data.argmax()] if row.nnz else 0
            return self.wf2[max_index],row.data.max()
        except KeyError as k:
            print("The word {} does not occur in the text.".format(k))


if __name__ == "__main__":
#def test(): 
    print("reading text1...")
    text1 = reader.ParText("deu")
    print("reading text2...")
    text2 = reader.ParText("eng")
    print("counting cooccurrences...")
    poisson = Cooccurrence(text1,text2,method="poisson")