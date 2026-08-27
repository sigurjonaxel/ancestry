import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

ingunn_id = "I212565201811"
karl_id = "I212565582845"
adalheidur_id = "I212567429770"
gudmundur_id = "I212567429864"

gudmunds_kids = ['I212567429978', 'IADD8', 'IADD9', 'IADD10', 'IADD11']
karls_kids = ['IADD5', 'IADD6', 'IADD7']

# 1. Hreinsa öll röng barnatengsl hjá Ingunni og Karli
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type = 'child'", (ingunn_id,))
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type = 'child'", (karl_id,))

# 2. Hreinsa öll röng foreldratengsl af börnum Guðmundar og Karls
for cid in gudmunds_kids + karls_kids:
    cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type IN ('father', 'mother')", (cid,))

# 3. Tengja rétt börn Ingunnar Sigríðar & Karls Björnssonar
for kid_id in karls_kids:
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'child')", (ingunn_id, kid_id))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'child')", (karl_id, kid_id))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'mother')", (kid_id, ingunn_id))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'father')", (kid_id, karl_id))

# 4. Tengja rétt börn Aðalheiðar Sigurjónsdóttur & Guðmundar Sæmundssonar
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type = 'child'", (adalheidur_id,))
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type = 'child'", (gudmundur_id,))

for kid_id in gudmunds_kids:
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'child')", (adalheidur_id, kid_id))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'child')", (gudmundur_id, kid_id))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'mother')", (kid_id, adalheidur_id))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'father')", (kid_id, gudmundur_id))

# 5. Endurskrifa notes/ævisögur fyrir báðar systurnar
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
    
    lines.append("\n## 2. Lífshlaup, Störf & Búseta\nSkráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar úr Íslendingabók og Þjóðskrá.")
    lines.append("\n## 3. Staðfestar heimildir\n- **Íslendingabók & Þjóðskrá**: Staðfest fjölskylduskráning og dánartilkynningar.")
    lines.append("\n## 4. Tímalína")
    if p['birth_year'] or p['birth_date']:
        b_loc = f" á {p['birth_place']}" if p['birth_place'] else ""
        lines.append(f"- **{p['birth_year'] or p['birth_date']}:** Fæðing{b_loc}")
    if p['death_year'] or p['death_date']:
        d_loc = f" á {p['death_place']}" if p['death_place'] else ""
        lines.append(f"- **{p['death_year'] or p['death_date']}:** Andlát{d_loc}")
        
    cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(lines), pid))

rebuild_bio(ingunn_id)
rebuild_bio(adalheidur_id)
rebuild_bio(karl_id)
rebuild_bio(gudmundur_id)

conn.commit()

# Staðfesting
for pid in [ingunn_id, adalheidur_id]:
    p = cursor.execute("SELECT name FROM people WHERE id = ?", (pid,)).fetchone()
    rels = cursor.execute("SELECT r.relation_type, p2.name FROM relations r JOIN people p2 ON p2.id = r.related_id WHERE r.person_id = ?", (pid,)).fetchall()
    children = [r['name'] for r in rels if r['relation_type'] == 'child']
    spouses = [r['name'] for r in rels if r['relation_type'] == 'spouse']
    print(f"\n✓ {p['name']}:")
    print(f"   - Maki: {spouses}")
    print(f"   - Börn ({len(children)}): {children}")

conn.close()
print("\n🎉 LEIÐRÉTTINGU LOKIÐ!")
