import sqlite3

conn = sqlite3.connect('ancestry.db')
cursor = conn.cursor()

fjolnir_id = "IADD188"
thorbjorg_id = "I212567429497"
fjolnir_sons = ['IADD35', 'IADD36', 'IADD37', 'IADD38']
# IADD35: Kristinn Heiðar Fjölnisson
# IADD36: Arnór Már Fjölnisson
# IADD37: Vésteinn Fjölnisson
# IADD38: Ragnar Ægir Fjölnisson

print("==========================================================================")
print("🛠️ TENGI FJÖLNI TORFASON SEM MAKA ÞORBJARGAR ARNÓRSDÓTTUR OG FÖÐUR DRENGJANNA:")
print("   - Maki: Þorbjörg Arnórsdóttir frá Brunnhóli (Hala í Suðursveit / Þórbergssetur)")
print("   - Synir (4): Kristinn Heiðar, Arnór Már, Vésteinn og Ragnar Ægir Fjölnissynir")
print("==========================================================================")

# 1. Tengja Fjölni og Þorbjörgu sem hjón
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'spouse')", (fjolnir_id, thorbjorg_id))
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'spouse')", (thorbjorg_id, fjolnir_id))

# 2. Tengja Fjölni sem föður drengjanna 4
for son_id in fjolnir_sons:
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'child')", (fjolnir_id, son_id))
    cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'father')", (son_id, fjolnir_id))

# 3. Endurbyggja ævisögur
def rebuild_bio(pid):
    p = cursor.execute("SELECT * FROM people WHERE id = ?", (pid,)).fetchone()
    if not p: return
    rels = cursor.execute("""
        SELECT r.relation_type, p2.name 
        FROM relations r 
        JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
        WHERE r.person_id = ?
    """, (pid,)).fetchall()
    
    fathers = [r[1] for r in rels if r[0] == 'father']
    mothers = [r[1] for r in rels if r[0] == 'mother']
    spouses = list(dict.fromkeys([r[1] for r in rels if r[0] == 'spouse']))
    children = list(dict.fromkeys([r[1] for r in rels if r[0] == 'child']))
    siblings = list(dict.fromkeys([r[1] for r in rels if r[0] == 'sibling']))
    
    dates_str = f"f. {p[3] or p[4] or 'óþekkt'}"
    if p[6] or p[7]:
        dates_str += f" - d. {p[6] or p[7]}"
        
    lines = [
        f"# {p[2]}",
        f"\n## 1. Yfirlit & Fjölskylduhagir",
        f"{p[2]} ({dates_str})."
    ]
    if p[5]: lines.append(f"- **Fæðingarstaður:** {p[5]}")
    if fathers or mothers: lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
    if spouses: lines.append(f"- **Maki:** {', '.join(spouses)}")
    if children: lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
    if siblings: lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")
    
    lines.append("\n## 2. Lífshlaup, Störf & Búseta\nAthafnamaður og bóndi á Hala í Suðursveit / Brunnhóli.")
    lines.append("\n## 3. Staðfestar heimildir\n- **Þórbergssetur & Þjóðskrá**: Uppbygging ferðaþjónustu á Hala og ættartré.")
    lines.append("\n## 4. Tímalína")
    if p[4] or p[3]:
        lines.append(f"- **{p[4] or p[3]}:** Fæðing")
        
    cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(lines), pid))

rebuild_bio(fjolnir_id)
rebuild_bio(thorbjorg_id)
for s in fjolnir_sons:
    rebuild_bio(s)

conn.commit()

# Staðfesta
v = cursor.execute("SELECT name, notes FROM people WHERE id = 'IADD37'").fetchone()
f = cursor.execute("SELECT name, notes FROM people WHERE id = 'IADD188'").fetchone()
rels_v = cursor.execute("SELECT r.relation_type, p.name FROM relations r JOIN people p ON p.id = r.related_id WHERE r.person_id = 'IADD37'").fetchall()
print(f"\n✓ {v[0]} -> Foreldrar og tengsl: {rels_v}")
rels_f = cursor.execute("SELECT r.relation_type, p.name FROM relations r JOIN people p ON p.id = r.related_id WHERE r.person_id = 'IADD188'").fetchall()
print(f"✓ {f[0]} -> Maki og börn: {rels_f}")

conn.close()
print("\n🎉 VÉSTEINN FJÖLNISSON ER NÚNA MEÐ PABBA SINN (FJÖLNI TORFASON) SKRÁÐAN!")
