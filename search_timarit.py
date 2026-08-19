import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re

def search_timarit(query):
    url = f"https://timarit.is/search?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        for a in soup.find_all('a', href=True):
            if '/page/' in a['href']:
                results.append(a['href'])
        return list(set(results))
    except Exception as e:
        print(f"Error searching timarit.is: {e}")
        return []

print(search_timarit("Sigtryggur Runólfsson 1988"))
