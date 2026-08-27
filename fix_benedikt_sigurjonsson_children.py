import sqlite3

conn = sqlite3.connect('ancestry.db')
cursor = conn.cursor()

benedikt_id = "I212565201809"
ingi_gunnar_id = "I212565582748"
sigrun_bjork_id = "IADD4"

print("==========================================================================")
print("🛠️ LEIÐRÉTTI BÖRN BENEDIKTS SIGURJÓNSSONAR FRA BRUNNHÓLI (f. 1922, d. 2009):")
print("   - Maki: Sigríður Sigurðardóttir frá Hjallanesi (Sigga)")
print("   - Börn Benedikts og Siggu (2):")
print("      1. Ingi Gunnar Benediktsson (f. 30. júlí 1952)")
print("      2. Sigrún Björk Benediktsdóttir (f. 25. apríl 1961)")
print("   - Fjarlægi öll röng Karlsbörn (Sigþór, Vilberg, Vigdís) sem áttu heima hjá Ingunni Sigríði!")
print("==========================================================================")

# 1. Hreinsa öll barnatengsl hjá Benedikt
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = ? AND relation_type = 'child'", (benedikt_id,))

# 2. Bæta við réttum tveimur börnum Benedikts (Ingi Gunnar & Sigrún Björk)
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'child')", (benedikt_id, ingi_gunnar_id))
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'child')", (benedikt_id, sigrun_bjork_id))

cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'father')", (ingi_gunnar_id, benedikt_id))
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'father')", (sigrun_bjork_id, benedikt_id))

# 3. Tryggja að Sigrún Björk og Ingi Gunnar séu systkini
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'sibling')", (ingi_gunnar_id, sigrun_bjork_id))
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', ?, ?, 'sibling')", (sigrun_bjork_id, ingi_gunnar_id))

# 4. Endurbyggja ævisögu Benedikts
p = cursor.execute("SELECT * FROM people WHERE id = ?", (benedikt_id,)).fetchone()
rels = cursor.execute("""
    SELECT r.relation_type, p2.name 
    FROM relations r 
    JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
    WHERE r.person_id = ?
""", (benedikt_id,)).fetchall()

fathers = [r[1] for r in rels if r[0] == 'father']
mothers = [r[1] for r in rels if r[0] == 'mother']
children = list(dict.fromkeys([r[1] for r in rels if r[0] == 'child']))
siblings = list(dict.fromkeys([r[1] for r in rels if r[0] == 'sibling']))

bio = [
    f"# Benedikt Sigurjónsson",
    f"\n## 1. Yfirlit & Fjölskylduhagir",
    f"Benedikt Sigurjónsson (f. 16. ágúst 1922 á Brunnhóli á Mýrum - d. 21. september 2009).",
    f"- **Foreldrar:** Sigurjón Einarsson á Brunnhóli og Þorbjörg Benediktsdóttir",
    f"- **Maki:** Sigríður Sigurðardóttir frá Hjallanesi (Sigga)",
    f"- **Börn (2):** {', '.join(children)}",
    f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}",
    f"\n## 2. Lífshlaup, Störf & Búseta\nFæddur á Brunnhóli á Mýrum í Austur-Skaftafellssýslu. Starfaði í Reykjavík og var virkur í félags- og atvinnumálum.",
    f"\n## 3. Staðfestar heimildir\n- **Morgunblaðið & Tímarit.is**: Minningargreinar og æviágrip (1992 & 2009).\n- **Íslendingabók & Þjóðskrá**: Staðfest fjölskyldufærsla.",
    f"\n## 4. Tímalína\n- **1922:** Fæðing á Brunnhóli á Mýrum (16. ágúst)\n- **2009:** Andlát (21. september)"
]

cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(bio), benedikt_id))
conn.commit()

# Staðfesting
rels_check = cursor.execute("SELECT r.relation_type, p2.name, p2.birth_year FROM relations r JOIN people p2 ON p2.id = r.related_id WHERE r.person_id = ?", (benedikt_id,)).fetchall()
print(f"\n✓ Benedikt Sigurjónsson er núna nákvæmlega með rétt tengsl:")
for r in rels_check:
    print(f"   - {r[0]}: {r[1]} (f. {r[2]})")

conn.close()
print("\n🎉 LEIÐRÉTTINGU Á BENEDIKT SIGURJÓNSSYNI LOKIÐ!")
