import sys
import csv
import glob
import re
from csp.main import clean_html, findContext, identifyAcronyms, ignore_sections
from postgres.dbFunctions import AcronymDatabase


def add_true_defs(db):
    with open('data/definitions.csv', 'r', encoding='ISO-8859-1') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            ret = db.addTrueDefinition(row[0], row[1].lower(), row[2])
    print ('Successfully added true definitions to database')


def add_acronyms(db):
    for fname in glob.glob("data/train/*.htm"):
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
            if db.getTrueDefinition(acronym, url) is None: # no label for definition
                continue
            aid = db.getAcronym(acronym)
            if aid is None:
                aid = db.addAcronym(acronym)
            true_definition = db.getTrueDefinition(acronym, url)
            context = findContext(acronym, rawText, i)
            did = db.addDefinition(true_definition, context, url, aid)
    print ('Successfully added acronyms to database')


if __name__ == "__main__":
    db = AcronymDatabase()
    add_true_defs(db)
    add_acronyms(db)
    db.close()
