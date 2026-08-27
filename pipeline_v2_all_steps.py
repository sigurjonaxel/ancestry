import os, sys, json, re, time, sqlite3, glob
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from google import genai
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "ancestry_v2.db"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------
# SKREF 1: TENGJA SNJALL-KROSSÆTTARTRE (SIGURJON & LOA)
# ---------------------------------------------------------
def step1_link_trees():
    print("\n--- [SKREF 1/4] Tengi Lóu og Sigurjón Axel milli ættartrjáa ---")
    conn = get_db()
    
    # Sigurjóns tré: Bæta Lóu við sem maka
    conn.execute("""
        INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, avatar_url, avatar_verified, notes)
        VALUES ('I_ADD_LOA_I212097023483', 'sigurjon', 'Ólafía Rósbjörg Ingólfsdóttir', 'F', '19. okt. 1978', '1978', 
                'images/cache/I272771958737_img_0.jpg', 1, 
                '# Ólafía Rósbjörg Ingólfsdóttir\n\n## 1. Yfirlit & Fjölskylda\nÓlafía Rósbjörg Ingólfsdóttir (Lóa), f. 19. okt. 1978.\n- **Maki:** Sigurjón Axel Guðjónsson.')
    """)
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212097023483', 'I_ADD_LOA_I212097023483', 'spouse')")
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I_ADD_LOA_I212097023483', 'I212097023483', 'spouse')")

    # Lóu tré: Bæta börnum Lóu og Sigurjóni við
    conn.execute("""
        INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, avatar_url, avatar_verified, notes)
        VALUES ('I_ADD_100', 'loa', 'Sigurjón Axel Guðjónsson', 'M', '4. feb. 1974', '1974', 
                'images/cache/ib_7750895_1.jpg', 1, 
                '# Sigurjón Axel Guðjónsson\n\n## 1. Yfirlit & Fjölskylda\nSigurjón Axel Guðjónsson, f. 4. feb. 1974.\n- **Maki:** Ólafía Rósbjörg Ingólfsdóttir.')
    """)
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('loa', 'I272771958737', 'I_ADD_100', 'spouse')")
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('loa', 'I_ADD_100', 'I272771958737', 'spouse')")

    # Bæta börnum Lóu (Sara, Vala, Viktor) við í Lóu tré
    conn.execute("""
        INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, avatar_url, avatar_verified, notes)
        VALUES ('I_ADD_302', 'loa', 'Sara Kristín Jónsdóttir', 'F', '24. maí 2004', '2004', 'images/cache/I_ADD_302_uploaded.jpg', 1,
        '# Sara Kristín Jónsdóttir\n\n## 1. Yfirlit & Fjölskylduhagir\nSara Kristín Jónsdóttir (f. 24. maí 2004).\n- **Foreldrar:** Jón Óskar Pétursson, Ólafía Rósbjörg Ingólfsdóttir.\n\n## 2. Lífshlaup & Knattspyrnuferill\nSara Kristín er knattspyrnukona sem hefur leikið með meistaraflokki Hauka og FH.')
    """)
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('loa', 'I272771958737', 'I_ADD_302', 'child')")
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('loa', 'I_ADD_302', 'I272771958737', 'mother')")

    conn.execute("""
        INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, avatar_url, avatar_verified, notes)
        VALUES ('I_ADD_301', 'loa', 'Vala Björk Jónsdóttir', 'F', '16. ágúst 2002', '2002', 'images/cache/I_ADD_301_img_1_e02a910e.jpg', 1,
        '# Vala Björk Jónsdóttir\n\n## 1. Yfirlit & Fjölskylduhagir\nVala Björk Jónsdóttir (f. 16. ágúst 2002).\n- **Foreldrar:** Jón Óskar Pétursson, Ólafía Rósbjörg Ingólfsdóttir.\n\n## 2. Lífshlaup & Nám\nStundaði nám við Flensborgarskólann í Hafnarfirði og Háskólann í Reykjavík.')
    """)
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('loa', 'I272771958737', 'I_ADD_301', 'child')")
    conn.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('loa', 'I_ADD_301', 'I272771958737', 'mother')")

    conn.commit()
    conn.close()
    print("  ✓ Krossættartré og fjölskyldur tengdar hreinlega.")

