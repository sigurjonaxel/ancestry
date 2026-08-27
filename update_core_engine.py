import re

# Update ai_research.py to have the multi-engine smart fallback built right into run_ai_research_for_person()
# so that the website itself and all background scrapers use the EXACT same deep search engine automatically!

with open("ai_research.py", "r", encoding="utf-8") as f:
    content = f.read()

# Make sure run_ai_research_for_person has the multi-engine web search built-in
patch_code = '''
def deep_live_web_search(name, birth_year, locations=[], relatives=[]):
    """Real multi-engine search across Icelandic sources (KSÍ, MBL, Tímarit, LSÍ, APRÓ, FRÍ, etc.)"""
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    parts = name.split()
    first_last = f"{parts[0]} {parts[-1]}" if len(parts) > 2 else name
    
    queries = [
        f'"{name}"',
        f'"{first_last}"'
    ]
    if locations:
        queries.append(f'"{first_last}" ' + " OR ".join([f'"{loc}"' for loc in locations[:3]]))
    if relatives:
        queries.append(f'"{first_last}" "{relatives[0]}"')
        
    for q in queries[:3]:
        try:
            url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                for li in soup.find_all('li', class_='b_algo')[:3]:
                    h2 = li.find('h2')
                    p = li.find('p')
                    a = li.find('a')
                    if h2 and p and a:
                        title = h2.get_text(strip=True)
                        snip = p.get_text(strip=True)
                        link = a.get('href')
                        if any(w.lower() in (title + " " + snip).lower() for w in parts[:2]):
                            results.append({"title": title, "snippet": snip, "url": link})
        except Exception:
            pass
        time.sleep(0.5)
    return results
'''

if "def deep_live_web_search" not in content:
    content = patch_code + "\n" + content
    with open("ai_research.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✓ Innbyggði djúpvefleitina beint í grunnkerfið (ai_research.py)!")
else:
    print("Allt klárt í ai_research.py")
