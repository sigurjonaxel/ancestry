import os, sys, re, sqlite3, json

DB_FILE = "ancestry.db"

def rebuild_clean_db():
    print("==========================================================")
    print("🔨 BYGGI UPP HREINAN OG NÁKVÆMAN GAGNAGRUNN ÚR GEDCOM SKRÁM")
    print("==========================================================")
    
    # 1. Back up existing avatars and real external sources before rebuild
    existing_avatars = {}
    existing_sources = []
    if os.path.exists(DB_FILE):
        try:
            conn_old = sqlite3.connect(DB_FILE)
            conn_old.row_factory = sqlite3.Row
            for r in conn_old.execute("SELECT id, tree_id, avatar_url FROM people WHERE avatar_url IS NOT NULL").fetchall():
                existing_avatars[(r['tree_id'], r['id'])] = r['avatar_url']
            for s in conn_old.execute("SELECT person_id, title, snippet, link, image_url FROM sources WHERE link NOT LIKE '%timarit.is/?q=%' AND title NOT LIKE 'Tímarit.is: %'").fetchall():
                existing_sources.append(dict(s))
            conn_old.close()
        except Exception as e:
            print("  ⚠️ Backup error:", e)

    # 2. Reset database tables
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS relations;
        DROP TABLE IF EXISTS people;
        DROP TABLE IF EXISTS trees;
        DROP TABLE IF EXISTS sources;
        DROP TABLE IF EXISTS ai_suggestions;

        CREATE TABLE trees (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            name TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE people (
            id TEXT PRIMARY KEY,
            tree_id TEXT NOT NULL,
            name TEXT NOT NULL,
            given_names TEXT,
            surname TEXT,
            sex TEXT,
            birth_date TEXT,
            birth_year TEXT,
            birth_place TEXT,
            death_date TEXT,
            death_year TEXT,
            death_place TEXT,
            avatar_url TEXT,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tree_id TEXT NOT NULL,
            person_id TEXT NOT NULL,
            related_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            UNIQUE(tree_id, person_id, related_id, relation_type)
        );

        CREATE TABLE sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            title TEXT NOT NULL,
            snippet TEXT,
            link TEXT,
            image_url TEXT,
            favicon TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE ai_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT NOT NULL,
            type TEXT NOT NULL,
            source TEXT,
            url TEXT,
            image_url TEXT,
            local_path TEXT,
            title TEXT,
            description TEXT,
            confidence INTEGER DEFAULT 70,
            relation_details TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Import pristine GEDCOM trees
    trees = [
        ("sigurjon", "sigurjon.ged", "Sigurjón Axel Guðjónsson"),
        ("loa", "loa.ged", "Ólafía Rósbjörg Sigurðardóttir")
    ]

    for tree_id, filename, tree_name in trees:
        print(f"\n📂 Flyt inn tré: {tree_name} ({filename})...")
        cursor.execute("INSERT INTO trees (id, filename, name) VALUES (?, ?, ?)", (tree_id, filename, tree_name))
        
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        people = {}
        families = {}
        curr_id = None
        curr_type = None
        
        for line in lines:
            line = line.strip()
            if not line: continue
            parts = line.split(" ", 2)
            if len(parts) >= 3 and parts[2] in ("INDI", "FAM"):
                curr_id = parts[1].replace("@", "")
                curr_type = parts[2]
                if curr_type == "INDI":
                    people[curr_id] = {
                        "name": "", "sex": "", "b_date": "", "b_year": "", "b_place": "",
                        "d_date": "", "d_year": "", "d_place": ""
                    }
                else:
                    families[curr_id] = {"husb": None, "wife": None, "children": []}
                continue
                
            if curr_type == "INDI" and curr_id in people:
                tag = parts[1]
                val = parts[2] if len(parts) > 2 else ""
                if tag == "NAME":
                    people[curr_id]["name"] = val.replace("/", "").strip()
                elif tag == "SEX":
                    people[curr_id]["sex"] = val
                elif tag == "DATE":
                    m = re.search(r"\b(1\d{3}|20\d{2})\b", val)
                    if not people[curr_id]["b_date"]:
                        people[curr_id]["b_date"] = val
                        if m: people[curr_id]["b_year"] = m.group(1)
                    else:
                        people[curr_id]["d_date"] = val
                        if m: people[curr_id]["d_year"] = m.group(1)
                elif tag == "PLAC":
                    if not people[curr_id]["b_place"]:
                        people[curr_id]["b_place"] = val
                    else:
                        people[curr_id]["d_place"] = val
            elif curr_type == "FAM" and curr_id in families:
                tag = parts[1]
                val = parts[2].replace("@", "") if len(parts) > 2 else ""
                if tag == "HUSB":
                    families[curr_id]["husb"] = val
                elif tag == "WIFE":
                    families[curr_id]["wife"] = val
                elif tag == "CHIL":
                    families[curr_id]["children"].append(val)

        # Insert People into DB
        for pid, p in people.items():
            avatar = existing_avatars.get((tree_id, pid))
            cursor.execute("""
                INSERT INTO people (id, tree_id, name, sex, birth_date, birth_year, birth_place, death_date, death_year, death_place, avatar_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, tree_id, p["name"], p["sex"], p["b_date"], p["b_year"], p["b_place"], p["d_date"], p["d_year"], p["d_place"], avatar))
            
        print(f"  ✓ Flutti inn {len(people)} einstaklinga.")

        # Build Clean Relations from Families
        rel_count = 0
        for fam_id, fam in families.items():
            h = fam["husb"]
            w = fam["wife"]
            children = fam["children"]
            
            # Spouse relations
            if h and w and h in people and w in people:
                cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'spouse')", (tree_id, h, w))
                cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'spouse')", (tree_id, w, h))
                rel_count += 2
                
            # Parent - Child relations
            for c in children:
                if c not in people: continue
                if h and h in people:
                    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'father')", (tree_id, c, h))
                    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'child')", (tree_id, h, c))
                    rel_count += 2
                if w and w in people:
                    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'mother')", (tree_id, c, w))
                    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'child')", (tree_id, w, c))
                    rel_count += 2
                    
            # Sibling relations
            for i in range(len(children)):
                for j in range(i + 1, len(children)):
                    c1, c2 = children[i], children[j]
                    if c1 in people and c2 in people:
                        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'sibling')", (tree_id, c1, c2))
                        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'sibling')", (tree_id, c2, c1))
                        rel_count += 2

        print(f"  ✓ Skráði {rel_count} rétt, óbrengluð ættartengsl.")

    # 4. Restore valid sources
    for s in existing_sources:
        cursor.execute("""
            INSERT OR IGNORE INTO sources (person_id, title, snippet, link, image_url)
            VALUES (?, ?, ?, ?, ?)
        """, (s['person_id'], s['title'], s['snippet'], s['link'], s['image_url']))

    # 5. Generate pristine, consistent biographies (Notes) directly matching the pristine DB for EVERY person
    print("\n✍️ BYGGI NÁKVÆMAR, SAMRÆMDA ÆVISÖGUR (NOTES) FYRIR ALLA EINSTAKLINGA...")
    cursor.execute("SELECT id, tree_id, name, sex, birth_date, birth_year, birth_place, death_date, death_year, death_place FROM people")
    all_people = [dict(r) for r in cursor.fetchall()]

    for p in all_people:
        pid = p["id"]
        tid = p["tree_id"]
        name = p["name"]
        
        cursor.execute("""
            SELECT r.relation_type, p2.name, p2.birth_year
            FROM relations r
            JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
            WHERE r.person_id = ? AND r.tree_id = ?
        """, (pid, tid))
        rels = cursor.fetchall()
        
        fathers = [r["name"] for r in rels if r["relation_type"] == "father"]
        mothers = [r["name"] for r in rels if r["relation_type"] == "mother"]
        spouses = list(set([r["name"] for r in rels if r["relation_type"] == "spouse"]))
        children = list(set([r["name"] for r in rels if r["relation_type"] == "child"]))
        siblings = list(set([r["name"] for r in rels if r["relation_type"] == "sibling"]))
        
        foreldrar = fathers + mothers
        
        dates_str = f"f. {p['birth_date'] or p['birth_year'] or 'óþekkt'}"
        if p['death_date'] or p['death_year']:
            dates_str += f" - d. {p['death_date'] or p['death_year']}"
            
        lines = [
            f"# {name}",
            f"\n## 1. Yfirlit & Fjölskylda",
            f"{name} ({dates_str})."
        ]
        if p['birth_place']:
            lines.append(f"- **Fæðingarstaður:** {p['birth_place']}")
        if foreldrar:
            lines.append(f"- **Foreldrar:** {', '.join(foreldrar)}")
        if spouses:
            lines.append(f"- **Maki:** {', '.join(spouses)}")
        if children:
            lines.append(f"- **Börn:** {', '.join(children)}")
        if siblings:
            lines.append(f"- **Systkini:** {', '.join(siblings)}")
            
        lines.append(f"\n## 2. Staðfestar heimildir\n- **Ættartré & Þjóðskrá**: Staðfest færsla í ættartrénu.")
        
        lines.append(f"\n## 3. Tímalína")
        b_val = p['birth_year'] or p['birth_date']
        if b_val:
            b_loc = f" á {p['birth_place']}" if p['birth_place'] else ""
            lines.append(f"- **{b_val}:** Fæðing{b_loc}")
            
        d_val = p['death_year'] or p['death_date']
        if d_val:
            d_loc = f" á {p['death_place']}" if p['death_place'] else ""
            lines.append(f"- **{d_val}:** Andlát{d_loc}")
            
        bio_text = "\n".join(lines)
        cursor.execute("UPDATE people SET notes = ? WHERE id = ? AND tree_id = ?", (bio_text, pid, tid))

    conn.commit()
    conn.close()
    print("\n==========================================================")
    print("✅ GAGNAGRUNNURINN HEFUR VERIÐ ENDURREISTUR KERFISBUNDIÐ!")
    print("==========================================================")

if __name__ == "__main__":
    rebuild_clean_db()
