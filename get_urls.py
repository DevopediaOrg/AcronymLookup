import csv
import json
import argparse
import requests


class WikiApiReader():
    def __init__(self, seed, recurse_depth, url_per_cat_limit):
        self.seed = seed
        self.recurse_depth = recurse_depth
        self.url_per_cat_limit = url_per_cat_limit
        self.api = 'https://en.wikipedia.org/w/api.php'
        self.data = {} # id: title

    def save_output(self, fname):
        # TODO Save inline to avoid large self.data
        with open(fname, 'w') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            for id, title in self.data.items():
                writer.writerow([title, 'https://en.wikipedia.org/?curid={}'.format(id)])

    def process_articles(self):
        if 'articles' not in self.seed:
            return

        chunk_size = 50 # 50 is the maximum api allows in one query
        for i in range(0, len(self.seed['articles']), chunk_size):
            print("Processing articles {}-{} ...".format(i, i+chunk_size-1), end=' ', flush=True)
            rsp = requests.get(self.api, params = {
                'action': 'query',
                'prop': 'info',
                'format': 'json',
                'titles': '|'.join(self.seed['articles'][i:i+chunk_size])
            })
            pages = rsp.json()['query']['pages']
            for article in pages.values():
                self.data[article['pageid']] = article['title']
            print("got {} articles.".format(len(pages)))

    def process_categories(self):
        if 'categories' not in self.seed:
            return

        for category in self.seed['categories']:
            print("Processing category {} ...".format(category), end=' ', flush=True)
            cat_data = {}
            self.recurse(cat_data, category, self.recurse_depth)
            self.data.update(cat_data)
            print("got {} articles.".format(len(cat_data)))

    def recurse(self, data, category, level):
        if level <= 0 or len(data) >= self.url_per_cat_limit:
            return

        categoryMembers = self.list_category_members(category)
        if categoryMembers == None:
            return

        for pageData in categoryMembers:
            if pageData['pageid'] not in data and pageData['pageid'] not in self.data:
                if pageData['title'][:len("Category:")] == "Category:": # a sub-category, depth-first
                    self.recurse(data, pageData['title'][len("Category:"):], level-1)
                else:
                    data[pageData['pageid']] = pageData['title']
                if len(data) >= self.url_per_cat_limit:
                    return

    def list_category_members(self, category):
        rsp = requests.get(self.api, params = {
            'action': 'query',
            'prop': 'info',
            'format': 'json',
            'list': 'categorymembers',
            'inprop':'fullurl',
            'cmtitle': 'Category:{}'.format(category),
            'cmsort':'timestamp'
            })

        rsp = rsp.json()
        try:
            result = rsp['query']['categorymembers']
        except:
            print("Skipping category due to error: ", rsp)
            result = None
        return result


if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--recursionDepth', type=int, help='number of sublevels of categories to traverse', default=3)
    parser.add_argument('--numURLs', type=int, help='approximately how many total URLs to explore', default=25000)
    args = parser.parse_args()

    with open("data/seed.json", "r") as f:
        seed = json.load(f)

    wkr = WikiApiReader(seed, args.recursionDepth, args.numURLs)
    wkr.process_articles()
    wkr.process_categories()
    wkr.save_output("data/data.csv")
