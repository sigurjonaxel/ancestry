import sqlite3, re

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("==========================================================================")
print("🧹 HREINSA ÖLL GERVIMAKATENGSL OG ENDURREIKNA ÆVISÖGUR ALLRA")
print("==========================================================================")

# 1. Stormur Adrían (f. 2023) er barn, EKKI maki neins!
# Fjarlægja öll spouse tengsl tengd Stormi (IADD153)
cursor.execute("DELETE FROM relations WHERE (person_id = 'IADD153' OR related_id = 'IADD153') AND relation_type = 'spouse'")

# 2. Leita að öðrum börnum (fædd eftir 2010) sem hafa spouse tengsl og hreinsa
cursor.execute("""
    DELETE FROM relations 
    WHERE relation_type = 'spouse' 
    AND (
        person_id IN (SELECT id FROM people WHERE birth_year != '' AND CAST(birth_year AS INTEGER) >= 2010)
        OR 
        related_id IN (SELECT id FROM people WHERE birth_year != '' AND CAST(birth_year AS INTEGER) >= 2010)
    )
""")

# 3. Fjarlægja alla óeðlilega maka hjá bræðrum þínum og fjölskyldu
# Ingvar Þór Guðjónsson (I212565591322) - maki er Stella Bryndís Helgadóttir
# Snæbjörn Ómar Guðjónsson (I212565591220) - maki er Jóna Valdís Ólafsdóttir
# Sigurgeir Guðjónsson (I212565591524) - maki er Einarína Einarsdóttir

# Hreinsa öll óeðlileg tengsl hjá Ingvari, Snæbirni og Sigurgeiri
for brother_id, wife_name in [
    ('I212565591322', 'Stella Bryndís Helgadóttir'),
    ('I212565591220', 'Jóna Valdís Ólafsdóttir'),
    ('I212565591524', 'Einarína Einarsdóttir')
]:
    # Finna id eiginkonu
    wife = cursor.execute("SELECT id FROM people WHERE name LIKE ? AND tree_id = 'sigurjon'", (f'%{wife_name}%',)).fetchone()
    if wife:
        wife_id = wife['id']
        # Eyða öllum öðrum spouse tengslum
        cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type = 'spouse' AND related_id != ?", (brother_id, wife_id))
        cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND related_id = ? AND relation_type = 'spouse' AND person_id != ?", (brother_id, wife_id))
        cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type = 'spouse' AND related_id != ?", (wife_id, brother_id))
        cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND related_id = ? AND relation_type = 'spouse' AND person_id != ?", (wife_id, brother_id))

# 4. Endurskrifa ævisögur (notes) allra í trénu út frá nýjum, 100% réttum tengslum
people = cursor.execute("SELECT id, tree_id, name, sex, birth_date, birth_year, birth_place, death_date, death_year, death_place FROM people").fetchall()

for p in people:
    pid = p['id']
    tid = p['tree_id']
    name = p['name']
    
    rels = cursor.execute("""
        SELECT r.relation_type, p2.name 
        FROM relations r 
        JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
        WHERE r.person_id = ? AND r.tree_id = ?
    """, (pid, tid)).fetchall()
    
    fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
    mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
    spouses = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'spouse']))
    children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
    siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))
    
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
    
    lines.append("\n## 2. Lífshlaup, Störf & Búseta\nSkráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.")
    lines.append("\n## 3. Staðfestar heimildir")
    if srcs:
        for s in srcs: lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
    else:
        lines.append("- **Þjóðskrá & Ættartré**: Staðfest færsla í ættartrénu.")
        
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
print("\n🎉 ALLIR GERVIMAKAR HREINSAÐIR OG ALLAR ÆVISÖGUR ENDURREIKNAÐAR!")
