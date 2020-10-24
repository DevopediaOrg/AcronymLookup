import sys
import pickle
import joblib
import os
import re
import glob
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GridSearchCV
from sklearn import tree, metrics, svm
from sklearn.ensemble import RandomForestClassifier
from database.wrapper import AcronymDatabase
from csp.main import clean_html, findContext, identifyAcronyms, ignore_sections
from utils import features


def train_naivebayes(X_train, true_defs, classifiers):
    params = [{'alpha': [0.01, 0.1, 0.5, 1]}]

    clf = GridSearchCV(estimator=MultinomialNB(), param_grid=params, n_jobs=-1, cv=2).fit(X_train, true_defs)
    print('Best alpha:', clf.best_estimator_.alpha)

    classifiers['MultinomialNB'] = MultinomialNB(alpha=clf.best_estimator_.alpha).fit(X_train, true_defs)

    pickle.dump(classifiers['MultinomialNB'], open('trained-models/naivebayes.pkl', "wb"))


def train_svc(X_train, true_defs, classifiers):
    params = [
        {
            'C': [1],
            'gamma': [0.001, 0.0001]
        }
    ]

    clf = GridSearchCV(estimator=svm.SVC(), param_grid=params, n_jobs=-1).fit(X_train, true_defs)
    print('Best C:', clf.best_estimator_.C) 
    print('Best Kernel:', clf.best_estimator_.kernel)
    print('Best Gamma:', clf.best_estimator_.gamma)

    classifiers['LinearSVC'] = svm.LinearSVC(C=clf.best_estimator_.C).fit(X_train, true_defs)

    pickle.dump(classifiers['LinearSVC'], open('trained-models/svc.pkl', "wb"))


def train_decisiontree(X_train, true_defs, classifiers):
    params = [
        {
            "max_depth": [3, None],
            "max_features": [1, 2, None],
            "min_samples_leaf": [1, 2, 3],
            "criterion": ["gini", "entropy"]
        }
    ]

    clf = GridSearchCV(estimator=tree.DecisionTreeClassifier(), param_grid=params, n_jobs=-1).fit(X_train, true_defs)
    print('Best Max Depth:', clf.best_estimator_.max_depth) 
    print('Best Max Features:', clf.best_estimator_.max_features)
    print('Best Min Samples:', clf.best_estimator_.min_samples_leaf)
    print('Best Criterion:', clf.best_estimator_.criterion)

    classifiers['DecisionTreeClassifier'] = \
        tree.DecisionTreeClassifier(min_samples_leaf=clf.best_estimator_.min_samples_leaf).fit(X_train, true_defs)

    pickle.dump(classifiers['DecisionTreeClassifier'], open('trained-models/decisiontree.pkl', "wb"))


def train_randomforest(X_train, true_defs, classifiers):
    classifiers['RandomForestClassifier'] = RandomForestClassifier().fit(X_train, true_defs)

    pickle.dump(classifiers['RandomForestClassifier'], open('trained-models/randomforest.pkl', "wb"))


def train_and_predict(what, tokenize, vect):

    if what == 'test':
        data_y_true = joblib.load('train.y.pkl'.format(what))

    if os.path.exists('{}.x.pkl'.format(what)) and os.path.exists('{}.y.pkl'.format(what)):
        data_x = joblib.load('{}.x.pkl'.format(what))
        data_y = joblib.load('{}.y.pkl'.format(what))
    else:
        data_x = []
        data_y = []
        for fname in glob.glob("data/{}/*.htm".format(what)):
            if 'dv.' in fname:
                url = 'https://devopedia.org/{}'.format(re.sub(r'.*\.(\d+)\.htm', r'\1', fname))
            else:
                url = 'https://en.wikipedia.org/?curid={}'.format(re.sub(r'.*\.(\d+)\.htm', r'\1', fname))

            with open(fname, "r") as f:
                html = f.read()

            rawText = clean_html(html)
            rawText = ignore_sections(rawText)
            if not rawText:
                continue

            acronyms = identifyAcronyms(rawText)
            for acronym, i in acronyms:
                if db.getTrueDefinition(acronym, url) is None:
                    continue
                if what == 'test' and db.getTrueDefinition(acronym, url) not in data_y_true:
                    continue
                context = findContext(acronym, rawText, i)
                data_x.append((acronym, context))
                data_y.append(db.getTrueDefinition(acronym, url))

        joblib.dump(data_x, '{}.x.pkl'.format(what))
        joblib.dump(data_y, '{}.y.pkl'.format(what))

    # On training set, we would have perfect prediction
    X_new_counts = vect.transform(features(d, tokenize, true_defs) for d in data_x)
    for cname, classifier in classifiers.items():
        predicted = classifier.predict(X_new_counts)
        print(cname, metrics.precision_recall_fscore_support(data_y, predicted, average='weighted'))
        #for train, definition, true in zip(data_x, predicted, data_y):
        #    if true != definition:
        #        print('%s => %s, %s'.format(train[0], definition, true))
        #print(cname, metrics.classification_report(data_y, predicted))


if __name__ == "__main__":
    db = AcronymDatabase()
    tokenize = CountVectorizer().build_tokenizer()
    true_defs = []

    cadList = db.getContextAcronymList()
    vect = DictVectorizer()
    X_train = vect.fit_transform(features(d, tokenize, true_defs) for d in cadList)
    os.makedirs('trained-models', exist_ok=True)
    joblib.dump(vect, 'trained-models/vectorizer.pkl')

    classifiers = {}
    train_naivebayes(X_train, true_defs, classifiers)
    train_svc(X_train, true_defs, classifiers)
    train_decisiontree(X_train, true_defs, classifiers)
    train_randomforest(X_train, true_defs, classifiers)

    print("Training...")
    train_and_predict('train', tokenize, vect)

    print("Validating...")
    train_and_predict('test', tokenize, vect)
