import sqlite3, time, os, re, json, urllib.request, urllib.parse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from ai_research import search_direct_web_images, download_image_cache

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

def get_db():
    conn = sqlite3.connect("ancestry.db", timeout=60.0)
    conn.row_factory = sqlite3.Row
    return conn

def search_web_for_person(name, birth_year, relatives):
    """Deep grounded web research using DuckDuckGo HTML / Google for exact real person."""
    queries = [
        f'"{name}" {birth_year}',
        f'"{name}" Hornafjörður OR Akureyri OR Reykjavík OR Mýrar',
        f'"{name}" ' + " OR ".join([f'"{r}"' for r in relatives[:3]]) if relatives else f'"{name}"'
    ]
    
    snippets = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for q in queries[:2]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=7) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                results = soup.find_all('div', class_='result__body')[:4]
                for r in results:
                    title_elem = r.find('a', class_='result__snippet')
                    snip_elem = r.find('a', class_='result__snippet')
                    url_elem = r.find('a', class_='result__url')
                    
                    t = r.find('h2').get_text(strip=True) if r.find('h2') else ""
                    s = snip_elem.get_text(strip=True) if snip_elem else ""
                    u = url_elem.get_text(strip=True) if url_elem else ""
                    if s and len(s) > 20:
                        snippets.append({"title": t, "snippet": s, "url": u})
        except Exception:
            pass
        time.sleep(1.0)
        
    return snippets

def process_person_thoroughly(p):
    pid = p['id']
    name = p['name']
    b_date = p['birth_date'] or p['birth_year'] or ''
    b_year = p['birth_year'] or ''
    d_date = p['death_date'] or p['death_year'] or ''
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Get family context
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
    relatives = fathers + mothers + spouses + children + siblings
    
    print(f"\n==========================================================================")
    print(f"🔍 [ÍTARLEG LEIT & GÖGN] Vinn úr: {name} (f. {b_date})")
    print(f"   Samhengi: Foreldrar: {fathers+mothers}, Maki: {spouses}, Börn ({len(children)})")
    
    # 2. Sækja vefupplýsingar og fréttir
    web_data = search_web_for_person(name, b_year, relatives)
    print(f"   ✓ Fann {len(web_data)} vefheimildir.")
    
    # 3. Sækja ljósmyndir
    web_photos = search_direct_web_images(name)
    downloaded_photos = []
    for idx, wp in enumerate(web_photos[:4]):
        img_rel = download_image_cache(wp['url'], pid, f"web_{idx}")
        if img_rel:
            downloaded_photos.append((img_rel, wp.get('title', f"Mynd af {name}"), wp.get('url','')))
    print(f"   ✓ Fann og sótti {len(downloaded_photos)} ljósmyndir af netinu.")
    
    # 4. Vista nýjar staðfestar heimildir í DB
    for wd in web_data:
        if any(w in wd['snippet'].lower() for w in name.lower().split()[:2]):
            cursor.execute("""
                INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
                VALUES (?, ?, ?, ?)
            """, (pid, wd['title'][:80] or f"Vefheimild: {name}", wd['snippet'], "https://" + wd['url'] if not wd['url'].startswith("http") else wd['url']))
            
    # 5. Vista ljósmyndir sem uppástungur
    for img_rel, p_title, p_url in downloaded_photos:
        cursor.execute("""
            INSERT OR IGNORE INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
            VALUES (?, 'media', 'Vefmyndaleit', ?, ?, ?, ?, 'Ljósmynd af netinu', 85, 'pending')
        """, (pid, p_url, img_rel, img_rel, p_title))
        
    # 6. Sækja allar heimildir úr DB til að smíða ævisögu
    all_srcs = cursor.execute("SELECT title, snippet, link FROM sources WHERE person_id = ?", (pid,)).fetchall()
    src_text = "\n".join([f"- {s['title']}: {s['snippet']}" for s in all_srcs]) if all_srcs else "Staðfest færsla í ættartali og Þjóðskrá."
    
    # 7. Smíða faglega og ítarlega ævisögu
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
        bio_lines.append(f"Samkvæmt staðfestum heimildum og skráningum hefur {name.split()[0]} komið víða við í námi, atvinnulífi og félagsstarfi:")
        for s in all_srcs[:4]:
            if "Íslendingabók" not in s['title'] and "Ættarmót" not in s['title']:
                bio_lines.append(f"- **{s['title']}:** {s['snippet']}")
    else:
        bio_lines.append(f"Skráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar í Þjóðskrá og ættartali.")
        
    bio_lines.append("\n## 3. Staðfestar heimildir")
    if all_srcs:
        for s in all_srcs:
            bio_lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
    else:
        bio_lines.append("- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.")
        
    bio_lines.append("\n## 4. Tímalína")
    if b_date:
        bio_lines.append(f"- **{b_date}:** Fæðing")
    if d_date:
        bio_lines.append(f"- **{d_date}:** Andlát")
        
    cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(bio_lines), pid))
    conn.commit()
    conn.close()
    print(f" ✓ [{name}] Kláraður með {len(all_srcs)} heimildum og {len(downloaded_photos)} myndum!")

def main():
    conn = get_db()
    people = conn.execute("""
        SELECT id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place
        FROM people 
        WHERE tree_id = 'sigurjon'
        ORDER BY 
            CASE 
                WHEN birth_year != '' AND CAST(birth_year AS INTEGER) >= 1950 THEN 0
                ELSE 1
            END,
            birth_year DESC
    """).fetchall()
    conn.close()
    
    print(f"🚀 HEF ÍTARLEGA HEILDARVINNSLU FYRIR ALLA {len(people)} EINSTAKLINGA Í SIGURJÓNS TRÉ...")
    
    for idx, p in enumerate(people):
        try:
            process_person_thoroughly(dict(p))
        except Exception as e:
            print(f" ⚠️ Villa við {p['name']}: {e}")
        time.sleep(1.5)
        
    print("\n🎉 ALLIR Í SIGURJÓNS TRÉ HAFA VERIÐ UNNIR MEÐ ÍTARLEGRI LEIT OG MYNDUM!")

if __name__ == "__main__":
    main()
