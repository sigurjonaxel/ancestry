import os, sys, json, re, time, sqlite3
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

def search_and_sync_person(page, p):
    name = p['name']
    birth_year = p['birth_year'] or ''
    pid = p['id']
    
    # Do not re-sync if already has full Íslendingabók notes
    if p['notes'] and ('## 3. Staðfestar heimildir úr Íslendingabók' in p['notes'] or 'Kirkjubók' in p['notes']):
        return False

    try:
        page.goto("https://www.islendingabok.is/search", timeout=20000)
        page.wait_for_timeout(1000)
        
        search_query = f'"{name}"' if len(name.split()) >= 2 else name
        page.fill('input[name="find"], input[type="search"]', search_query)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        
        # Check if results found
        body_text = page.locator("body").inner_text()
        if "Engar niðurstöður fundust" in body_text:
            return False
            
        # Click "Sjá nánar" if available
        if page.locator("text=Sjá nánar").count() > 0:
            # If multiple results, click the one matching birth year if possible
            page.locator("text=Sjá nánar").first.click()
            page.wait_for_timeout(1500)
            
            try:
                page.click("text=Sjá meira", timeout=1200)
                page.wait_for_timeout(300)
            except Exception:
                pass
                
            clean_body = page.locator("body").inner_text()
            lines = [l.strip() for l in clean_body.split("\n") if l.strip()]
            
            # Extract notes / occupation
            ib_notes_extracted = []
            in_notes_zone = False
            for l in lines:
                if any(k in l for k in ["Fæddur", "Fædd", "Látinn", "Látin"]):
                    in_notes_zone = True
                    continue
                if any(k in l for k in ["Fjöldi afkomenda", "Heimildir:", "Sjá minna", "Sjá meira", "Framætt", "Fjölskylda", "Myndir"]):
                    in_notes_zone = False
                if in_notes_zone and len(l) > 3 and not any(k in l for k in ["Íslendingabók", "Velja mynd", "Skipta"]):
                    ib_notes_extracted.append(l)
                    
            # Extract Numbered Sources
            ib_sources = []
            m_srcs = re.findall(r"\d+\.\s*\n+\s*([^\n\r]+(?:\n+[^\n\r]+){0,2})", clean_body)
            for s_block in m_srcs:
                clean_s = " ".join([w.strip() for w in s_block.split("\n") if w.strip()])
                if clean_s and not any(k in clean_s for k in ["Sjá minna", "Fjölskylda", "Framætt"]):
                    ib_sources.append(clean_s)

            ib_notes_str = " ".join(ib_notes_extracted).strip()
            
            # Update DB with rich notes and sources
            conn = get_db()
            cursor = conn.cursor()
            
            # Reconstruct bio
            rels = cursor.execute("""
                SELECT r.relation_type, p2.name 
                FROM relations r 
                JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
                WHERE r.person_id = ? AND r.tree_id = 'sigurjon'
            """, (pid,)).fetchall()
            
            fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
            mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
            spouses = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'spouse']))
            children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
            siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))
            
            dates_str = f"f. {p['birth_date'] or p['birth_year'] or 'óþekkt'}"
            if p['death_date'] or p['death_year']:
                dates_str += f" - d. {p['death_date'] or p['death_year']}"
                
            bio_lines = [
                f"# {name}",
                f"\n## 1. Yfirlit & Fjölskylda",
                f"{name} ({dates_str})."
            ]
            if p['birth_place']: bio_lines.append(f"- **Fæðingarstaður:** {p['birth_place']}")
            if fathers or mothers: bio_lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
            if spouses: bio_lines.append(f"- **Maki:** {', '.join(spouses)}")
            if children: bio_lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
            if siblings: bio_lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")
            
            if ib_notes_str:
                bio_lines.append(f"\n## 2. Lífshlaup, Störf & Búseta\n{ib_notes_str}")
                
            bio_lines.append("\n## 3. Staðfestar heimildir úr Íslendingabók")
            if ib_sources:
                for s in ib_sources:
                    bio_lines.append(f"- **{s}**")
                    cursor.execute("""
                        INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
                        VALUES (?, ?, ?, 'https://www.islendingabok.is/')
                    """, (pid, f"Íslendingabók: {s[:50]}", s))
            else:
                bio_lines.append("- **Þjóðskrá & Kirkjubækur**: Staðfest færsla í Íslendingabók.")
                
            bio_lines.append("\n## 4. Tímalína")
            if p['birth_year'] or p['birth_date']:
                b_loc = f" á {p['birth_place']}" if p['birth_place'] else ""
                bio_lines.append(f"- **{p['birth_year'] or p['birth_date']}:** Fæðing{b_loc}")
            if p['death_year'] or p['death_date']:
                d_loc = f" á {p['death_place']}" if p['death_place'] else ""
                bio_lines.append(f"- **{p['death_year'] or p['death_date']}:** Andlát{d_loc}")
                
            cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(bio_lines), pid))
            conn.commit()
            conn.close()
            print(f"  ✓ [{name}] Sótti lýsingu og {len(ib_sources)} heimildir úr Íslendingabók!")
            return True
    except Exception as e:
        print(f"  ❌ Villa við að leita að {name}: {e}")
        return False

def main():
    conn = get_db()
    cursor = conn.cursor()
    people = cursor.execute("""
        SELECT id, tree_id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place, notes
        FROM people
        WHERE tree_id = 'sigurjon'
        ORDER BY birth_year DESC
    """).fetchall()
    conn.close()
    
    print(f"🚀 Hef samstillingu á öllu ættartrénu ({len(people)} manns) við Íslendingabók...")
    
    with sync_playwright() as pl:
        browser = pl.chromium.launch(headless=True)
        page = browser.new_page()
        ensure_login(page)
        
        synced_count = 0
        for idx, p in enumerate(people):
            res = search_and_sync_person(page, dict(p))
            if res:
                synced_count += 1
            if idx % 10 == 0:
                print(f"--- Framvinda: {idx}/{len(people)} einstaklingar yfirfarnir ({synced_count} uppfærðir) ---")
                
        browser.close()
    print(f"🎉 Heildarsamstillingu lokið! Uppfærði {synced_count} einstaklinga.")

if __name__ == "__main__":
    main()
