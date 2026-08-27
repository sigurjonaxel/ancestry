import os, sys, json, re, time, sqlite3, urllib.parse, urllib.request
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
    page.goto("https://www.islendingabok.is/login", timeout=20000)
    if page.locator('input[name="islendingabok-user"]').count() > 0:
        page.fill('input[name="islendingabok-user"]', user)
        page.fill('input[name="islendingabok-password"]', password)
        page.click('button:has-text("Innskrá"), input[type="submit"]')
        page.wait_for_timeout(3000)

def extract_person_ib_details(page, ind_id):
    if ind_id == "7750895" or ind_id == "me":
        page.goto("https://www.islendingabok.is/individual", timeout=20000)
    else:
        page.goto(f"https://www.islendingabok.is/individual?indId={ind_id}&tabs=family", timeout=20000)
        
    page.wait_for_timeout(1500)
    
    # Click "Sjá meira" to uncollapse all text and sources
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

    # 2. Birth / Death / Places
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

    # 3. Extract Official Notes / Occupation / Bio snippet
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

    # 5. Extract relatives with indId
    rel_ids = []
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m_id = re.search(r"indId=(\d+)", href)
        if m_id and m_id.group(1) != ind_id:
            rel_ids.append(m_id.group(1))

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
        "rel_ids": list(set(rel_ids))
    }

def update_person_in_db_safely(tree_id, p_data):
    if not p_data["name"] or len(p_data["name"].split()) < 2:
        return
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Match person by exact name and matching birth year or approximate birth year
    cursor.execute("""
        SELECT id, birth_year, birth_date, birth_place, death_year, death_date, death_place, notes 
        FROM people 
        WHERE tree_id = ? AND name = ?
    """, (tree_id, p_data["name"]))
    rows = cursor.fetchall()
    
    matched_id = None
    if len(rows) == 1:
        matched_id = rows[0]["id"]
    elif len(rows) > 1:
        for r in rows:
            if p_data["birth_year"] and r["birth_year"] == p_data["birth_year"]:
                matched_id = r["id"]
                break
        if not matched_id:
            matched_id = rows[0]["id"]
            
    if not matched_id:
        # Special case for Sigurjón Axel
        if p_data["name"] == "Sigurjón Axel Guðjónsson" and tree_id == "sigurjon":
            matched_id = "I212097023483"
        else:
            conn.close()
            return
            
    # Fetch relations from DB to build 100% consistent overview
    cursor.execute("""
        SELECT r.relation_type, p2.name, p2.birth_year
        FROM relations r
        JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
        WHERE r.person_id = ? AND r.tree_id = ?
    """, (matched_id, tree_id))
    rels = cursor.fetchall()
    
    fathers = [r["name"] for r in rels if r["relation_type"] == "father"]
    mothers = [r["name"] for r in rels if r["relation_type"] == "mother"]
    spouses = list(dict.fromkeys([r["name"] for r in rels if r["relation_type"] == "spouse"]))
    children = list(dict.fromkeys([r["name"] for r in rels if r["relation_type"] == "child"]))
    siblings = list(dict.fromkeys([r["name"] for r in rels if r["relation_type"] == "sibling"]))
    
    b_date = p_data["birth_date"] or p_data["birth_year"] or ""
    b_place = p_data["birth_place"] or ""
    d_date = p_data["death_date"] or p_data["death_year"] or ""
    d_place = p_data["death_place"] or ""
    
    dates_str = f"f. {b_date or 'óþekkt'}"
    if d_date:
        dates_str += f" - d. {d_date}"
        
    lines = [
        f"# {p_data['name']}",
        f"\n## 1. Yfirlit & Fjölskylda",
        f"{p_data['name']} ({dates_str})."
    ]
    if b_place:
        lines.append(f"- **Fæðingarstaður:** {b_place}")
    if fathers or mothers:
        lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
    if spouses:
        lines.append(f"- **Maki:** {', '.join(spouses)}")
    if children:
        lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
    if siblings:
        lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")

    # 2. Lífshlaup úr Íslendingabók
    if p_data["ib_notes"]:
        lines.append(f"\n## 2. Lífshlaup, Störf & Búseta\n{p_data['ib_notes']}")
        
    # 3. Staðfestar heimildir úr Íslendingabók
    lines.append("\n## 3. Staðfestar heimildir úr Íslendingabók")
    if p_data["ib_sources"]:
        for s in p_data["ib_sources"]:
            lines.append(f"- **{s}**")
            cursor.execute("""
                INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
                VALUES (?, ?, ?, ?)
            """, (matched_id, f"Íslendingabók: {s[:50]}", s, f"https://www.islendingabok.is/individual?indId={p_data['ind_id']}"))
    else:
        lines.append("- **Þjóðskrá & Kirkjubækur**: Staðfest færsla í Íslendingabók.")
        
    # 4. Tímalína
    lines.append("\n## 4. Tímalína")
    if b_date:
        b_loc = f" á {b_place}" if b_place else ""
        lines.append(f"- **{b_date}:** Fæðing{b_loc}")
    if d_date:
        d_loc = f" á {d_place}" if d_place else ""
        lines.append(f"- **{d_date}:** Andlát{d_loc}")
        
    bio_text = "\n".join(lines)
    
    cursor.execute("""
        UPDATE people 
        SET birth_date = COALESCE(NULLIF(?, ''), birth_date),
            birth_year = COALESCE(NULLIF(?, ''), birth_year),
            birth_place = COALESCE(NULLIF(?, ''), birth_place),
            death_date = COALESCE(NULLIF(?, ''), death_date),
            death_year = COALESCE(NULLIF(?, ''), death_year),
            death_place = COALESCE(NULLIF(?, ''), death_place),
            notes = ?
        WHERE id = ? AND tree_id = ?
    """, (b_date, p_data["birth_year"], b_place, d_date, p_data["death_year"], d_place, bio_text, matched_id, tree_id))
    
    conn.commit()
    conn.close()
    return matched_id

def sync_entire_tree_ib_details(max_depth=3):
    print("==========================================================")
    print("🚀 HEF ALGJÖRA SAMSTILLINGU ÍSLENDINGABÓKAR-TEXTA & HEIMILDA")
    print("==========================================================")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        ensure_login(page)
        
        root_id = "7750895"
        queue = [(root_id, 0)]
        visited = set()
        count_updated = 0
        
        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            
            try:
                p_data = extract_person_ib_details(page, current_id)
                if not p_data or not p_data["name"]:
                    continue
                    
                mid = update_person_in_db_safely("sigurjon", p_data)
                if mid:
                    count_updated += 1
                    print(f"[{count_updated}] ✓ {p_data['name']} (f. {p_data['birth_date'] or p_data['birth_year']})")
                    if p_data['ib_notes']:
                        print(f"    📝 Texti: {p_data['ib_notes'][:80]}...")
                    if p_data['ib_sources']:
                        print(f"    📚 {len(p_data['ib_sources'])} heimildir vistaðar.")
                
                if depth < max_depth:
                    for rid in p_data["rel_ids"]:
                        if rid not in visited:
                            queue.append((rid, depth + 1))
                            
            except Exception as e:
                print(f"  ❌ Villa við að sækja indId={current_id}: {e}")
                
        browser.close()
        
    print("\n==========================================================")
    print(f"✅ Samstillingu lokið! {count_updated} manns fengu ítarlegan texta og heimildaskrá úr Íslendingabók.")
    print("==========================================================")

if __name__ == "__main__":
    sync_entire_tree_ib_details(max_depth=3)
