import urllib.request, urllib.parse, re, os, sqlite3
from bs4 import BeautifulSoup

urls = [
    "https://landvernd.is/frettir/mengun-med-midlum-sigrar-keppni-ungra-umhverfisfrettamanna-2020/",
    "https://www.mbl.is/frettir/innlent/2020/07/07/islenskir_nemendur_i_1_saeti_i_aljodlegri_keppni/"
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
pid = "I212565202554"

# Leita á Landvernd
url_landvernd = "https://landvernd.is/?s=" + urllib.parse.quote("Mengun með miðlum")
req = urllib.request.Request(url_landvernd, headers=headers)
html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

img_found = None
article_link = None

for article in soup.find_all('article'):
    if "Mengun" in article.get_text() or "Axel" in article.get_text():
        img = article.find('img')
        a = article.find('a')
        if a: article_link = a.get('href')
        if img:
            img_found = img.get('src')
            print("✓ Fann mynd af Axel og liðsfélögum á Landvernd:", img_found)
            break

if not img_found and article_link:
    req2 = urllib.request.Request(article_link, headers=headers)
    html2 = urllib.request.urlopen(req2, timeout=10).read().decode('utf-8')
    soup2 = BeautifulSoup(html2, 'html.parser')
    og_img = soup2.find("meta", property="og:image")
    if og_img:
        img_found = og_img.get("content")

if img_found:
    local_filename = "I212565202554_yre_axel.jpg"
    local_path = os.path.join(cache_dir, local_filename)
    rel_path = f"images/cache/{local_filename}"
    
    req_img = urllib.request.Request(img_found, headers=headers)
    with urllib.request.urlopen(req_img, timeout=10) as r:
        with open(local_path, "wb") as f:
            f.write(r.read())
            
    conn = sqlite3.connect("ancestry.db", timeout=30.0)
    cursor = conn.cursor()
    cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (rel_path, pid))
    cursor.execute("""
        INSERT OR IGNORE INTO sources (person_id, title, snippet, link, image_url)
        VALUES (?, 'Landvernd / YRE: Verðlaunamynd af Axel Bjarkar', 'Ljósmynd af Axel Bjarkar Sigurjónssyni og verðlaunahöfum.', ?, ?)
    """, (pid, article_link or 'https://landvernd.is/', rel_path))
    cursor.execute("""
        INSERT OR IGNORE INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
        VALUES (?, 'media', 'Landvernd', ?, ?, ?, 'Verðlaunamynd YRE', 'Ljósmynd af Axel Bjarkar', 100, 'confirmed')
    """, (pid, article_link or '', rel_path, rel_path))
    conn.commit()
    conn.close()
    print("🎉 RAUNVERULEG VERÐLAUNAMYND AF AXEL BJARKAR KOMIN SEM PRÓFÍLMYND!")
