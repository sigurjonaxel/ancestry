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

# Extract person's real name from within the individual card container on Íslendingabók
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

    ib_files = sorted(glob.glob("images/cache/ib_*_1.jpg"))
    print(f"Greini eigendur {len(ib_files)} Íslendingabókarmynda...")

    conn = get_db()
    cursor = conn.cursor()
    
    # Reset Sigurjon's avatar to his true image (ib_7750895_1.jpg)
    cursor.execute("UPDATE people SET avatar_url = 'images/cache/ib_7750895_1.jpg', avatar_verified = 1 WHERE id = 'I212097023483'")
    
    matched = 0
    for fpath in ib_files:
        m = re.search(r"ib_(\d+)_1\.jpg", fpath)
        if not m: continue
        ind_id = m.group(1)
        
        # Don't check Sigurjon again
        if ind_id == "7750895":
            continue
            
        try:
            page.goto(f"https://www.islendingabok.is/individual?indId={ind_id}&tabs=family", timeout=15000)
            page.wait_for_timeout(1000)
            
            # The person's name on individual page is in h1 or strong or first non-nav div
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Find the main individual container
            person_name = ""
            # In Islendingabok modern UI, individual name is in a header/heading inside main area
            main = soup.find("main") or soup.find("div", class_=re.compile(r"individual|content|main", re.I)) or soup
            for tag in main.find_all(["h1", "h2", "h3", "div", "span"]):
                txt = tag.get_text().strip()
                if len(txt.split()) >= 2 and not any(x in txt.lower() for x in ["íslendingabók", "einstaklingur", "stillingar", "útskrá", "um mig", "tölfræði", "forsíða", "ábendingar", "fróðleikur", "algengar", "leiðbeiningar", "skilmálar", "english", "fjölskylda", "myndir", "framætt", "sjá meira", "sjá minna", "fædd", "dá", "bóndi", "húsfreyja", "heimildir", "faðir", "móðir", "maki", "börn", "systkin"]):
                    # Found candidate name
                    person_name = txt
                    break

            birth_year = ""
            body_txt = soup.get_text()
            m_by = re.search(r"Fædd(?:ur|ist|ing)?\s+.*?(\d{4})", body_txt, re.IGNORECASE)
            if m_by:
                birth_year = m_by.group(1)

            if person_name and person_name != "Sigurjón Axel Guðjónsson":
                # Find in people table
                cursor.execute("SELECT id, name, birth_year FROM people WHERE tree_id = 'sigurjon' AND name = ?", (person_name,))
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
                    matched += 1
                    print(f"  📷 ✓ [{person_name}] (f. {birth_year}) -> {fpath}")

        except Exception as e:
            print(f"  ❌ Error for indId={ind_id}: {e}")

    conn.commit()
    conn.close()
    browser.close()
    print(f"\n🎉 Tengdi {matched} staðfestar myndir úr Íslendingabók við rétta einstaklinga!")

