import urllib.request, urllib.parse, json, re
from bs4 import BeautifulSoup

def search_bing_html(query):
    try:
        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        for r in soup.find_all('li', class_='b_algo'):
            h2 = r.find('h2')
            p = r.find('p')
            if h2:
                title = h2.get_text().strip()
                snippet = p.get_text().strip() if p else ''
                a = h2.find('a')
                link = a['href'] if a and 'href' in a.attrs else ''
                if title:
                    results.append({'title': title, 'link': link, 'snippet': snippet})
        return results
    except Exception as e:
        print(f"Bing search error: {e}")
        return []

def search_timarit_api(name):
    try:
        url = f"https://timarit.is/api/search?q={urllib.parse.quote(name)}&size=5"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=8).read().decode('utf-8'))
        results = []
        for item in data.get('items', []):
            results.append({
                'title': f"Tímarit.is: {item.get('title', 'Grein')} ({item.get('pubDate', '')[:4]})",
                'link': f"https://timarit.is/page/{item.get('id')}",
                'snippet': item.get('snippet', '')
            })
        return results
    except Exception:
        return []

if __name__ == "__main__":
    b_res = search_bing_html('"Jóna Valdís Ólafsdóttir"')
    print(f"Bing fann {len(b_res)} niðurstöður:")
    for r in b_res:
        print(" -", r['title'], "->", r['snippet'])
