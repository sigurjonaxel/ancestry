import os, sys, json, re, time, sqlite3, glob, hashlib, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "ancestry.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_login(page):
    user = os.environ.get("ISLENDINGABOK_USER_SIGURJON") or os.environ.get("ISLENDINGABOK_USER")
    password = os.environ.get("ISLENDINGABOK_PASS_SIGURJON") or os.environ.get("ISLENDINGABOK_PASS")
    page.goto("https://www.islendingabok.is/login", timeout=25000)
    if page.locator('input[name="islendingabok-user"]').count() > 0:
        page.fill('input[name="islendingabok-user"]', user)
        page.fill('input[name="islendingabok-password"]', password)
        page.click('button:has-text("Innskrá"), input[type="submit"]')
        page.wait_for_timeout(3000)

def search_and_fetch_photo(page, p):
    name = p['name']
    birth_year = p['birth_year'] or ''
    pid = p['id']
    
    # If person already has verified avatar, skip
    if p['avatar_url'] and p['avatar_verified']:
        return None

    try:
        page.goto("https://www.islendingabok.is/search", timeout=15000)
        search_query = f'"{name}"' if len(name.split()) >= 2 else name
        page.fill('input[name="find"], input[type="search"]', search_query)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        
        if page.locator("text=Sjá nánar").count() == 0:
            return None
            
        page.locator("text=Sjá nánar").first.click()
        page.wait_for_timeout(2000)
        
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for images on individual page
        # In Íslendingabók, photo is under /photo?indId=... or img tags with class/alt
        photo_url = None
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if "photo" in src or "mynd" in src.lower() or "individual" in src:
                if not any(x in src.lower() for x in ["logo", "merki", "icon", "flag", "banner"]):
                    photo_url = src
                    break
                    
        if not photo_url:
            # Check if there is an <a> tag pointing to Myndir
            for a in soup.find_all("a", href=True):
                if "tabs=photos" in a["href"] or "myndir" in a.text.lower():
                    page.goto(f"https://www.islendingabok.is/{a['href'].lstrip('/')}", timeout=10000)
                    page.wait_for_timeout(1500)
                    p_soup = BeautifulSoup(page.content(), "html.parser")
                    for img in p_soup.find_all("img"):
                        src = img.get("src", "")
                        if "photo" in src and not "logo" in src:
                            photo_url = src
                            break
                    break

        if photo_url:
            if not photo_url.startswith("http"):
                photo_url = f"https://www.islendingabok.is/{photo_url.lstrip('/')}"
                
            cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            clean_id = pid.replace('@', '')
            out_file = f"{clean_id}_ib_portrait.jpg"
            out_path = os.path.join(cache_dir, out_file)
            rel_path = f"images/cache/{out_file}"
            
            # Download using playwright browser session to maintain auth cookies
            img_bytes = page.request.get(photo_url).body()
            if len(img_bytes) > 1500: # Real image
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                    
                conn = get_db()
                conn.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (rel_path, pid))
                conn.commit()
                conn.close()
                print(f"  📷 [FANN MYND!] Tengdi nýja staðfesta ljósmynd við {name} ({pid})!")
                return rel_path
    except Exception as e:
        print(f"  ❌ Villa við {name}: {e}")
    return None

def main():
    conn = get_db()
    cursor = conn.cursor()
    people_missing_photos = cursor.execute("""
        SELECT id, tree_id, name, birth_year, avatar_url, avatar_verified 
        FROM people 
        WHERE tree_id = 'sigurjon' 
        AND (avatar_url IS NULL OR avatar_verified = 0)
        ORDER BY 
            CASE 
                WHEN birth_year != '' AND CAST(birth_year AS INTEGER) >= 1850 THEN 0
                ELSE 1
            END,
            birth_year DESC
    """).fetchall()
    conn.close()
    
    print(f"🔎 Athuga myndir á Íslendingabók fyrir {len(people_missing_photos)} einstaklinga sem vantar prófílmynd...")
    
    with sync_playwright() as pl:
        browser = pl.chromium.launch(headless=True)
        page = browser.new_page()
        ensure_login(page)
        
        found_count = 0
        for idx, p in enumerate(people_missing_photos[:80]):
            res = search_and_fetch_photo(page, dict(p))
            if res:
                found_count += 1
            if (idx + 1) % 10 == 0:
                print(f"--- Skannað: {idx+1}/80 einstaklingar ({found_count} nýjar myndir fundust) ---")
                
        browser.close()
    print(f"\n🎉 Skönnun lokið! Fann og tengdi {found_count} nýjar prófílmyndir úr Íslendingabók.")

if __name__ == "__main__":
    main()
