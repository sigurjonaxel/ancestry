import sys
sys.path.insert(0, '')
from advanced_scraper import search_images_via_bing, remove_icelandic_chars
name = "Snæbjörn Ómar Guðjónsson"
name_parts = [p.lower() for p in name.split() if len(p) > 2]
name_parts_clean = [remove_icelandic_chars(p) for p in name_parts]

all_results = search_images_via_bing(name, "1978")

SKIP_IMAGE_DOMAINS = [
    'youtube.com', 'youtu.be', 'vimeo.com', 'ytimg.com',
    'wikipedia.org', 'wikimedia.org', 'wikidata.org',
    'gstatic.com', 'google.com', 'bing.com',
    'squarespace.com',
]

SKIP_TITLE_KEYWORDS = [
    'video', 'youtube', 'vimeo', 'logo', 'icon', 'banner',
    'yfirlit', 'office', 'building', 'map', 'flag'
]

for img in all_results:
    img_url = img.get("image") or img.get("url")
    title = img.get("title", "")
    title_lower = title.lower()
    page_url = img.get("url", "").lower()
    img_url_lower = img_url.lower()
    
    skip_domain = False
    for d in SKIP_IMAGE_DOMAINS:
        if d in img_url_lower or d in page_url:
            skip_domain = True
            print(f"Skipped domain {d}: {img_url}")
            break
    if skip_domain: continue
    
    skip_title = False
    for k in SKIP_TITLE_KEYWORDS:
        if k in title_lower:
            skip_title = True
            print(f"Skipped title keyword {k}: {title}")
            break
    if skip_title: continue
    
    combined_clean = remove_icelandic_chars(title_lower + " " + page_url + " " + img_url_lower)
    has_first = name_parts_clean[0] in combined_clean
    has_last = name_parts_clean[-1] in combined_clean
    
    if not (has_first and has_last):
        print(f"Skipped name match (first: {has_first}, last: {has_last}): {combined_clean}")
    else:
        print(f"ACCEPTED: {title}")
