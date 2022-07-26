import copy
from enum import unique

def edits1(word):
	"All edits that are one edit away from `word`."
	letters    = 'abcdefghijklmnopqrstuvwxyz'
	splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
	deletes    = [L + R[1:]               for L, R in splits if R]
	transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
	replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
	inserts    = [L + c + R               for L, R in splits for c in letters]
	return set(deletes + transposes + replaces + inserts)

def edits2(word): 
	"All edits that are two edits away from `word`."
	return (e2 for e1 in edits1(word) for e2 in edits1(e1))

def known(words, worddictionary): 
	"The subset of `words` that appear in the dictionary of WORDS."
	return set(w for w in words if w in worddictionary)

def candidates(word, worddictionary): 
	"Generate possible spelling corrections for word."
	return set(known(edits2(word), worddictionary) or known(edits1(word), worddictionary) or [word])

def remove_number_and_special_characters(txtfilepath):
	data = open(txtfilepath, "r")
	listoflines = data.readlines()
	data.close()
	listoflines = [''.join(x for x in line.strip('\n') if (x.isalpha()) or x==' ') for line in listoflines]
	return listoflines

def remove_number_and_special_characters_from_list(listoflines):
	listoflines = [''.join(x for x in line.strip('\n') if (x.isalpha()) or x==' ') for line in listoflines]
	return listoflines

def make_kws_and_lower(listoflines):
	### takes txt file and converts every line into a list of keywords
	### returns a list of lists of lowercased keywords, i.e. list of keyphrases
	listofKPs = [kp.lower().split(' ') for kp in listoflines]
	return listofKPs

def remove_stopwords(listofKPs, dictionaryofstopwords):
	### takes output from make_kws and removes the stopwords
	for kpindex in range(len(listofKPs)):
		listofKPs[kpindex] = [kw for kw in listofKPs[kpindex] if kw not in dictionaryofstopwords]
	return listofKPs

def remove_empty_KWs(listofKPs):
	for kpindex in range(len(listofKPs)):
		listofKPs[kpindex] = [kw for kw in listofKPs[kpindex] if len(kw)!=0]
	return listofKPs

def remove_empty_KWs_and_KPs(listofKPs):
	for kpindex in range(len(listofKPs)):
		listofKPs[kpindex] = [kw for kw in listofKPs[kpindex] if len(kw)!=0]
	return [kp for kp in listofKPs if len(kp)!=0]

def add_key_phrases_to_dictionary(keyphrase, globalKPmatrix, worddictionary): # the keyphrase passed here is essentially a list of keywords associated with it.
	
	def powerset(s):
		x = len(s)
		powerset = []
		for i in range(1 << x):
			powerset.append([s[j] for j in range(x) if (i & (1 << j))])
		return [element for element in powerset if len(element)!=0]
	
	import numpy as np
	newkpstobeadded = [kp for kp in powerset(keyphrase) if len(kp)>0 and len(kp)<3]
	localkpmatrix = np.zeros((len(uniquekpstobeadded), len(uniquekpstobeadded)))
	for i in range(len(localkpmatrix)):
		for j in range(len(localkpmatrix[i])):
			localkpmatrix[i, j] = 1
			### not writing unless written pseudo code.

	# add all the KPs possible, and before importance calculation, delete all that occur only once, or less than some threshold value.

	return globalKPmatrix, worddictionary

def delete_random_kps_from_global_matrix():
	return

