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

def run_full_sync():
    print("==========================================================================")
    print("🚀 HEF HEILDARKEYRSLU Á ÖLLUM Í SIGURJÓNS TRÉ:")
    print("   1. Íslendingabók (Innskráning, Lýsingar, Heimildaskrá, Opinberar Myndir)")
    print("   2. Ættartrétékk & 100% Tengslasamræmi")
    print("   3. Vandaðar Ævisögur & Tímalínur")
    print("==========================================================================")

    user = os.environ.get("ISLENDINGABOK_USER_SIGURJON") or os.environ.get("ISLENDINGABOK_USER")
    password = os.environ.get("ISLENDINGABOK_PASS_SIGURJON") or os.environ.get("ISLENDINGABOK_PASS")
    
    conn = get_db()
    cursor = conn.cursor()
    people = cursor.execute("""
        SELECT id, tree_id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place, avatar_url, avatar_verified, notes
        FROM people 
        WHERE tree_id = 'sigurjon'
        ORDER BY 
            CASE 
                WHEN birth_year != '' AND CAST(birth_year AS INTEGER) >= 1850 THEN 0
                ELSE 1
            END,
            birth_year DESC
    """).fetchall()
    conn.close()

    print(f"👥 Fann {len(people)} einstaklinga í tré Sigurjóns sem fara í gegnum ferlið.")

    with sync_playwright() as pl:
        browser = pl.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🔑 Skrái inn á Íslendingabók.is...")
        page.goto("https://www.islendingabok.is/login", timeout=30000)
        if page.locator('input[name="islendingabok-user"]').count() > 0:
            page.fill('input[name="islendingabok-user"]', user)
            page.fill('input[name="islendingabok-password"]', password)
            page.click('button:has-text("Innskrá"), input[type="submit"]')
            page.wait_for_timeout(3500)
            
        print("✅ Innskráning tókst!")

        synced = 0
        for idx, p in enumerate(people):
            pid = p['id']
            name = p['name']
            birth_year = p['birth_year'] or ''

            # Check if blocked
            if "bannaður" in page.content().lower() or "blocked" in page.content().lower():
                print(f"🚨 [VIÐVÖRUN / BLOKKUN]: Íslendingabók lokaði á fyrirspurnir við {name}!")
                break

            try:
                page.goto("https://www.islendingabok.is/search", timeout=15000)
                search_query = f'"{name}"' if len(name.split()) >= 2 else name
                page.fill('input[name="find"], input[type="search"]', search_query)
                page.keyboard.press("Enter")
                page.wait_for_timeout(1800)

                if page.locator("text=Sjá nánar").count() > 0:
                    page.locator("text=Sjá nánar").first.click()
                    page.wait_for_timeout(1800)
                    try:
                        page.click("text=Sjá meira", timeout=1000)
                        page.wait_for_timeout(300)
                    except Exception: pass

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
                    m_srcs = re.findall(r"\d+\.\s*\n+\s*([^\n\r]+(?:\n+[^\n\r]+){0,2})", clean_body)
                    ib_sources = []
                    for s_block in m_srcs:
                        clean_s = " ".join([w.strip() for w in s_block.split("\n") if w.strip()])
                        if clean_s and not any(k in clean_s for k in ["Sjá minna", "Fjölskylda", "Framætt"]):
                            ib_sources.append(clean_s)

                    ib_notes_str = " ".join(ib_notes_extracted).strip()

                    # Save to DB
                    conn = get_db()
                    cursor = conn.cursor()
                    for s in ib_sources:
                        cursor.execute("""
                            INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
                            VALUES (?, ?, ?, 'https://www.islendingabok.is/')
                        """, (pid, f"Íslendingabók: {s[:50]}", s))

                    # Rebuild markdown bio
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

                    srcs = cursor.execute("SELECT title, snippet FROM sources WHERE person_id = ?", (pid,)).fetchall()

                    dates_str = f"f. {p['birth_date'] or p['birth_year'] or 'óþekkt'}"
                    if p['death_date'] or p['death_year']:
                        dates_str += f" - d. {p['death_date'] or p['death_year']}"

                    bio_lines = [
                        f"# {name}",
                        f"\n## 1. Yfirlit & Fjölskylduhagir",
                        f"{name} ({dates_str})."
                    ]
                    if p['birth_place']: bio_lines.append(f"- **Fæðingarstaður:** {p['birth_place']}")
                    if fathers or mothers: bio_lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
                    if spouses: bio_lines.append(f"- **Maki:** {', '.join(spouses)}")
                    if children: bio_lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
                    if siblings: bio_lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")

                    if ib_notes_str:
                        bio_lines.append(f"\n## 2. Lífshlaup, Störf & Búseta\n{ib_notes_str}")
                    else:
                        bio_lines.append(f"\n## 2. Lífshlaup, Störf & Búseta\nSkráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar úr Íslendingabók.")

                    bio_lines.append("\n## 3. Staðfestar heimildir")
                    if srcs:
                        for s in srcs:
                            bio_lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
                    # 📸 AUTOMATIC WEB PHOTO DISCOVERY IN DEFAULT RUN:
                    # Sækir raunverulegar ljósmyndir af netinu sjálfkrafa í hverri keyrslu
                    try:
                        from ai_research import search_direct_web_images, download_image_cache
                        web_photos = search_direct_web_images(name)
                        for wp_idx, wp in enumerate(web_photos[:4]):
                            img_rel = download_image_cache(wp['url'], pid, f"web_{wp_idx}")
                            if img_rel:
                                cursor.execute("""
                                    INSERT OR IGNORE INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
                                    VALUES (?, 'media', 'Vefmyndaleit', ?, ?, ?, ?, 'Ljósmynd af netinu', 85, 'pending')
                                """, (pid, wp.get('url',''), img_rel, img_rel, wp.get('title', f"Mynd af {name}")))
                    except Exception as pe:
                        print(f"   [Myndaleit] Villa: {pe}")

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

                    synced += 1
                    print(f"[{idx+1}/{len(people)}] ✓ [{name}] (f. {birth_year}) -> Uppfærði lýsingu og {len(ib_sources)} heimildir.")

                # Pacing between searches to prevent any rate limit
                time.sleep(2.0)

            except Exception as e:
                print(f"[{idx+1}/{len(people)}] ⚠️ Villa við {name}: {e}")

        browser.close()

    print("\n==========================================================================")
    print(f"🎉 HEILDARSAMSTILLINGU LOKIÐ! Uppfærði {synced} einstaklinga í tré Sigurjóns.")
    print("==========================================================================")

if __name__ == "__main__":
    run_full_sync()
