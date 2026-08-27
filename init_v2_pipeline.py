import os, sys, re, sqlite3, json, shutil

DB_FILE = "ancestry_v2.db"

def init_v2_database():
    print("==========================================================================")
    print("🌟 BYRJA V2 HREINA ENDURBYGGINGU (ancestry_v2.db)")
    print("==========================================================================")
    
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.executescript("""
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
            avatar_verified INTEGER DEFAULT 0,
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

    # Import Clean GEDCOM trees
    trees = [
        ("sigurjon", "sigurjon.ged", "Sigurjón Axel Guðjónsson"),
        ("loa", "loa.ged", "Ólafía Rósbjörg Sigurðardóttir")
    ]

    for tree_id, filename, tree_name in trees:
        print(f"\n📂 Flyt inn tré í V2: {tree_name} ({filename})...")
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

        # Insert People
        for pid, p in people.items():
            cursor.execute("""
                INSERT INTO people (id, tree_id, name, sex, birth_date, birth_year, birth_place, death_date, death_year, death_place)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pid, tree_id, p["name"], p["sex"], p["b_date"], p["b_year"], p["b_place"], p["d_date"], p["d_year"], p["d_place"]))
            
        print(f"  ✓ Flutti inn {len(people)} einstaklinga í V2.")

        # Build Clean Relations
        rel_count = 0
        for fam_id, fam in families.items():
            h = fam["husb"]
            w = fam["wife"]
            children = fam["children"]
            
            if h and w and h in people and w in people:
                cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'spouse')", (tree_id, h, w))
                cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'spouse')", (tree_id, w, h))
                rel_count += 2
                
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
                    
            for i in range(len(children)):
                for j in range(i + 1, len(children)):
                    c1, c2 = children[i], children[j]
                    if c1 in people and c2 in people:
                        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'sibling')", (tree_id, c1, c2))
                        cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES (?, ?, ?, 'sibling')", (tree_id, c2, c1))
                        rel_count += 2

        print(f"  ✓ Skráði {rel_count} hrein tengsl.")

    conn.commit()
    conn.close()
    print("\n✅ V2 GRUNNUR ER TILBÚINN FYRIR FRAMHALDIÐ!")

if __name__ == "__main__":
    init_v2_database()
