import sys
import urllib.parse
from bs4 import BeautifulSoup
import json
import time

try:
    import cloudscraper
except ImportError:
    print("Please install cloudscraper: .venv/bin/pip install cloudscraper beautifulsoup4 lxml")
    sys.exit(1)

def scrape_mbl(scraper, query):
    url = f"https://www.mbl.is/greinasafn/leit/?q={urllib.parse.quote(query)}&category=minningargreinar"
    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        for article in soup.find_all('div', class_='teaser-text'):
            a = article.find('a')
            if a:
                results.append('https://www.mbl.is' + a['href'] if not a['href'].startswith('http') else a['href'])
        return results
    except Exception as e:
        print(f"Error searching mbl.is for {query}: {e}")
        return []

def get_article_text(scraper, url):
    try:
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        content = soup.find('div', class_='article-text')
        if not content:
            content = soup.find('div', class_='news-text')
        if content:
            return content.get_text(strip=True, separator='\n')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""

def main():
    queries = [
        "Sveinn Unnsteinn Jónsson 1944",
        "Sigtryggur Runólfsson 1921 1988",
        "Guðbjörg Sigurpálsdóttir 1926 2014",
        "Svana Sigtryggsdóttir 1953 2020",
        "Ingólfur Árni Sveinsson 1947 2002",
        "Lilja Árnadóttir 1926 2006",
        "Loftur Jóhannsson 1923 2011"
    ]
    
    scraper = cloudscraper.create_scraper()
    results_db = {}
    
    print("Byrja að skrapa minningargreinar af mbl.is...")
    
    for q in queries:
        print(f"\nLeita að: {q}")
        urls = scrape_mbl(scraper, q)
        if not urls:
            print("Engin grein fannst.")
            continue
            
        print(f"Fann {len(urls)} greinar, sæki þá fyrstu: {urls[0]}")
        text = get_article_text(scraper, urls[0])
        
        if text:
            print(f"Búið að sækja texta ({len(text)} stafir).")
            # Save snippet for preview
            preview = text[:200].replace('\n', ' ') + '...'
            print(f"Brot: {preview}")
            results_db[q] = {
                'url': urls[0],
                'text': text
            }
        
        # Vertu kurteis við vefþjóninn
        time.sleep(2)
        
    with open('scraped_obituaries.json', 'w', encoding='utf-8') as f:
        json.dump(results_db, f, ensure_ascii=False, indent=2)
        
    print("\nLokið! Gögnin voru vistuð í scraped_obituaries.json")

if __name__ == "__main__":
    main()
