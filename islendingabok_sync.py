import os, sys, json, re, time, sqlite3, urllib.parse, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

def get_db():
    conn = sqlite3.connect("ancestry.db")
    conn.row_factory = sqlite3.Row
    return conn

def ensure_login(page):
    user = os.environ.get("ISLENDINGABOK_USER_SIGURJON") or os.environ.get("ISLENDINGABOK_USER")
    password = os.environ.get("ISLENDINGABOK_PASS_SIGURJON") or os.environ.get("ISLENDINGABOK_PASS")
    page.goto("https://www.islendingabok.is/login", timeout=20000)
    if page.locator('input[name="islendingabok-user"]').count() > 0:
        page.fill('input[name="islendingabok-user"]', user)
        page.fill('input[name="islendingabok-password"]', password)
        page.click('button:has-text("Innskrá"), input[type="submit"]')
        page.wait_for_timeout(3000)

def search_timarit_articles(name, keywords=None):
    results = []
    try:
        query = f'"{name}"'
        if keywords:
            query += f" {keywords}"
        url = f"https://timarit.is/?q={urllib.parse.quote(query)}&size=10&isAdvanced=false"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        text = soup.get_text()
        # Find all lines after Morgunblaðið, etc.
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for idx, l in enumerate(lines):
            if any(p in l for p in ["Morgunblaðið", "Tíminn", "Alþýðublaðið", "Þjóðviljinn", "Vísir", "Dagblaðið", "Búnaðarrit", "Ársrit"]):
                pub_title = l
                snip = lines[idx+1] if idx+1 < len(lines) else ""
                results.append({
                    "title": f"Tímarit.is: {pub_title}",
                    "link": url,
                    "snippet": snip[:180]
                })
                if len(results) >= 3:
                    break
    except Exception as e:
        print(f"  [Tímarit Search Error] {e}")
    return results

def download_ib_image(page, img_rel_url, ind_id, idx):
    try:
        if not img_rel_url or not img_rel_url.startswith("image/"):
            return None
        full_url = "https://www.islendingabok.is/" + img_rel_url
        cookies = page.context.cookies()
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        req = urllib.request.Request(full_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Cookie": cookie_header
        })
        data = urllib.request.urlopen(req, timeout=10).read()
        os.makedirs("images/cache", exist_ok=True)
        local_path = f"images/cache/ib_{ind_id}_{idx}.jpg"
        with open(local_path, "wb") as f:
            f.write(data)
        return local_path
    except Exception as e:
        print(f"  [IB Img Error] {e}")
        return None

