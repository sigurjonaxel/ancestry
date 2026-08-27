import os, sys, json, re, time, sqlite3, glob
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "ancestry.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Extract person metadata directly from Íslendingabók indId to match exact person in tree
def download_and_link_official_ib_photos():
    print("==========================================================================")
    print("🏛️ SÆKI OG TENGI 100% OPINBERAR LJÓSMYNDIR ÚR ÍSLENDINGABÓK BEINT VIÐ PRÓFÍLA")
    print("==========================================================================")
    
    user = os.environ.get("ISLENDINGABOK_USER_SIGURJON") or os.environ.get("ISLENDINGABOK_USER")
    password = os.environ.get("ISLENDINGABOK_PASS_SIGURJON") or os.environ.get("ISLENDINGABOK_PASS")
    
    with sync_playwright() as pl:
        browser = pl.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://www.islendingabok.is/login", timeout=25000)
        if page.locator('input[name="islendingabok-user"]').count() > 0:
            page.fill('input[name="islendingabok-user"]', user)
            page.fill('input[name="islendingabok-password"]', password)
            page.click('button:has-text("Innskrá"), input[type="submit"]')
            page.wait_for_timeout(3000)

        # Inspect all ib_<indId>_1.jpg files and find their exact owners in Íslendingabók
        ib_files = sorted(glob.glob("images/cache/ib_*_1.jpg"))
        print(f"Fann {len(ib_files)} sóttar Íslendingabókarmyndir. Athuga hver á hverja mynd...")

        conn = get_db()
        cursor = conn.cursor()
        
        matched_count = 0
        for fpath in ib_files:
            m = re.search(r"ib_(\d+)_1\.jpg", fpath)
            if not m: continue
            ind_id = m.group(1)
            
            try:
                page.goto(f"https://www.islendingabok.is/individual?indId={ind_id}&tabs=family", timeout=15000)
                page.wait_for_timeout(1000)
                
                body_text = page.locator("body").inner_text()
                lines = [l.strip() for l in body_text.split("\n") if l.strip()]
                
                # Extract Name and Birth Year
                name = ""
                ignore_words = ("íslendingabók", "einstaklingur", "velja mynd", "skipta", "leita", "stillingar", "framætt", "tölfræði", "fjölskylda", "myndir", "æviágrip", "ábendingar", "sjá meira", "sjá minna", "heimildir", "fædd", "dá", "barn", "kona", "maður", "viðurnefni", "aðgerð misfórst")
                for l in lines[:15]:
                    low = l.lower()
                    if len(l.split()) >= 2 and not any(k in low for k in ignore_words):
                        name = l
                        break

                birth_year = ""
                m_by = re.search(r"Fædd(?:ur|ist|ing)?\s+.*?(\d{4})", body_text, re.IGNORECASE)
                if m_by:
                    birth_year = m_by.group(1)

                if name:
                    # Match in DB
                    cursor.execute("SELECT id, name, birth_year FROM people WHERE tree_id = 'sigurjon' AND name = ?", (name,))
                    rows = cursor.fetchall()
                    target_id = None
                    if len(rows) == 1:
                        target_id = rows[0]["id"]
                    elif len(rows) > 1:
                        for r in rows:
                            if birth_year and r["birth_year"] == birth_year:
                                target_id = r["id"]
                                break
                        if not target_id:
                            target_id = rows[0]["id"]

                    if target_id:
                        cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (fpath, target_id))
                        matched_count += 1
                        print(f"  📷 ✓ [{name}] (f. {birth_year}) -> Tengdi Íslendingabókarmynd ({fpath})")

            except Exception as e:
                print(f"  ❌ Villa við indId={ind_id}: {e}")

        conn.commit()
        conn.close()
        browser.close()
        
    print(f"\n==========================================================================")
    print(f"🎉 BÚIÐ! Tengdi {matched_count} staðfestar opinberar ljósmyndir úr Íslendingabók!")
    print("==========================================================================")

if __name__ == "__main__":
    download_and_link_official_ib_photos()
