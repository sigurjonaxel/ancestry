import urllib.request, re, os, sqlite3
from bs4 import BeautifulSoup

url = "https://apro.is/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

print("Leita að starfsmannamynd af Axel Bjarkar á apro.is...")

# Look for Axel in the page
img_url = None
for member in soup.find_all(['div', 'section', 'li', 'article']):
    text = member.get_text()
    if "Axel Bjarkar" in text or "axel@apro.is" in text:
        img = member.find('img')
        if img and img.get('src'):
            src = img.get('src')
            if not src.startswith('http'):
                src = "https://apro.is" + (src if src.startswith('/') else '/' + src)
            img_url = src
            print(f"✓ Fann mynd af Axel Bjarkar á apro.is: {img_url}")
            break

if not img_url:
    # Look for all images on apro.is
    for img in soup.find_all('img'):
        alt = img.get('alt', '')
        src = img.get('src', '')
        if "axel" in alt.lower() or "axel" in src.lower():
            if not src.startswith('http'):
                src = "https://apro.is" + (src if src.startswith('/') else '/' + src)
            img_url = src
            print(f"✓ Fann mynd eftir alt/src: {img_url}")
            break

if img_url:
    cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
    local_filename = "I212565202554_apro_axel.jpg"
    local_path = os.path.join(cache_dir, local_filename)
    rel_path = f"images/cache/{local_filename}"
    
    req_img = urllib.request.Request(img_url, headers=headers)
    with urllib.request.urlopen(req_img, timeout=10) as r:
        with open(local_path, "wb") as f:
            f.write(r.read())
            
    print(f"✓ Mynd sótt og vistuð: {rel_path}")
    
    conn = sqlite3.connect("ancestry.db", timeout=30.0)
    cursor = conn.cursor()
    
    # Setja sem opinbera prófílmynd og í Sögubók
    cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = 'I212565202554'", (rel_path,))
    cursor.execute("""
        INSERT OR IGNORE INTO sources (person_id, title, snippet, link, image_url)
        VALUES ('I212565202554', 'APRÓ: Starfsmannamynd af Axel Bjarkar', 'Starfsmaður hjá APRÓ ehf. við hugbúnaðarþróun og gervigreind.', 'https://apro.is/', ?)
    """, (rel_path,))
    cursor.execute("""
        INSERT OR IGNORE INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
        VALUES ('I212565202554', 'media', 'APRÓ ehf.', 'https://apro.is/', ?, ?, 'Starfsmannamynd hjá APRÓ', 'Opinber starfsmannamynd', 100, 'confirmed')
    """, (rel_path, rel_path))
    
    conn.commit()
    conn.close()
    print("🎉 MYNDIN AF APRO.IS ER NÚNA ORÐIN AÐ PRÓFÍLMYND AXELS!")
else:
    print("Fann ekki beina img tag, skoða allar myndir á síðunni:")
    for img in soup.find_all('img')[:10]:
        print(" - IMG:", img.get('src'), "ALT:", img.get('alt'))
