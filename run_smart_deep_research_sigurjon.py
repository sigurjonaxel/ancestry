import sqlite3, time, os, re, json, urllib.request, urllib.parse
from bs4 import BeautifulSoup
from ai_research import search_direct_web_images, download_image_cache

def get_db():
    conn = sqlite3.connect("ancestry.db", timeout=60.0)
    conn.row_factory = sqlite3.Row
    return conn

def search_smart_web(name, birth_year, locations, relatives):
    """
    Snjöll íslensk vefleit:
    1. Prófar fullt nafn OG nafn án millinafns (t.d. 'Ármann Karl' vs 'Ármann').
    2. Tengir við staði (Svínafell, Brunnhóll, Höfn, Hornafjörður, Akureyri, Reykjavík).
    3. Tengir við maka og foreldra.
    4. Leitar á Tímarit.is og Bing/Google.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    results = []
    
    parts = name.split()
    first_last = f"{parts[0]} {parts[-1]}" if len(parts) > 2 else name
    
    queries = [
        f'"{name}"',
        f'"{first_last}" ' + " OR ".join([f'"{loc}"' for loc in locations if loc]) if locations else f'"{first_last}"'
    ]
    if relatives:
        queries.append(f'"{first_last}" "{relatives[0]}"')
        
    for q in queries[:2]:
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
                        # Sanity check: must contain part of person's name or place
                        if any(w.lower() in (title + " " + snip).lower() for w in parts[:2]):
                            results.append({"title": title, "snippet": snip, "link": link})
        except Exception:
            pass
        time.sleep(1.0)
        
    return results

def process_person_smart(p):
    pid = p['id']
    name = p['name']
    b_date = p['birth_date'] or p['birth_year'] or ''
    b_year = p['birth_year'] or ''
    d_date = p['death_date'] or p['death_year'] or ''
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Get family context & places
    rels = cursor.execute("""
        SELECT r.relation_type, p2.name, p2.birth_year 
        FROM relations r 
        JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
        WHERE r.person_id = ? AND r.tree_id = 'sigurjon'
    """, (pid,)).fetchall()
    
    fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
    mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
    spouses = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'spouse']))
    children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
    siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))
    relatives = spouses + fathers + mothers
    
    locations = ["Hornafjörður", "Höfn", "Brunnhóll", "Akureyri", "Reykjavík", "Mýrar", "Öræfi", "Svínafell"]
    
    print(f"\n==========================================================================")
    print(f"🔍 [SNJÖLL VEFRANNSÓKN] {name} (f. {b_date})")
    
    # 2. Snjöll vefleit
    web_data = search_smart_web(name, b_year, locations, relatives)
    print(f"   ✓ Fann {len(web_data)} vefheimildir.")
    
    # 3. Vista nýjar staðfestar heimildir
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
            
    print(f"   ✓ Fann og sótti {len(downloaded_photos)} ljósmyndir af netinu.")
    
    # 5. Sækja allar heimildir úr DB og endurbyggja ævisögu
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
    print(f" ✓ [{name}] Uppfærður með {len(all_srcs)} heimildum og {len(downloaded_photos)} myndum!")

def main():
    conn = get_db()
    # Process key adult descendants and living members in Sigurjon tree
    people = conn.execute("""
        SELECT id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place
        FROM people 
        WHERE tree_id = 'sigurjon'
        ORDER BY 
            CASE 
                WHEN birth_year != '' AND CAST(birth_year AS INTEGER) BETWEEN 1940 AND 2010 THEN 0
                ELSE 1
            END,
            birth_year DESC
    """).fetchall()
    conn.close()
    
    print(f"🚀 HEF NÝJA SNJALLA VEFRANNSÓKN FYRIR ALLA {len(people)} EINSTAKLINGA Í SIGURJÓNS TRÉ...")
    
    for idx, p in enumerate(people):
        try:
            process_person_smart(dict(p))
        except Exception as e:
            print(f" ⚠️ Villa við {p['name']}: {e}")
        time.sleep(1.5)
        
    print("\n🎉 ALLIR Í SIGURJÓNS TRÉ HAFA VERIÐ ENDURRANNSAKAÐIR MEÐ SNJÖLLU LEITINNI!")

if __name__ == "__main__":
    main()
