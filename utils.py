from sklearn.feature_extraction import text, DictVectorizer


def features(cad, tokenize, true_defs):
    acronym = cad[0]
    context = cad[1]
    if len(cad) == 3: true_defs.append(cad[2])
    terms = tokenize(context)
    d = {acronym: 10}
    for t in terms:
        if t not in text.ENGLISH_STOP_WORDS:
            d[t] = d.get(t, 0) + 1
    return d


