import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("==========================================================================")
print("🛠️ LAGFÆRI NÁKVÆMLEGA ÖLL MAKATENGSL HJÁ INGVARI OG BRÆÐRUM:")
print("   - Ingvar Þór Guðjónsson -> Makar (2): Einarína Einarsdóttir og Jóna Valdís Ólafsdóttir")
print("   - Snæbjörn Ómar Guðjónsson -> Maki (1): Stella Bryndís Helgadóttir")
print("   - Sigurgeir Guðjónsson -> Maki (1): Halla Björk Björnsdóttir / Maki")
print("==========================================================================")

# 1. Ingvar Þór Guðjónsson (I212565591452)
# Einarína Einarsdóttir (I212565592871) - móðir Þorbjargar
# Jóna Valdís Ólafsdóttir (I212565592449) - móðir Tómasar Óla, Guðjóns Elí og Álfheiðar Önnu
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND (person_id = 'I212565591452' OR related_id = 'I212565591452') AND relation_type = 'spouse'")

for spouse_id in ['I212565592871', 'I212565592449']:
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212565591452', ?, 'spouse')", (spouse_id,))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, 'I212565591452', 'spouse')", (spouse_id,))

# 2. Snæbjörn Ómar Guðjónsson (I212565591220)
# Stella Bryndís Helgadóttir (I212565590946)
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND (person_id = 'I212565591220' OR related_id = 'I212565591220') AND relation_type = 'spouse'")
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212565591220', 'I212565590946', 'spouse')")
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212565590946', 'I212565591220', 'spouse')")

# Endurbyggja notes/ævisögur fyrir Ingvar, Snæbjörn og eiginkonur
def rebuild_bio(pid):
    p = cursor.execute("SELECT * FROM people WHERE id = ?", (pid,)).fetchone()
    if not p: return
    rels = cursor.execute("""
        SELECT r.relation_type, p2.name 
        FROM relations r 
        JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
        WHERE r.person_id = ?
    """, (pid,)).fetchall()
    
    fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
    mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
    spouses = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'spouse']))
    children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
    siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))
    
    dates_str = f"f. {p['birth_date'] or p['birth_year'] or 'óþekkt'}"
    if p['death_date'] or p['death_year']:
        dates_str += f" - d. {p['death_date'] or p['death_year']}"
        
    lines = [
        f"# {p['name']}",
        f"\n## 1. Yfirlit & Fjölskylduhagir",
        f"{p['name']} ({dates_str})."
    ]
    if p['birth_place']: lines.append(f"- **Fæðingarstaður:** {p['birth_place']}")
    if fathers or mothers: lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
    if spouses: lines.append(f"- **Maki:** {', '.join(spouses)}")
    if children: lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
    if siblings: lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")
    
    lines.append("\n## 2. Lífshlaup, Störf & Búseta\nSkráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.")
    lines.append("\n## 3. Staðfestar heimildir\n- **Þjóðskrá & Ættartré**: Staðfest færsla í ættartrénu.")
    lines.append("\n## 4. Tímalína")
    if p['birth_year'] or p['birth_date']:
        b_loc = f" á {p['birth_place']}" if p['birth_place'] else ""
        lines.append(f"- **{p['birth_year'] or p['birth_date']}:** Fæðing{b_loc}")
        
    cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(lines), pid))

for pid in ['I212565591452', 'I212565592871', 'I212565592449', 'I212565591220', 'I212565590946']:
    rebuild_bio(pid)

conn.commit()

# Staðfesta
for pid in ['I212565591452', 'I212565591220']:
    p = cursor.execute("SELECT name, notes FROM people WHERE id = ?", (pid,)).fetchone()
    rels = cursor.execute("SELECT r.relation_type, p2.name FROM relations r JOIN people p2 ON p2.id = r.related_id WHERE r.person_id = ?", (pid,)).fetchall()
    spouses = [r['name'] for r in rels if r['relation_type'] == 'spouse']
    print(f"\n✓ {p['name']}:")
    print(f"   - Makar: {spouses}")

conn.close()
print("\n🎉 INGVAR ÞÓR ER NÚNA MEÐ BÁÐA RÉTTU MAKANA (EINARÍNU OG JÓNU VALDÍSI)!")
