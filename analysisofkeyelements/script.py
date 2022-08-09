import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
import numpy

paragraphs = pd.read_pickle('/Users/chinmayshrivastava/Desktop/OSCA/V4.0/scraping/paragraphsfromhnandbc101.pickle')

paragraphsvectorizer = CountVectorizer(analyzer='word', ngram_range=(1, 1))
docs = list(paragraphs['text'])
X2 = paragraphsvectorizer.fit_transform(docs)
countmatrixP = X2.toarray()

numpy.savetxt('countP.txt', countmatrixP, delimiter=',')
del countmatrixP