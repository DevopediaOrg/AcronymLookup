import sys
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from csp.main import clean_html, findContext, identifyAcronyms, ignore_sections
from utils import features


def predict(txt, model, tokenize, vect):
    txt = ' {}'.format(txt)
    rawText = clean_html(txt)
    if not rawText:
        return None

    acronyms = identifyAcronyms(rawText)
    data = []
    defs = []
    for acronym, i in acronyms:
        context = findContext(acronym, rawText, i)
        data.append((acronym,context))
    featureVect = vect.transform(features(d, tokenize, defs) for d in data)
    predicted = model.predict(featureVect)
    results = []
    for train, definition in zip(data, predicted):
        results.append('{} => {}'.format(train[0], definition))
    return {'results': results}


clf, txt = sys.argv[1], sys.argv[2]
model = joblib.load('trained-models/{}.pkl'.format(clf))
vect = joblib.load('trained-models/vectorizer.pkl')
tokenize = CountVectorizer().build_tokenizer()

predicted = predict(txt, model, tokenize, vect)
print(predicted)
