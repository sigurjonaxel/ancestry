import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import re

def search_mbl(query):
    url = f"https://www.mbl.is/greinasafn/leit/?q={urllib.parse.quote(query)}&category=minningargreinar"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        for article in soup.find_all('div', class_='teaser-text'):
            a = article.find('a')
            if a:
                results.append(a['href'])
        return results
    except Exception as e:
        print(f"Error searching mbl.is: {e}")
        return []

def get_article_text(url):
    if not url.startswith('http'):
        url = 'https://www.mbl.is' + url
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        content = soup.find('div', class_='article-text')
        if not content:
            content = soup.find('div', class_='news-text')
        if content:
            return content.get_text(strip=True, separator='\n')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""

print("Searching for Svana...")
svana_urls = search_mbl("Svana Sigtryggsdóttir 1953")
if svana_urls:
    print(f"Found Svana article: {svana_urls[0]}")
    text = get_article_text(svana_urls[0])
    print(text[:1000] + "...\n")

print("Searching for Sigtryggur...")
sig_urls = search_mbl("Sigtryggur Runólfsson 1921 1988")
if sig_urls:
    print(f"Found Sigtryggur article: {sig_urls[0]}")
    text = get_article_text(sig_urls[0])
    print(text[:1000] + "...")
