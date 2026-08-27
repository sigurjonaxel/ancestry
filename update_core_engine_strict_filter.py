# Update ai_research.py to permanently ban bing search junk, danish clothes, wikipedia name articles, and foreign homonyms!

with open("ai_research.py", "r", encoding="utf-8") as f:
    content = f.read()

strict_validator = '''
def is_valid_icelandic_source(title, snippet, url):
    """Strict gatekeeper preventing any foreign clothes, wiki articles, TV shows, or junk links."""
    if not url or 'bing.com' in url or 'yahoo.com' in url:
        return False
        
    banned_keywords = [
        'axelarhús', 'modetøj', 'aarhus', 'exclusive', 'clothing', 'fashion', 
        'sjónvarpsþættir', 'tv series', 'wikipedia, frjálsa', 'turdus iliacus', 
        'skógarþröstur', 'svartþröstur', 'fuglavefur', 'afterglow', 'singer-songwriter'
    ]
    
    text = (title + " " + (snippet or "") + " " + url).lower()
    for b in banned_keywords:
        if b in text:
            return False
    return True
'''

if "def is_valid_icelandic_source" not in content:
    content = strict_validator + "\n" + content
    with open("ai_research.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✓ Innbyggði stranga síu gegn ruslheimildum í kjarnaforritið!")
