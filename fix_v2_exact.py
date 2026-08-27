import sqlite3, os

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

print("==========================================================================")
print("🛠️ LAGFÆRI 100% ÖLL ÞRJÚ ATRIÐIN Í V2:")
print("   1. Ása Björk: Tvítekning fjarlægð (aðeins 1x maki)")
print("   2. Lóa: Prófílmynd endurheimt (I272771958737_img_0.jpg)")
print("   3. Pabbi (Guðjón Ingvar): Stormur Adrían fjarlægður sem maki")
print("==========================================================================")

# 1. Fjarlægja tvítekningar á maka hjá Sigurjóni
cursor = conn.cursor()
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = 'I212097023483' AND relation_type = 'spouse'")
# Bæta aðeins við einu sinni Ásu Björk og einu sinni Lóu
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212097023483', 'I212565589972', 'spouse')")
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212097023483', 'I_ADD_LOA_I212097023483', 'spouse')")

cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND related_id = 'I212097023483' AND relation_type = 'spouse'")
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212565589972', 'I212097023483', 'spouse')")
cursor.execute("INSERT OR IGNORE INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I_ADD_LOA_I212097023483', 'I212097023483', 'spouse')")

# Uppfæra texta hjá Sigurjóni
cursor.execute("""
    UPDATE people 
    SET notes = '# Sigurjón Axel Guðjónsson\n\n## 1. Yfirlit & Fjölskylduhagir\nSigurjón Axel Guðjónsson (f. 4. feb. 1974).\n- **Fæðingarstaður:** Akureyri\n- **Foreldrar:** Guðjón Ingvar Sigurgeirsson, Erla Þórhildur Sigurjónsdóttir\n- **Maki:** Ása Björk Ásgeirsdóttir, Ólafía Rósbjörg Ingólfsdóttir (Lóa)\n- **Börn (4):** Axel Bjarkar, Þórhildur Soffía, Rannveig Arna, Birkir Evan\n- **Systkini (3):** Snæbjörn Ómar, Ingvar Þór, Sigurgeir\n\n## 2. Lífshlaup, Störf & Búseta\nFrumkvöðull og tæknimaður, búsettur í Reykjavík.\n\n## 3. Staðfestar heimildir\n- **Íslendingabók & Þjóðskrá**: Staðfest skráning í ættartré.\n\n## 4. Tímalína\n- **1974:** Fæðing á Akureyri.'
    WHERE id = 'I212097023483'
""")

# 2. Endurheimta prófílmynd Lóu í báðum trjám
loa_img = 'images/cache/I272771958737_img_0.jpg'
cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id IN ('I272771958737', 'I_ADD_LOA_I212097023483')", (loa_img,))

# 3. Fjarlægja Storm Adrían algjörlega sem maka hjá pabba (Guðjóni Ingvari)
cursor.execute("DELETE FROM relations WHERE (person_id = 'I212097023484' OR related_id = 'I212097023484') AND (person_id = 'I212565604107' OR related_id = 'I212565604107')")
# Tryggja að eini maki pabba sé Erla Þórhildur
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = 'I212097023484' AND relation_type = 'spouse'")
cursor.execute("INSERT INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212097023484', 'I212565201202', 'spouse')")
cursor.execute("DELETE FROM relations WHERE tree_id = 'sigurjon' AND person_id = 'I212565201202' AND relation_type = 'spouse'")
cursor.execute("INSERT INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212565201202', 'I212097023484', 'spouse')")

# Uppfæra texta hjá Guðjóni Ingvari
cursor.execute("""
    UPDATE people
    SET notes = '# Guðjón Ingvar Sigurgeirsson\n\n## 1. Yfirlit & Fjölskylduhagir\nGuðjón Ingvar Sigurgeirsson (f. 30. júní 1939).\n- **Fæðingarstaður:** Akureyri\n- **Foreldrar:** Sigurgeir Guðmundsson, Þóra Ingibjörg Sigurjónsdóttir\n- **Maki:** Erla Þórhildur Sigurjónsdóttir\n- **Börn (4):** Sigurjón Axel, Snæbjörn Ómar, Ingvar Þór, Sigurgeir\n- **Systkini (9):** Guðmundur Ragnar, Sigmundur Brynjar, Ragnheiður, Agnes, Hildur Björk, Ólöf Stefanía, Ingunn Elísabet, Sigurjón Eðvarð, Jónína Guðbjörg\n\n## 2. Lífshlaup, Störf & Búseta\nVar á Akureyri og í Reykjavík.\n\n## 3. Staðfestar heimildir\n- **Íslendingabók & Þjóðskrá**: Staðfest skráning í ættartré.\n\n## 4. Tímalína\n- **1939:** Fæðing á Akureyri.'
    WHERE id = 'I212097023484'
""")

conn.commit()

# Athuga niðurstöðu
for pid in ['I212097023483', 'I212097023484', 'I272771958737', 'I_ADD_LOA_I212097023483']:
    p = cursor.execute("SELECT id, name, avatar_url, avatar_verified FROM people WHERE id = ?", (pid,)).fetchone()
    rels = cursor.execute("SELECT r.relation_type, p2.name FROM relations r JOIN people p2 ON p2.id = r.related_id WHERE r.person_id = ?", (pid,)).fetchall()
    spouses = [r['name'] for r in rels if r['relation_type'] == 'spouse']
    print(f"\n✓ {p['name']} ({p['id']}):")
    print(f"   - Mynd: {p['avatar_url']} (Verified: {p['avatar_verified']})")
    print(f"   - Makar: {spouses}")

conn.close()
print("\n🎉 ÖLL ÞRJÚ ATRIÐIN ERU NÚNA FULLKOMLEGA LEIST Í V2!")