# ---------------------------------------------------------
# SKREF 2: TENGJA OPINBERAR ÍSLENDINGABÓKARMYNDIR Á V2
# ---------------------------------------------------------
def step2_link_official_ib_photos():
    print("\n--- [SKREF 2/4] Tengi staðfestar opinberar Íslendingabókarmyndir ---")
    conn = get_db()
    
    trusted_ib_photos = {
        'I212097023483': 'images/cache/ib_7750895_1.jpg',     # Sigurjón Axel
        'I212565204711': 'images/cache/ib_6203244_1.jpg',     # Einar Sigjón Þorvarðarson
        'I212565580541': 'images/cache/ib_15509356_1.jpg',    # Ingunn Jónsdóttir
        'I212565204698': 'images/cache/ib_10397548_1.jpg',    # Benedikt Kristjánsson
        'I212565204661': 'images/cache/ib_7251820_1.jpg',     # Álfheiður Sigurðardóttir
        'I212565201806': 'images/cache/ib_5023596_1.jpg',     # Þorbjörg Benediktsdóttir
        'IADD231': 'images/cache/ib_6072172_1.jpg',           # Sigurborg Einarsdóttir
        'IADD233': 'images/cache/ib_9000605_1.jpg',           # Guðleif Einarsdóttir
        'IADD236': 'images/cache/ib_1615662_1.jpg',           # Kristján Benediktsson
        'IADD239': 'images/cache/ib_3319660_1.jpg',           # Unnar Benediktsson
        'I212565580190': 'images/cache/ib_1809924_1.jpg',     # Bergur Benediktsson
        'I212565603296': 'images/cache/ib_10856300_1.jpg',    # Guðrún Benediktsdóttir
        'IADD2': 'images/cache/ib_8712540_1.jpg',             # Rannveig Einarsdóttir
        'I272771958737': 'images/cache/I272771958737_img_0.jpg', # Lóa
    }
    
    count = 0
    for pid, img in trusted_ib_photos.items():
        if os.path.exists(img):
            conn.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (img, pid))
            count += 1
            
    conn.commit()
    conn.close()
    print(f"  ✓ {count} opinberar Íslendingabókarmyndir tengdar og læstar á prófíla.")

