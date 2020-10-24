
import csv
import re
import operator
import glob
from .csp import CSP, BacktrackingSearch


# solveCSP() - given an |acronym| and |text| which
# gives the context of the acronym (but does not include
# the acronym itself, solve a constraint satisfaction
# problem.
# constraints (required):
#  - matched words in long form must be sequential
# factors (good to have):
#  - characters matching acronym are upper case
#  - characters matching acronyms are the first in the word
def solveCSP(acronym, text, threshold=1000):
    csp = CSP()

    for idx, char in enumerate(acronym):
        variableName = (idx, char)

        # create the domain
        # word is a string representing the word the variable corresponds to
        # wordIdx gives the index of the word in the text
        # charIdx gives the index of the character being matched in the word
        domain = []
        for wordIdx, word in enumerate(text):
            indices = [i for i, letter in enumerate(word) if letter.lower() == char.lower()]
            for charIdx in indices:
                domain.append((word, wordIdx, charIdx))
    
        csp.add_variable(variableName, domain)
        def is_first_char(candidateWord,_,index):
            if index == 0:
                return 10
            else:
                return 1
        csp.add_unary_factor(variableName, is_first_char)
        def is_upper(candidateWord,_,index):
            if candidateWord[index].isupper():
                return 10
            else:
                return 1
        csp.add_unary_factor(variableName, is_upper)

    for idx in range(len(acronym)-1):
        var1 = (idx, acronym[idx])
        var2 = (idx+1, acronym[idx+1])
        def is_after(var1, var2):
            _,firstWordIdx,_ = var1
            _,secondWordIdx,_ = var2
        
            if secondWordIdx >= firstWordIdx:
                return 1
            else:
                return 0
        csp.add_binary_factor(var1, var2, is_after)

    search = BacktrackingSearch()
    search.solve(csp, True, True)

    if search.optimalWeight >= threshold:
        return extractDefinition(text, search.optimalAssignment)
    else:
        return None


# given the optimal assignment, re-create the definition
# Note: this automatically includes all interim words
# (ideally "and", "the" etc.)
def extractDefinition(text, assignment):
    startIdx = assignment[min(assignment)][1]
    endIdx = assignment[max(assignment)][1]
    definition = text[startIdx:endIdx+1]
    return " ".join(definition)


# findDefinition() - given an |acronym|, the |text| containing
# the acronym, and the |index| at which the acronym was found
# in the text, find the appropriate definition for the acronym
def findDefinition(acronym, text, index):
    startIdx = index-10 if index-10 >=0 else 0
    endIdx = index+10 if index+10 <= len(text) else len(text)
    
    window = text[startIdx:index]
    leftSide = solveCSP(acronym, window)
    window = text[index+1:endIdx]
    rightSide = solveCSP(acronym, window)

    # prefer definition (acronym) format in case of a "tie"
    return leftSide if leftSide else rightSide


def clean_html(html):
    # First we remove inline JavaScript/CSS:
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
    # Then we remove html comments. This has to be done before removing regular
    # tags since comments can contain '>' characters.
    cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
    # Next we can remove the remaining tags:
    cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
    # Finally, we deal with whitespace
    cleaned = re.sub(r"&nbsp;", " ", cleaned)
    cleaned = re.sub(r"  ", " ", cleaned)
    cleaned = re.sub(r"  ", " ", cleaned)
    return [''] + cleaned.strip().split() # add null start to overcome indexing error elsewhere


def ignore_sections(rawText):
    footerIndices = [i for i, x in enumerate(rawText) if x.lower()=='references']
    headerIndices = [i for i, x in enumerate(rawText) if x.lower()=='abstract']
    if len(footerIndices) > 0:
        return rawText[:max(footerIndices)] # remove extraneous information
    if len(headerIndices) > 0:
        return rawText[max(headerIndices):] # remove extraneous information


def identifyAcronyms(rawText):
    acronyms = []
    #words commonly misidentified as acronyms are manually blacklisted
    blacklist = ['ABSTRACT', 'INTRODUCTION', 'CONCLUSION', 'CONCLUSIONS', 'ACKNOWLEDGEMENTS', 'RESULTS']
    for i in range(1,len(rawText)-1):
        word = rawText[i]
        word = re.sub(r'[^\w\s]','',word)
        '''
        characteristics of an acronym: all capital letters, length > 2,
        contains only alphabet characters, not in blacklist, and not part
        of a header (identified by determining if surrounding words are in all-caps)
        '''
        nextIndex = i+1
        prevIndex = i-1
        if len(word)>2 and word[:-1].isupper() and word.isalpha() \
           and word not in blacklist and not rawText[i-1].isupper() \
           and not rawText[i+1].isupper():
            acronyms.append((word, i))    
    return acronyms


def findContext(acronym, rawText, i):
    startIndex=i-15
    if i-10 < 0: startIndex = 0
    endIndex = i+15 
    if i+10 > len(rawText): endIndex = len(rawText)-1
    context = []
    for word in rawText[startIndex:endIndex+1]:
        word = word.lower()
        word = "".join(re.findall("[a-zA-Z]+", word))
        if len(word)==0 or word==acronym.lower(): continue
        context.append(word)
    return " ".join(context)


if __name__ == "__main__":
    data = []
    for fname in glob.glob("../data/train/*.htm"):
        with open(fname, "r") as f:
            html = f.read()

        rawText = clean_html(html)
        rawText = ignore_sections(rawText)
        if not rawText:
            continue

        currentAcronymDefs = {} # local database links acronym text to definitions (file-specific)
        acronyms = identifyAcronyms(rawText) # list of all acronyms and corresponding index in rawtext
        for acronym, i in acronyms:
            if acronym not in currentAcronymDefs:
                definition = findDefinition(acronym, rawText, i)
                if definition:
                    currentAcronymDefs[acronym] = (definition, " ".join(rawText[i-10:i+10]))

        for ac in currentAcronymDefs:
            data.append([ac, currentAcronymDefs[ac][0], fname, currentAcronymDefs[ac][1]])

    with open('../data/defs.csv', 'w') as csvfile: # TODO Save to definitions.csv
        writer = csv.writer(csvfile)
        writer.writerows(data)
