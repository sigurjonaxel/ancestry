import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# 1. Add Lóa (Ólafía Rósbjörg Ingólfsdóttir) as spouse in 'sigurjon' tree
conn.execute("""
    INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, avatar_url, notes)
    VALUES ('I_ADD_LOA_I212097023483', 'sigurjon', 'Ólafía Rósbjörg Ingólfsdóttir', 'F', '19. okt. 1978', '1978', 
            'images/cache/I272771958737_img_0.jpg', 
            '# Ólafía Rósbjörg Ingólfsdóttir\n\n## 1. Yfirlit & Fjölskylda\nÓlafía Rósbjörg Ingólfsdóttir (Lóa), f. 19. okt. 1978.\n- **Maki:** Sigurjón Axel Guðjónsson.\n\n*(Smelltu á prófílinn til að hoppa beint yfir í ættartré Lóu).*')
""")

conn.execute("""
    INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type)
    VALUES ('sigurjon', 'I212097023483', 'I_ADD_LOA_I212097023483', 'spouse')
""")
conn.execute("""
    INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type)
    VALUES ('sigurjon', 'I_ADD_LOA_I212097023483', 'I212097023483', 'spouse')
""")

# 2. Add Sigurjón Axel as spouse in 'loa' tree
conn.execute("""
    INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, avatar_url, notes)
    VALUES ('I_ADD_100', 'loa', 'Sigurjón Axel Guðjónsson', 'M', '4. feb. 1974', '1974', 
            'images/cache/ib_7750895_1.jpg', 
            '# Sigurjón Axel Guðjónsson\n\n## 1. Yfirlit & Fjölskylda\nSigurjón Axel Guðjónsson, f. 4. feb. 1974.\n- **Maki:** Ólafía Rósbjörg Ingólfsdóttir.\n\n*(Smelltu á prófílinn til að hoppa beint yfir í ættartré Sigurjóns).*')
""")

conn.execute("""
    INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type)
    VALUES ('loa', 'I272771958737', 'I_ADD_100', 'spouse')
""")
conn.execute("""
    INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type)
    VALUES ('loa', 'I_ADD_100', 'I272771958737', 'spouse')
""")

# 3. Update Sigurjón Axel note in 'sigurjon' tree to show both Ása Björk and Ólafía Rósbjörg (Lóa)
p = conn.execute("SELECT * FROM people WHERE id='I212097023483'").fetchone()
rels = conn.execute("""
    SELECT r.relation_type, p2.name 
    FROM relations r 
    JOIN people p2 ON p2.id=r.related_id 
    WHERE r.person_id='I212097023483'
""").fetchall()

fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
spouses = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'spouse']))
children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))

dates_str = f"f. {p['birth_date'] or p['birth_year'] or 'óþekkt'}"
lines = [f"# {p['name']}", f"\n## 1. Yfirlit & Fjölskylda", f"{p['name']} ({dates_str})."]
if p['birth_place']: lines.append(f"- **Fæðingarstaður:** {p['birth_place']}")
if fathers or mothers: lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
if spouses: lines.append(f"- **Maki:** {', '.join(spouses)}")
if children: lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
if siblings: lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")
lines.append("\n## 2. Staðfestar heimildir\n- **Ættartré & Þjóðskrá**: Staðfest færsla í ættartrénu.")
lines.append("\n## 3. Tímalína")
lines.append(f"- **1974:** Fæðing á Akureyri")
conn.execute("UPDATE people SET notes=? WHERE id='I212097023483'", ("\n".join(lines),))

conn.commit()
conn.close()
print("🎉 Lóa og Sigurjón Axel tengd rétt sem kross-ættartrés makar!")