def add_document(dictionaryofdocuments, worddictionary, wrongworddictionary, documentID, listofKPs):
	### adds a new documents with counted words to the dictionary of documents and corrects the spellings
	if documentID in dictionaryofdocuments:
		return print('document already accounted for.')
	else:
		temporaryworddict = {}
		totalKWoccurances = 0
		for kp in listofKPs:
			for kw in kp:
				totalKWoccurances+=1
				if kw in temporaryworddict:
					temporaryworddict[kw]+=1
				else:
					temporaryworddict[kw]=1

				if kw not in worddictionary:
					worddictionary[kw] = True

		dictionaryofdocuments[documentID] = {}
		dictionaryofdocuments[documentID]['count'] = temporaryworddict
		dictionaryofdocuments[documentID]['importance'] = totalKWoccurances # doing this makes the importance as the total number of word occurances in total
																			# important for correcting spellings
		worddictionary = calculate_word_importance(dictionaryofdocuments, worddictionary)
		# dictionaryofdocuments, worddictionary, wrongworddictionary = correct_spellings(dictionaryofdocuments, worddictionary, wrongworddictionary)
		return dictionaryofdocuments, worddictionary, wrongworddictionary

def calculate_word_importance(dictionaryofdocuments, worddictionary):
	# worddictionary stores the final importances
	sumofdocumentimportance = 0

	for word in worddictionary:
		worddictionary[word] = 0

	for document in dictionaryofdocuments:
		sumofdocumentimportance += dictionaryofdocuments[document]['importance']
		totalKWoccurancesindocument = 0
		for word in dictionaryofdocuments[document]['count']:
			totalKWoccurancesindocument+=dictionaryofdocuments[document]['count'][word]
		for word in dictionaryofdocuments[document]['count']:
			worddictionary[word]+=(dictionaryofdocuments[document]['importance'])*((dictionaryofdocuments[document]['count'][word])/totalKWoccurancesindocument)
			
	for word in worddictionary:
		worddictionary[word] = worddictionary[word]/sumofdocumentimportance

	return worddictionary

# def find_wrong_words(worddictionary, wrongworddictionary):
# 	### worddictionary = {word: importance}
# 	todelete = []
# 	for word in worddictionary:
# 		topcandidate = word
# 		allcandidates = candidates(word, worddictionary)
# 		for candidate in allcandidates:
# 			if worddictionary[topcandidate]<worddictionary[candidate]:
# 				topcandidate = candidate

# 		for candidate in allcandidates:
# 			if candidate!=topcandidate:
# 				wrongworddictionary[candidate] = topcandidate
# 				if candidate not in set(todelete): # important so that a word isn't counted more than once
# 					worddictionary[topcandidate]+=worddictionary[candidate]
# 				todelete.append(candidate)

# 			# if worddictionary[word]>worddictionary[candidate] and worddictionary[candidate]>0:
# 			# 	wrongworddictionary[candidate] = word
# 			# 	worddictionary[word]+=worddictionary[candidate]
# 			# 	worddictionary[candidate] = -1 # making sure that this only counts once
# 			# 	todelete.append(candidate)
# 			# elif worddictionary[word]<worddictionary[candidate] and worddictionary[word]>0:
# 			# 	wrongworddictionary[word] = candidate
# 			# 	worddictionary[candidate]+=worddictionary[word]
# 			# 	worddictionary[word] = -1
# 			# 	todelete.append(word)
# 			# 	break
# 			# else:
# 				# pass
# 	for word in set(todelete):
# 		del worddictionary[word]

# 	return worddictionary, wrongworddictionary

# def correct_spellings(dictionaryofdocuments, worddictionary, wrongworddictionary):
# 	### takes in a dictionary of documents like
# 	### dictdoc = {doc1:{word1: noofoccurancesofword1, word2:noofoccurancesofword1, totalKWoccurances: 
# 	### totalwordoccurances}} and so on
# 	### returns a corrected dictionary of documents whith corrected spellings
# 	worddictionary, wrongworddictionary = find_wrong_words(worddictionary, wrongworddictionary)
# 	dictionarytoreturn = copy.deepcopy(dictionaryofdocuments)
# 	for document in dictionaryofdocuments:
# 		for word in dictionaryofdocuments[document]['count']:
# 			if word in worddictionary:
# 				continue
# 			elif word in wrongworddictionary:
# 				dictionarytoreturn[document]['count'][wrongworddictionary[word]] = dictionarytoreturn[document]['count'][word]
# 				del dictionarytoreturn[document]['count'][word]

# 	return dictionarytoreturn, worddictionary, wrongworddictionary