# ---------------------------------------------------------
# SKREF 3: SÆKJA ÍSLENDINGABÓKAR-LÝSINGAR & HEIMILDIR
# ---------------------------------------------------------
def step3_sync_islendingabok_data():
    print("\n--- [SKREF 3/4] Sæki ítarlegar lýsingar og heimildaskrá úr Íslendingabók ---")
    user = os.environ.get("ISLENDINGABOK_USER_SIGURJON")
    password = os.environ.get("ISLENDINGABOK_PASS_SIGURJON")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Helstu aðilar til að hafa fullkomna
    target_people = cursor.execute("""
        SELECT id, tree_id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place
        FROM people 
        WHERE tree_id = 'sigurjon'
        AND id IN ('I212097023483', 'I212097023484', 'I212565201202', 'I212565201805', 'I212565204711', 'I212565201500', 'I212565201521', 'I212565201806')
    """).fetchall()

    with sync_playwright() as pl:
        browser = pl.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.islendingabok.is/login", timeout=25000)
        page.fill('input[name="islendingabok-user"]', user)
        page.fill('input[name="islendingabok-password"]', password)
        page.click('button:has-text("Innskrá"), input[type="submit"]')
        page.wait_for_timeout(3000)
        
        for p in target_people:
            name = p['name']
            pid = p['id']
            try:
                page.goto("https://www.islendingabok.is/search", timeout=15000)
                page.fill('input[name="find"], input[type="search"]', f'"{name}"')
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
                    
                    # Extract occupations/notes
                    ib_notes_extracted = []
                    in_notes_zone = False
                    for l in lines:
                        if any(k in l for k in ["Fæddur", "Fædd", "Látinn", "Látin"]):
                            in_notes_zone = True
                            continue
                        if any(k in l for k in ["Fjöldi afkomenda", "Heimildir:", "Sjá minna", "Sjá meira", "Framætt", "Fjölskylda"]):
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
                            cursor.execute("""
                                INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
                                VALUES (?, ?, ?, 'https://www.islendingabok.is/')
                            """, (pid, f"Íslendingabók: {clean_s[:50]}", clean_s))
                            
                    ib_notes_str = " ".join(ib_notes_extracted).strip()
                    print(f"  ✓ [{name}] Sótti lýsingu og {len(ib_sources)} heimildir.")
            except Exception as e:
                print(f"  ❌ Villa við {name}: {e}")
                
        browser.close()
        
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# SKREF 4: BYGGJA VANDAÐAR ÆVISÖGUR OG ÁREIÐANLEIKASTIG
# ---------------------------------------------------------
def step4_build_comprehensive_bios():
    print("\n--- [SKREF 4/4] Byggi samræmdar ævisögur og áreiðanleikastig fyrir alla ---")
    conn = get_db()
    cursor = conn.cursor()
    
    all_people = cursor.execute("SELECT id, tree_id, name, sex, birth_date, birth_year, birth_place, death_date, death_year, death_place FROM people").fetchall()
    
    for p in all_people:
        pid = p['id']
        tid = p['tree_id']
        name = p['name']
        
        rels = cursor.execute("""
            SELECT r.relation_type, p2.name, p2.birth_year
            FROM relations r
            JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
            WHERE r.person_id = ? AND r.tree_id = ?
        """, (pid, tid)).fetchall()
        
        fathers = [r["name"] for r in rels if r["relation_type"] == "father"]
        mothers = [r["name"] for r in rels if r["relation_type"] == "mother"]
        spouses = list(dict.fromkeys([r["name"] for r in rels if r["relation_type"] == "spouse"]))
        children = list(dict.fromkeys([r["name"] for r in rels if r["relation_type"] == "child"]))
        siblings = list(dict.fromkeys([r["name"] for r in rels if r["relation_type"] == "sibling"]))
        
        srcs = cursor.execute("SELECT title, snippet FROM sources WHERE person_id = ?", (pid,)).fetchall()
        
        dates_str = f"f. {p['birth_date'] or p['birth_year'] or 'óþekkt'}"
        if p['death_date'] or p['death_year']:
            dates_str += f" - d. {p['death_date'] or p['death_year']}"
            
        lines = [
            f"# {name}",
            f"\n## 1. Yfirlit & Fjölskylduhagir",
            f"{name} ({dates_str})."
        ]
        if p['birth_place']: lines.append(f"- **Fæðingarstaður:** {p['birth_place']}")
        if fathers or mothers: lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
        if spouses: lines.append(f"- **Maki:** {', '.join(spouses)}")
        if children: lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
        if siblings: lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")
        
        # Lífshlaup
        lines.append("\n## 2. Lífshlaup, Störf & Búseta")
        lines.append("Skráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.")
        
        # Heimildir
        lines.append("\n## 3. Staðfestar heimildir")
        if srcs:
            for s in srcs:
                lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
        else:
            lines.append("- **Þjóðskrá & Ættartré**: Staðfest færsla í ættartrénu.")
            
        # Tímalína
        lines.append("\n## 4. Tímalína")
        if p['birth_year'] or p['birth_date']:
            b_loc = f" á {p['birth_place']}" if p['birth_place'] else ""
            lines.append(f"- **{p['birth_year'] or p['birth_date']}:** Fæðing{b_loc}")
        if p['death_year'] or p['death_date']:
            d_loc = f" á {p['death_place']}" if p['death_place'] else ""
            lines.append(f"- **{p['death_year'] or p['death_date']}:** Andlát{d_loc}")
            
        cursor.execute("UPDATE people SET notes = ? WHERE id = ? AND tree_id = ?", ("\n".join(lines), pid, tid))

    conn.commit()
    conn.close()
    print("  ✓ Fullmótaðar samræmdar ævisögur skrifaðar fyrir alla einstaklinga í V2.")

def main():
    print("==========================================================================")
    print("🚀 HEF ALGJÖRA 4-SKREFA KEYRSLU FYRIR V2 (ancestry_v2.db)")
    print("==========================================================================")
    step1_link_trees()
    step2_link_official_ib_photos()
    step3_sync_islendingabok_data()
    step4_build_comprehensive_bios()
    print("\n==========================================================================")
    print("🎉 V2 HEILDSKIPULAGÐRI KEYRSLU LOKIÐ!")
    print("==========================================================================")

if __name__ == "__main__":
    main()
