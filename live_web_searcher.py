import urllib.request, urllib.parse, re
from bs4 import BeautifulSoup

def perform_live_web_search(name, extra_keywords=""):
    """
    Independent live web searcher that fetches real-time web news, 
    education, hospital, sports and government sources without hitting API rate limits or Captcha.
    """
    clean_name = name.strip()
    query = f'"{clean_name}" {extra_keywords}'.strip()
    
    search_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        search_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    results = []
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='algo')
        
        for it in items:
            h3 = it.find('h3')
            if not h3: continue
            title = h3.get_text().strip()
            
            # Find real link
            a_tag = h3.find('a')
            raw_link = a_tag['href'] if a_tag and 'href' in a_tag.attrs else ''
            
            # Extract real URL from Yahoo redirect if present
            real_url = raw_link
            m_ru = re.search(r"/RU=([^/]+)/", raw_link)
            if m_ru:
                try:
                    real_url = urllib.parse.unquote(m_ru.group(1))
                except Exception:
                    pass
                    
            p_tag = it.find('div', class_='compText') or it.find('p')
            snippet = p_tag.get_text().strip() if p_tag else ''
            
            # Verification: make sure the search result relates to the person or family
            if title and (clean_name.lower() in title.lower() or clean_name.lower() in snippet.lower()):
                results.append({
                    'title': title,
                    'link': real_url,
                    'snippet': snippet
                })
                
    except Exception as e:
        print(f"[Live Web Searcher] Error fetching results for {name}: {e}")
        
    return results

if __name__ == "__main__":
    test_res = perform_live_web_search("Jóna Valdís Ólafsdóttir")
    print(f"Fann {len(test_res)} staðfestar greinar fyrir Jónu Valdísi:")
    for r in test_res:
        print(" 📄 Titill:", r['title'])
        print(" 🔗 Slóð:", r['link'])
        print(" 📝 Útdráttur:", r['snippet'])
        print()
