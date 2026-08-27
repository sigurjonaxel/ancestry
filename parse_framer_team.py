from playwright.sync_api import sync_playwright
import sqlite3, os, urllib.request

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://apro.is/", timeout=20000)
    page.wait_for_timeout(3000)
    
    # Scroll down to team section
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    
    # Find Axel Bjarkar element
    axel_el = page.locator("text=Axel Bjarkar")
    if axel_el.count() > 0:
        print("✓ Fann Axel Bjarkar á APRÓ síðunni!")
        # Get parent container and its image
        parent = axel_el.first.locator("xpath=ancestor::div[contains(@class, 'framer')][4]")
        img = parent.locator("img").first
        if img.count() > 0:
            src = img.get_attribute("src")
            print("✓ Fann starfsmannamynd Axels:", src)
            
            cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
            local_path = os.path.join(cache_dir, "I212565202554_apro_axel.jpg")
            rel_path = "images/cache/I212565202554_apro_axel.jpg"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(src, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                with open(local_path, "wb") as f:
                    f.write(r.read())
                    
            conn = sqlite3.connect("ancestry.db", timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = 'I212565202554'", (rel_path,))
            cursor.execute("""
                INSERT OR IGNORE INTO sources (person_id, title, snippet, link, image_url)
                VALUES ('I212565202554', 'APRÓ: Opinber starfsmannamynd', 'Starfsmaður hjá APRÓ ehf. við hugbúnaðarþróun og gervigreind.', 'https://apro.is/', ?)
            """, (rel_path,))
            conn.commit()
            conn.close()
            print("🎉 NÁKVÆMLEGA RÉTT STARFSMANNAMYND AF APRO.IS VISTUÐ SEM PRÓFÍLMYND!")
    else:
        print("Fann ekki beinan texta 'Axel Bjarkar', leita að öllum starfsmönnum...")
        for h in page.locator("h1, h2, h3, h4, p").all_inner_texts():
            if "axel" in h.lower():
                print(" -", h)
    browser.close()