def fetch_and_parse_person(page, ind_id):
    if ind_id == "7750895" or ind_id == "me":
        page.goto("https://www.islendingabok.is/individual", timeout=20000)
    else:
        # Search person by ID or query directly
        page.goto("https://www.islendingabok.is/front", timeout=15000)
        page.goto(f"https://www.islendingabok.is/individual?indId={ind_id}&tabs=family", timeout=20000)
        
    page.wait_for_timeout(1500)
    
    # Click "Sjá meira"
    try:
        page.click("text=Sjá meira", timeout=1500)
        page.wait_for_timeout(400)
    except Exception:
        pass

    header_text = ""
    try:
        header_text = page.locator("header").inner_text()
    except Exception:
        pass
        
    body_text = page.locator("body").inner_text()
    clean_body = body_text.replace(header_text, "").strip()
    lines = [l.strip() for l in clean_body.split("\n") if l.strip()]
    
    # 1. Name
    name = ""
    ignore_words = ("íslendingabók", "einstaklingur", "velja mynd", "skipta", "leita", "stillingar", "framætt", "tölfræði", "fjölskylda", "myndir", "æviágrip", "ábendingar", "sjá meira", "sjá minna", "heimildir", "fædd", "dá", "barn", "kona", "maður", "viðurnefni", "aðgerð misfórst")
    for l in lines[:15]:
        low = l.lower()
        if len(l.split()) >= 2 and not any(k in low for k in ignore_words):
            name = l
            break

    # 2. Birth / Death
    birth_date, birth_year, birth_place = "", "", ""
    death_date, death_year, death_place = "", "", ""
    
    m_birth = re.search(r"Fædd(?:ur|ist|ing)?\s+([\d\.]+\s+[a-záðéíóúýþæö]+\s+\d{4}|\d{4})(?:\s+(?:á|í)\s+([^\n\r]+))?", clean_body, re.IGNORECASE)
    if m_birth:
        birth_date = m_birth.group(1).strip()
        m_by = re.search(r"\b(\d{4})\b", birth_date)
        if m_by:
            birth_year = m_by.group(1)
        if m_birth.group(2):
            birth_place = m_birth.group(2).strip().split("\n")[0].split("Heimildir")[0].split("Fjöldi")[0].split("Látin")[0].strip()
            
    m_death = re.search(r"(?:Dá(?:inn|in|st)?|Látin[sn]?)\s+([\d\.]+\s+[a-záðéíóúýþæö]+\s+\d{4}|\d{4})(?:\s+(?:á|í)\s+([^\n\r]+))?", clean_body, re.IGNORECASE)
    if m_death:
        death_date = m_death.group(1).strip()
        m_dy = re.search(r"\b(\d{4})\b", death_date)
        if m_dy:
            death_year = m_dy.group(1)
        if m_death.group(2):
            death_place = m_death.group(2).strip().split("\n")[0].split("Heimildir")[0].strip()

    # 3. Extract Historical Text / Occupation (e.g. "Bóndi og símstöðvarstjóri. Vinnumaður á Brunnhóli...")
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

    # 4. Extract Numbered Sources
    ib_sources = []
    m_srcs = re.findall(r"\d+\.\s*\n+\s*([^\n\r]+(?:\n+[^\n\r]+){0,2})", clean_body)
    for s_block in m_srcs:
        clean_s = " ".join([w.strip() for w in s_block.split("\n") if w.strip()])
        if clean_s and not any(k in clean_s for k in ["Sjá minna", "Fjölskylda", "Framætt"]):
            ib_sources.append(clean_s)

    # 5. Images
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("image/"):
            images.append(a["href"])
            
    # 6. Relationships
    father = None
    mother = None
    spouses = []
    children = []
    siblings = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m_id = re.search(r"indId=(\d+)", href)
        if not m_id:
            continue
        rel_id = m_id.group(1)
        if rel_id == ind_id:
            continue
        rel_name = a.text.strip()
        if not rel_name or len(rel_name.split()) < 2:
            continue
            
        pblock = a.find_parent(["div", "section", "li", "td", "tr"])
        ptxt = pblock.get_text() if pblock else ""
        
        if "Faðir" in ptxt and not father:
            father = (rel_id, rel_name)
        elif "Móðir" in ptxt and not mother:
            mother = (rel_id, rel_name)
        elif any(k in ptxt for k in ["Eiginkona", "Eiginmaður", "Maki", "Sambýlis"]):
            spouses.append((rel_id, rel_name))
        elif "Börn" in ptxt:
            children.append((rel_id, rel_name))
        elif "Alsystkin" in ptxt or "Hálfsystkin" in ptxt:
            siblings.append((rel_id, rel_name))
            
    return {
        "ind_id": ind_id,
        "name": name,
        "birth_date": birth_date,
        "birth_year": birth_year,
        "birth_place": birth_place,
        "death_date": death_date,
        "death_year": death_year,
        "death_place": death_place,
        "ib_notes": " ".join(ib_notes_extracted).strip(),
        "ib_sources": ib_sources,
        "images": images,
        "father": father,
        "mother": mother,
        "spouses": list(set(spouses)),
        "children": list(set(children)),
        "siblings": list(set(siblings))
    }

