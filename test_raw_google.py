import sys
sys.path.insert(0, '')
from advanced_scraper import search_images_via_raw_google
res = search_images_via_raw_google("Snæbjörn Ómar Guðjónsson", "1978")
print(f"Found: {len(res)}")
