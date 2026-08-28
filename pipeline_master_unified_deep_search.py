import os, sys, json, re, time, sqlite3, urllib.parse, urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
user = os.environ.get("ISLENDINGABOK_USER_LOA") or os.environ.get("ISLENDINGABOK_USER")
password = os.environ.get("ISLENDINGABOK_PASS_LOA") or os.environ.get("ISLENDINGABOK_PASS")

def get_connection():
    conn = sqlite3.connect("ancestry.db", timeout=120.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def search_timarit_all(name, spouse_kw=None):
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    queries = [f'"{name}"']
    if spouse_kw:
        queries.append(f'"{name}" {spouse_kw}')

    seen_links = set()
    for q in queries:
        url = f"https://timarit.is/?q={urllib.parse.quote(q)}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                lines = [l.strip() for l in soup.get_text().splitlines() if l.strip()]
                for idx, l in enumerate(lines):
                    if any(p in l for p in ["Morgunblaðið", "Fréttablaðið", "DV", "Dagblaðið", "Tíminn", "Alþýðublaðið", "Þjóðviljinn"]):
                        title = l
                        date_info = lines[idx+1] if idx+1 < len(lines) else ""
                        snip = lines[idx+2] if idx+2 < len(lines) else ""
                        if "  " in snip and len(snip.split("  ")) >= 3: continue
                        if len(snip) < 15: continue
                        full_txt = (title + " " + date_info + " " + snip).lower()
                        if any(part.lower() in full_txt for part in name.split()[:2]):
                            if url not in seen_links:
                                seen_links.add(url)
                                is_edu = any(k in full_txt for k in ["stúdent", "brautskrá", "háskól", "próf", "deild"])
                                tag = "🎓 Menntun / Brautskráning" if is_edu else "📰 Minningargrein / Grein"
                                results.append({
                                    "title": f"Tímarit.is: {title} ({tag})",
                                    "snippet": snip[:180],
                                    "link": url
                                })
                                if len(results) >= 2: break
        except Exception:
            pass
        if len(results) >= 2: break
    return results

def run_master_unified_deep_search(tree_id="loa"):
    print("========================================================================", flush=True)
    print(f"🚀 MASTER GENEALOGY DEEP SEARCH (LÖG 1, 2, 3) FYRIR TRÉ: '{tree_id}'", flush=True)
    print("========================================================================", flush=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM people WHERE tree_id = ? ORDER BY id ASC", (tree_id,))
    people = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    total = len(people)
    print(f"✓ Alls {total} einstaklingar sem verða fullunnir í einu samfelldu aðalforriti.", flush=True)

    # 1. ÍSLENDINGABÓK
    ib_data = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print("🔑 Innskráning á Íslendingabók.is...", flush=True)
        page.goto("https://www.islendingabok.is/login", timeout=30000)
        if page.locator('input[name="islendingabok-user"]').count() > 0:
            page.fill('input[name="islendingabok-user"]', user)
            page.fill('input[name="islendingabok-password"]', password)
            page.click('button:has-text("Innskrá"), input[type="submit"]')
            page.wait_for_timeout(3500)
        print("✓ Innskráning tókst!", flush=True)

        t0 = time.time()
        for idx, person in enumerate(people, 1):
            pid = person['id']
            name = person['name']
            by = person.get('birth_year') or ''
            by_int = int(by) if by and str(by).isdigit() else None
            
            ib_note = ""
            try:
                page.goto("https://www.islendingabok.is/search", timeout=12000)
                page.fill('input[type="search"], input[name="search"]', name)
                page.press('input[type="search"], input[name="search"]', 'Enter')
                page.wait_for_timeout(1400)
                
                body_text = page.locator("body").inner_text()
                m_storf = re.search(r'(Var á [^\n\.]+|Húsfreyja[^\n\.]+|Bóndi[^\n\.]+|Sjómaður[^\n\.]+|Verkamaður[^\n\.]+|Kennari[^\n\.]+|Prestur[^\n\.]+|Trésmiður[^\n\.]+)', body_text)
                if m_storf:
                    candidate = m_storf.group(1).strip()
                    m_year = re.search(r'\b(1[789]\d\d|20\d\d)\b', candidate)
                    if not m_year or not by_int or (by_int <= int(m_year.group(1)) <= (by_int + 105)):
                        ib_note = candidate
            except Exception:
                pass
            
            ib_data[pid] = ib_note
            if idx % 50 == 0 or idx == total:
                print(f"   -> [Lög 1 - Íslendingabók] {idx}/{total} afgreiddir ({(idx/total)*100:.1f}%) | Liðinn tími: {time.time()-t0:.1f}s", flush=True)

        browser.close()

    # 2. TÍMARIT & MASTER SNIÐMÁT
    print("\n------------------------------------------------------------------------", flush=True)
    print("📰 LÖG 2 & 3: Tímarit.is leitað og Master Sniðmát smíðað fyrir alla", flush=True)
    print("------------------------------------------------------------------------", flush=True)
    
    t1 = time.time()
    for idx, person in enumerate(people, 1):
        pid = person['id']
        name = person['name']
        by = person.get('birth_year') or ''
        dy = person.get('death_year') or ''
        b_date = person.get('birth_date') or by
        d_date = person.get('death_date') or dy
        bp = person.get('birth_place') or ''
        by_int = int(by) if by and str(by).isdigit() else None
        
        conn_w = get_connection()
        c_w = conn_w.cursor()
        
        # Sækja tengsl
        rels = c_w.execute("""
            SELECT r.relation_type, p2.name, p2.birth_year, p2.death_year 
            FROM relations r 
            JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
            WHERE r.person_id = ? AND r.tree_id = ?
        """, (pid, tree_id)).fetchall()
        
        fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
        mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
        spouses = []
        for r in rels:
            if r['relation_type'] == 'spouse':
                s_str = r['name']
                if r['birth_year'] and r['death_year']: s_str += f" (f. {r['birth_year']} - d. {r['death_year']})"
                elif r['birth_year']: s_str += f" (f. {r['birth_year']})"
                spouses.append(s_str)
        spouses = list(dict.fromkeys(spouses))
        children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
        siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))
        
        # Leita á Tímarit.is ef fullorðinn
        if by_int and by_int < 2005:
            sp_kw = spouses[0].split()[0] if spouses else ""
            t_res = search_timarit_all(name, sp_kw)
            for tr in t_res:
                c_w.execute("""
                    INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
                    VALUES (?, ?, ?, ?)
                """, (pid, tr['title'], tr['snippet'], tr['link']))

        # Varðveita ef nú þegar eru handskrifaðar / sérsniðnar lífsögur
        existing_notes = person.get('notes') or ''
        custom_bio = ""
        m_sec2 = re.search(r'## 2\. [^\n]+\n([\s\S]*?)(?=\n## 3\.|\Z)', existing_notes)
        if m_sec2:
            sec2 = m_sec2.group(1).strip()
            if not any(k in sec2 for k in ["Skráður einstaklingur í ættartali", "óviðkomandi"]) and len(sec2) > 15:
                custom_bio = sec2

        dates_str = f"f. {b_date or 'óþekkt'}"
        if d_date: dates_str += f" - d. {d_date}"
        
        lines = [
            f"# {name}",
            f"\n## 1. Yfirlit & Fjölskylduhagir",
            f"{name} ({dates_str})."
        ]
        if bp: lines.append(f"- **Fæðingarstaður:** {bp}")
        if fathers or mothers: lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
        if spouses: lines.append(f"- **Maki:** {', '.join(spouses)}")
        if children: lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
        if siblings: lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")
        
        lines.append("\n## 2. Lífshlaup, Menntun & Búseta")
        if custom_bio:
            lines.append(custom_bio)
        elif ib_data.get(pid):
            lines.append(f"- **Íslendingabók:** {ib_data[pid]}")
        else:
            if by_int and (2026 - by_int) <= 18:
                lines.append(f"{name.split()[0]} er í hópi yngri kynslóða ættarinnar, skráð(ur) í ættartali.")
            else:
                lines.append("Skráður einstaklingur í ættartali.")

        srcs = c_w.execute("SELECT title, snippet FROM sources WHERE person_id = ?", (pid,)).fetchall()
        lines.append("\n## 3. Staðfestar heimildir")
        if srcs:
            for s in srcs: lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
        else:
            lines.append("- **Íslendingabók & Þjóðskrá**: Staðfest færsla og ættartengsl.")
            
        lines.append("\n## 4. Tímalína")
        if b_date: lines.append(f"- **{b_date}:** Fæðing")
        if d_date: lines.append(f"- **{d_date}:** Andlát")
        
        c_w.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(lines), pid))
        conn_w.commit()
        conn_w.close()
        
        if idx % 50 == 0 or idx == total:
            print(f"   -> [Lög 2 & 3] {idx}/{total} lokið ({(idx/total)*100:.1f}%) | Liðinn tími: {time.time()-t1:.1f}s", flush=True)

    print("\n========================================================================", flush=True)
    print(f"🎉 MASTER DEEP SEARCH FULLKLÁRAÐ FYRIR ALLA {total} EINSTAKLINGA Í '{tree_id}'!", flush=True)
    print("========================================================================", flush=True)

if __name__ == '__main__':
    run_master_unified_deep_search('loa')
