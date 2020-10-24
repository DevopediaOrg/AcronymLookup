import csv
import random
import re
import os
import requests


def read_urls():
    urls = []
    with open('data/data.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) <= 1: continue
            title, url = row[0], row[1]
            if url:
                urls.append(url)
    return urls


def download_data(urls, savein):
    os.makedirs(savein, exist_ok=True)

    for i, url in enumerate(urls):
        if i%50 == 0:
            print("Processing URL {}-{} ...".format(i, i+49))
        rsp = requests.get(url)
        if rsp.status_code != 200:
            continue

        try:
            pfx = 'dv.' if 'devopedia.org' in url else 'wk.'
            pgid = re.sub(r'.*?(\d+)$', r'\1', url)
            with open("{}/{}{}.htm".format(savein, pfx, pgid), "w") as f:
                f.write(rsp.text)
        except Exception as e:
            print("Error in saving response", e)
            continue


if __name__== "__main__":
    urls = read_urls()
    random.seed(46798)
    random.shuffle(urls)

    train = urls[:int(0.7*len(urls))]
    test = urls[int(0.7*len(urls)):]
    print ('Size of Training Dataset:', len(train))
    print ('Size of Testing Dataset:', len(test))

    download_data(train, 'data/train')
    download_data(test, 'data/test')
