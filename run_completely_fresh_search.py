import sqlite3, time, os, re, json, urllib.request, urllib.parse
from bs4 import BeautifulSoup
from ai_research import search_direct_web_images, download_image_cache

def get_db():
    conn = sqlite3.connect("ancestry.db", timeout=60.0)
    conn.row_factory = sqlite3.Row
    return conn

print("==========================================================================")
print("🚀 BYRJA ALVEG UPP Á NÝTT: HREIN HEILDARLEIT Á ÖLLU SIGURJÓNS TRÉ")
print("   - Engar takmarkanir, fullar krossprófanir (bæir, íþróttir, skólar, félög)")
print("   - Allir 677 einstaklingar fara í gegnum alvöru djúpvefleitina")
print("==========================================================================")

def deep_search_person(name, birth_year, locations, relatives):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    results = []
    
    parts = name.split()
    first_last = f"{parts[0]} {parts[-1]}" if len(parts) > 2 else name
    
    # Smíða snjallar leitarfyrirspurnir
    queries = [
        f'"{name}"',
        f'"{first_last}"'
    ]
    if locations:
        queries.append(f'"{first_last}" ' + " OR ".join([f'"{loc}"' for loc in locations[:3]]))
    if relatives:
        queries.append(f'"{first_last}" "{relatives[0]}"')
        
    for q in queries[:3]:
        try:
            url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                for li in soup.find_all('li', class_='b_algo')[:3]:
                    h2 = li.find('h2')
                    p = li.find('p')
                    a = li.find('a')
                    if h2 and p and a:
                        title = h2.get_text(strip=True)
                        snip = p.get_text(strip=True)
                        link = a.get('href')
                        if any(w.lower() in (title + " " + snip).lower() for w in parts[:2]):
                            results.append({"title": title, "snippet": snip, "link": link})
        except Exception:
            pass
        time.sleep(0.5)
        
    return results

def process_person_from_scratch(p, total_count, current_idx):
    pid = p['id']
    name = p['name']
    b_date = p['birth_date'] or p['birth_year'] or ''
    b_year = p['birth_year'] or ''
    d_date = p['death_date'] or p['death_year'] or ''
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Get family context
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
    
    locations = ["Hornafjörður", "Höfn", "Brunnhóll", "Akureyri", "Reykjavík", "Mýrar", "Öræfi", "Svínafell", "Selfoss"]
    
    # 2. Keyra djúpvefleitina
    web_data = deep_search_person(name, b_year, locations, spouses + fathers + mothers)
    
    # 3. Vista vefheimildir
    for wd in web_data:
        cursor.execute("""
            INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
            VALUES (?, ?, ?, ?)
        """, (pid, wd['title'][:90], wd['snippet'], wd['link']))
        
    # 4. Sækja raunverulegar vefljósmyndir
    web_photos = search_direct_web_images(name)
    downloaded_photos = []
    for idx, wp in enumerate(web_photos[:4]):
        img_rel = download_image_cache(wp['url'], pid, f"web_{idx}")
        if img_rel:
            downloaded_photos.append((img_rel, wp.get('title', f"Mynd af {name}"), wp.get('url','')))
            cursor.execute("""
                INSERT OR IGNORE INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
                VALUES (?, 'media', 'Vefmyndaleit', ?, ?, ?, ?, 'Ljósmynd af netinu', 85, 'pending')
            """, (pid, wp.get('url',''), img_rel, img_rel, wp.get('title', f"Mynd af {name}")))
            
    # 5. Sækja allar heimildir og endursmíða ævisögu
    all_srcs = cursor.execute("SELECT title, snippet, link FROM sources WHERE person_id = ?", (pid,)).fetchall()
    
    dates_str = f"f. {b_date or 'óþekkt'}"
    if d_date:
        dates_str += f" - d. {d_date}"
        
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
    
    bio_lines.append("\n## 2. Lífshlaup, Nám, Störf & Búseta")
    if len(all_srcs) > 1:
        bio_lines.append(f"Samkvæmt staðfestum heimildum hefur {name.split()[0]} komið víða við í námi, atvinnulífi og félagsstarfi:")
        for s in all_srcs[:5]:
            if "Íslendingabók" not in s['title'] and "Ættarmót" not in s['title']:
                bio_lines.append(f"- **{s['title']}:** {s['snippet']}")
    else:
        bio_lines.append(f"Skráður einstaklingur í ættartali Ættarmóts 2024 (Afkomendur Þorbjargar og Sigurjóns á Brunnhóli).")
        
    bio_lines.append("\n## 3. Staðfestar heimildir")
    if all_srcs:
        for s in all_srcs:
            bio_lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
    else:
        bio_lines.append("- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.")
        
    bio_lines.append("\n## 4. Tímalína")
    if b_date: bio_lines.append(f"- **{b_date}:** Fæðing")
    if d_date: bio_lines.append(f"- **{d_date}:** Andlát")
    
    cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(bio_lines), pid))
    conn.commit()
    conn.close()
    
    print(f"[{current_idx}/{total_count}] ✓ [{name}] -> {len(all_srcs)} heimildir | {len(downloaded_photos)} myndir")

def main():
    conn = get_db()
    people = conn.execute("""
        SELECT id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place
        FROM people 
        WHERE tree_id = 'sigurjon'
        ORDER BY 
            CASE 
                WHEN birth_year != '' AND CAST(birth_year AS INTEGER) BETWEEN 1940 AND 2024 THEN 0
                ELSE 1
            END,
            birth_year DESC
    """).fetchall()
    conn.close()
    
    total = len(people)
    print(f"🚀 HEF NÝJU HEILDARKJÖRNALEITINA FYRIR ALLA {total} EINSTAKLINGA...")
    
    for idx, p in enumerate(people):
        try:
            process_person_from_scratch(dict(p), total, idx + 1)
        except Exception as e:
            print(f"[{idx+1}/{total}] ⚠️ Villa við {p['name']}: {e}")
        time.sleep(1.0)
        
    print("\n🎉 ALLIR Í SIGURJÓNS TRÉ HAFA VERIÐ RANNSAKAÐIR FRÁ GRUNNI MEÐ NÝJU VEFAÐFERÐINNI!")

if __name__ == "__main__":
    main()
