import os, sys, json, re, sqlite3, glob
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "ancestry.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

user = os.environ.get("ISLENDINGABOK_USER_SIGURJON") or os.environ.get("ISLENDINGABOK_USER")
password = os.environ.get("ISLENDINGABOK_PASS_SIGURJON") or os.environ.get("ISLENDINGABOK_PASS")

with sync_playwright() as pl:
    browser = pl.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.islendingabok.is/login", timeout=25000)
    page.fill('input[name="islendingabok-user"]', user)
    page.fill('input[name="islendingabok-password"]', password)
    page.click('button:has-text("Innskrá"), input[type="submit"]')
    page.wait_for_timeout(3000)

    conn = get_db()
    cursor = conn.cursor()
    people = cursor.execute("""
        SELECT id, tree_id, name, birth_year, avatar_url, avatar_verified 
        FROM people 
        WHERE tree_id = 'sigurjon'
        ORDER BY 
            CASE 
                WHEN birth_year != '' AND CAST(birth_year AS INTEGER) >= 1800 THEN 0
                ELSE 1
            END,
            birth_year DESC
    """).fetchall()

    print(f"🏛️ Leita að opinberum ljósmyndum á Íslendingabók fyrir {len(people)} einstaklinga...")

    found_portraits = 0
    cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
    os.makedirs(cache_dir, exist_ok=True)

    for idx, p in enumerate(people[:50]):
        name = p['name']
        birth_year = p['birth_year'] or ''
        pid = p['id']

        try:
            page.goto("https://www.islendingabok.is/search", timeout=15000)
            search_query = f'"{name}"' if len(name.split()) >= 2 else name
            page.fill('input[name="find"], input[type="search"]', search_query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1800)

            if page.locator("text=Sjá nánar").count() == 0:
                continue

            page.locator("text=Sjá nánar").first.click()
            page.wait_for_timeout(1800)

            # Check if there is an image with src matching /image/2/
            soup = BeautifulSoup(page.content(), "html.parser")
            
            # Look for image tags starting with /image/ or image/
            cand_img_urls = []
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if "/image/" in src or "image/2/" in src:
                    if not src.startswith("http"):
                        src = f"https://www.islendingabok.is/{src.lstrip('/')}"
                    cand_img_urls.append(src)

            if cand_img_urls:
                # The portrait of the main individual is the primary image URL
                chosen_url = cand_img_urls[0]
                img_bytes = page.request.get(chosen_url).body()
                if len(img_bytes) > 2500: # Real JPEG portrait
                    clean_id = pid.replace('@', '')
                    out_file = f"{clean_id}_ib_portrait.jpg"
                    out_path = os.path.join(cache_dir, out_file)
                    with open(out_path, "wb") as f:
                        f.write(img_bytes)
                        
                    rel_path = f"images/cache/{out_file}"
                    cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (rel_path, pid))
                    conn.commit()
                    found_portraits += 1
                    print(f"  📷 [{found_portraits}] ✓ [{name}] (f. {birth_year}) -> Sótti og tengdi opinbera mynd ({out_file})!")

        except Exception as e:
            print(f"  ❌ Error on {name}: {e}")

    conn.close()
    browser.close()
    print(f"\n🎉 LOKIÐ! Sótti og tengdi {found_portraits} staðfestar ljósmyndir beint úr Íslendingabók!")