def sync_person_to_db(tree_id, p_data, avatar_path=None):
    if not p_data["name"] or len(p_data["name"].split()) < 2:
        return None
        
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, notes, avatar_url, sex FROM people WHERE tree_id = ? AND (id = ? OR name = ?)", 
                   (tree_id, f"IB_{p_data['ind_id']}", p_data["name"]))
    row = cursor.fetchone()
    
    db_id = f"IB_{p_data['ind_id']}"
    if p_data["name"] == "Sigurjón Axel Guðjónsson" and tree_id == "sigurjon":
        db_id = "I212097023483"
    elif row:
        db_id = row["id"]
        
    final_avatar = avatar_path or (row["avatar_url"] if row else None)
    
    foreldrar_str = []
    if p_data["father"]: foreldrar_str.append(p_data["father"][1])
    if p_data["mother"]: foreldrar_str.append(p_data["mother"][1])
    
    dates_str = f"f. {p_data['birth_date'] or p_data['birth_year'] or 'óþekkt'}"
    if p_data['death_date'] or p_data['death_year']:
        dates_str += f" - d. {p_data['death_date'] or p_data['death_year']}"
        
    bio_lines = [
        f"# {p_data['name']}",
        f"\n## 1. Yfirlit & Fjölskylda",
        f"{p_data['name']} ({dates_str}).",
    ]
    if p_data['birth_place']:
        bio_lines.append(f"- **Fæðingarstaður:** {p_data['birth_place']}")
    if foreldrar_str:
        bio_lines.append(f"- **Foreldrar:** {', '.join(foreldrar_str)}")
    if p_data['spouses']:
        bio_lines.append(f"- **Maki:** {', '.join([s[1] for s in p_data['spouses']])}")
    if p_data['children']:
        bio_lines.append(f"- **Börn:** {', '.join([c[1] for c in p_data['children']])}")
    if p_data['siblings']:
        bio_lines.append(f"- **Systkini:** {', '.join([sb[1] for sb in p_data['siblings']])}")

    if p_data['ib_notes']:
        bio_lines.append(f"\n## 2. Lífshlaup & Menntun\n{p_data['ib_notes']}")
        
    bio_lines.append("\n## 3. Staðfestar heimildir")
    if p_data['ib_sources']:
        for s in p_data['ib_sources']:
            bio_lines.append(f"- **Íslendingabók**: {s}")
    else:
        bio_lines.append("- **Íslendingabók (Opinber ættfræðigrunnur)**: Staðfestar upplýsingar úr Þjóðskrá og kirkjubókum.")
        
    bio_lines.append("\n## 4. Tímalína")
    b_txt = p_data['birth_year'] or p_data['birth_date']
    if b_txt:
        place_info = f" á {p_data['birth_place']}" if p_data['birth_place'] else ""
        bio_lines.append(f"- **{b_txt}:** Fæðing{place_info}")
    d_txt = p_data['death_year'] or p_data['death_date']
    if d_txt:
        bio_lines.append(f"- **{d_txt}:** Andlát")
        
    bio_text = "\n".join(bio_lines)
    sex = "F" if p_data["name"].strip().endswith("dóttir") or p_data["name"].strip().endswith("dottir") else "M"

    if row:
        cursor.execute("""
            UPDATE people 
            SET name = ?, sex = ?, birth_date = COALESCE(NULLIF(?, ''), birth_date),
                birth_year = COALESCE(NULLIF(?, ''), birth_year),
                birth_place = COALESCE(NULLIF(?, ''), birth_place),
                death_date = COALESCE(NULLIF(?, ''), death_date),
                death_year = COALESCE(NULLIF(?, ''), death_year),
                death_place = COALESCE(NULLIF(?, ''), death_place),
                avatar_url = COALESCE(?, avatar_url),
                notes = ?
            WHERE id = ?
        """, (p_data["name"], sex, p_data["birth_date"], p_data["birth_year"], p_data["birth_place"],
              p_data["death_date"], p_data["death_year"], p_data["death_place"], final_avatar, bio_text, db_id))
    else:
        cursor.execute("""
            INSERT INTO people (id, tree_id, name, sex, birth_date, birth_year, birth_place, death_date, death_year, death_place, avatar_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (db_id, tree_id, p_data["name"], sex, p_data["birth_date"], p_data["birth_year"], p_data["birth_place"],
              p_data["death_date"], p_data["death_year"], p_data["death_place"], final_avatar, bio_text))
        
    for s in p_data['ib_sources']:
        cursor.execute("""
            INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
            VALUES (?, ?, ?, ?)
        """, (db_id, f"Íslendingabók: {s[:50]}", s, f"https://www.islendingabok.is/individual?indId={p_data['ind_id']}"))

    conn.commit()
    conn.close()
    return db_id

def link_relations_in_db(tree_id, person_db_id, p_data, id_map):
    conn = get_db()
    cursor = conn.cursor()
    
    if p_data["father"]:
        fid, fname = p_data["father"]
        f_db_id = id_map.get(fid, f"IB_{fid}")
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'father')",
                       (tree_id, person_db_id, f_db_id))
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'child')",
                       (tree_id, f_db_id, person_db_id))
        
    if p_data["mother"]:
        mid, mname = p_data["mother"]
        m_db_id = id_map.get(mid, f"IB_{mid}")
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'mother')",
                       (tree_id, person_db_id, m_db_id))
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'child')",
                       (tree_id, m_db_id, person_db_id))
        
    for sid, sname in p_data["spouses"]:
        s_db_id = id_map.get(sid, f"IB_{sid}")
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'spouse')",
                       (tree_id, person_db_id, s_db_id))
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'spouse')",
                       (tree_id, s_db_id, person_db_id))
        
    cursor.execute("SELECT sex FROM people WHERE id = ?", (person_db_id,))
    p_row = cursor.fetchone()
    p_sex = p_row["sex"] if p_row else ("F" if p_data["name"].endswith("dóttir") else "M")
    parent_type = "mother" if p_sex == "F" else "father"
    
    for cid, cname in p_data["children"]:
        c_db_id = id_map.get(cid, f"IB_{cid}")
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'child')",
                       (tree_id, person_db_id, c_db_id))
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, ?)",
                       (tree_id, c_db_id, person_db_id, parent_type))
        
    for sbid, sbname in p_data["siblings"]:
        sb_db_id = id_map.get(sbid, f"IB_{sbid}")
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'sibling')",
                       (tree_id, person_db_id, sb_db_id))
        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'sibling')",
                       (tree_id, sb_db_id, person_db_id))
        
    conn.commit()
    conn.close()

def search_and_link_timarit_for_ancestors(all_parsed, id_map):
    print("\n📰 SÆKI OG TENGJA TÍMARIT.IS HEIMILDIR...")
    conn = get_db()
    cursor = conn.cursor()
    
    for ind_id, p_data in all_parsed.items():
        name = p_data["name"]
        db_id = id_map.get(ind_id)
        if not db_id or len(name.split()) < 2:
            continue
            
        kw = p_data.get("birth_place") or ""
        t_results = search_timarit_articles(name, kw)
        for tr in t_results[:3]:
            print(f"    [+] Fann Tímarit grein fyrir {name}: {tr['title']}")
            cursor.execute("""
                INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
                VALUES (?, ?, ?, ?)
            """, (db_id, tr['title'], tr['snippet'], tr['link']))
            
    conn.commit()
    conn.close()

def regenerate_all_bios_with_ai(all_parsed, id_map):
    print("\n✍️ SEMUR OG ENDURGERIR ÆVISÖGUR MEÐ GEMINI AI FYRIR HVERN EINSTAKLING...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  ⚠️ Vantar GEMINI_API_KEY")
        return
        
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print("  ⚠️ Ekki tókst að ræsa Gemini client:", e)
        return
        
    conn = get_db()
    cursor = conn.cursor()
    
    for ind_id, p_data in all_parsed.items():
        name = p_data["name"]
        db_id = id_map.get(ind_id)
        if not db_id or len(name.split()) < 2:
            continue
            
        # Skip overriding Sigurjón or Lóa if already fully polished
        if db_id in ("I212097023483", "I_ADD_LOA_I212097023483", "I272771958737"):
            continue
            
        cursor.execute("SELECT notes FROM people WHERE id = ?", (db_id,))
        p_row = cursor.fetchone()
        existing_notes = p_row["notes"] if p_row else ""
        
        cursor.execute("SELECT title, snippet, link FROM sources WHERE person_id = ?", (db_id,))
        srcs = cursor.fetchall()
        src_context = "\n".join([f"- {s['title']}: {s['snippet']} ({s['link']})" for s in srcs]) if srcs else ""
        
        prompt = f"""
        Þú ert íslenskur ættfræðingur. Skrifaðu hnitmiðaða, nákvæma og raunsæja samantekt á íslensku fyrir {name}.
        
        GÖGN:
        - Fæðing: {p_data.get('birth_date') or p_data.get('birth_year')} ({p_data.get('birth_place') or ''})
        - Andlát: {p_data.get('death_date') or p_data.get('death_year')} ({p_data.get('death_place') or ''})
        - Texti/Störf úr Íslendingabók: {p_data.get('ib_notes') or 'Ekki skráð'}
        - Staðfestar heimildir:
        {src_context}
        
        STRÖNG FYRIRMÆLI:
        - Bannað er að búa til skáldskap eða upplogna starfsferla.
        - Haltu textanum skýrum, formlegum og byggðum eingöngu á ofangreindum staðreyndum.
        
        Form:
        # {name}
        ## 1. Yfirlit & Fjölskylda
        ## 2. Lífshlaup & Heimildir
        ## 3. Tímalína
        """
        
        try:
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            if resp and resp.text:
                new_bio = resp.text.strip()
                cursor.execute("UPDATE people SET notes = ? WHERE id = ?", (new_bio, db_id))
                conn.commit()
                print(f"  ✓ Endurgerði ævisögu með AI fyrir: {name}")
                time.sleep(1.5)
        except Exception as ge:
            print(f"  ⚠️ AI Bio villa fyrir {name}: {ge}")
            time.sleep(3)
            
    conn.close()

def traverse_sigurjon_tree(max_depth=3):
    print("==========================================================")
    print("🚀 HEF RÖKSTUÐLAÐA ÍSLENDINGABÓKARSAMSTILLINGU (V3) FYRIR SIGURJÓN")
    print("==========================================================")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        ensure_login(page)
        
        root_id = "7750895"
        queue = [(root_id, 0)]
        visited = set()
        id_map = {}
        all_parsed = {}
        
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            
            print(f"\n[Dýpt {depth}] Sæki indId={current_id} úr Íslendingabók...")
            try:
                p_data = fetch_and_parse_person(page, current_id)
                if not p_data or not p_data["name"]:
                    continue
                all_parsed[current_id] = p_data
                
                avatar_path = None
                if p_data["images"]:
                    avatar_path = download_ib_image(page, p_data["images"][0], current_id, 1)
                    if avatar_path:
                        print(f"  📷 Fann og vistaði mynd: {avatar_path}")
                        
                db_id = sync_person_to_db("sigurjon", p_data, avatar_path)
                id_map[current_id] = db_id
                
                print(f"  ✓ {p_data['name']} (f. {p_data['birth_date'] or p_data['birth_year']} | {p_data['birth_place']}) -> DB ID: {db_id}")
                if p_data['ib_notes']:
                    print(f"    📝 Texti/Störf: {p_data['ib_notes'][:70]}...")
                if p_data['ib_sources']:
                    print(f"    📚 Heimildir: {len(p_data['ib_sources'])} skráðar (t.d. {p_data['ib_sources'][0][:40]}...)")
                
                if depth < max_depth:
                    if p_data["father"] and p_data["father"][0] not in visited:
                        queue.append((p_data["father"][0], depth + 1))
                    if p_data["mother"] and p_data["mother"][0] not in visited:
                        queue.append((p_data["mother"][0], depth + 1))
                    for sid, _ in p_data["spouses"]:
                        if sid not in visited:
                            queue.append((sid, depth + 1))
                    for cid, _ in p_data["children"]:
                        if cid not in visited:
                            queue.append((cid, depth + 1))
                    for sbid, _ in p_data["siblings"]:
                        if sbid not in visited:
                            queue.append((sbid, depth + 1))
                            
            except Exception as e:
                print(f"  ❌ Villa við að sækja indId={current_id}: {e}")
                
        print("\n🔗 Tengi öll fjölskyldutengsl rétt í ancestry.db...")
        for ind_id, p_data in all_parsed.items():
            db_id = id_map.get(ind_id)
            if db_id:
                link_relations_in_db("sigurjon", db_id, p_data, id_map)
                
        # Link Tímarit.is articles
        search_and_link_timarit_for_ancestors(all_parsed, id_map)
        
        browser.close()
        
    # Regenerate AI Biographies for everyone based on all gathered data
    regenerate_all_bios_with_ai(all_parsed, id_map)
        
    print("\n==========================================================")
    print(f"✅ Fullri Íslendingabókar-, Tímarit.is- og AI ævisögusamstillingu lokið!")
    print("==========================================================")

if __name__ == "__main__":
    traverse_sigurjon_tree(max_depth=3)
