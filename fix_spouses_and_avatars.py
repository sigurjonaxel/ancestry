import os, re, sqlite3, glob

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

print("=== 1. HREINSA SPURIOUS OG TVÖFALDAN MAKA ===")

# Delete artificial I_ADD spouse duplicate for Sigurjón Axel (keep real I212565585214)
conn.execute("DELETE FROM relations WHERE person_id='I212097023483' AND related_id='I_ADD_501'")
conn.execute("DELETE FROM relations WHERE person_id='I_ADD_501' AND related_id='I212097023483'")
conn.execute("DELETE FROM people WHERE id='I_ADD_501'")

# Delete fake I_ADD_500 for Axel Bjarkar
conn.execute("DELETE FROM relations WHERE person_id='I212565202554' AND related_id='I_ADD_500'")
conn.execute("DELETE FROM relations WHERE person_id='I_ADD_500' AND related_id='I212565202554'")
conn.execute("DELETE FROM people WHERE id='I_ADD_500'")

# Delete any fake/spurious IADD relations linked to Karl Björnsson, Guðmundur Sæmundsson, etc.
for pid in ['IADD142', 'IADD146', 'IADD158', 'IADD159', 'IADD160', 'IADD161', 'IADD162', 'IADD163', 'IADD164', 'IADD165', 'IADD166', 'IADD167', 'IADD168', 'IADD169', 'IADD170', 'IADD171', 'IADD172', 'IADD173', 'IADD174', 'IADD175', 'IADD176', 'IADD177', 'IADD178', 'IADD179', 'IADD180', 'IADD181', 'IADD183', 'IADD184', 'IADD185', 'IADD186', 'IADD187', 'IADD188', 'IADD189', 'IADD190', 'IADD191', 'IADD192', 'IADD193', 'IADD194', 'IADD195', 'IADD196', 'IADD197', 'IADD198', 'IADD199', 'IADD202', 'IADD203', 'IADD204', 'IADD205', 'IADD206', 'IADD207', 'IADD208', 'IADD209', 'IADD210', 'IADD211', 'IADD212', 'IADD213', 'IADD214', 'IADD215', 'IADD216', 'IADD156', 'IADD157']:
    conn.execute("DELETE FROM relations WHERE person_id=? OR related_id=?", (pid, pid))
    conn.execute("DELETE FROM people WHERE id=?", (pid,))

# Refresh Sigurjón Axel bio note
for pid in ['I212097023483']:
    p = conn.execute("SELECT * FROM people WHERE id=?", (pid,)).fetchone()
    rels = conn.execute("""
        SELECT r.relation_type, p2.name 
        FROM relations r 
        JOIN people p2 ON p2.id=r.related_id 
        WHERE r.person_id=?
    """, (pid,)).fetchall()
    
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
    if children: lines.append(f"- **Börn:** {', '.join(children)}")
    if siblings: lines.append(f"- **Systkini:** {', '.join(siblings)}")
    lines.append("\n## 2. Staðfestar heimildir\n- **Ættartré & Þjóðskrá**: Staðfest færsla í ættartrénu.")
    lines.append("\n## 3. Tímalína")
    lines.append(f"- **1974:** Fæðing á Akureyri")
    conn.execute("UPDATE people SET notes=? WHERE id=?", ("\n".join(lines), pid))

print("✓ Spurious spouses hreinsaðir!")

print("\n=== 2. TENGJA MYNDIR ÚR IMAGES/CACHE VIÐ ALLA EINSTAKLINGA KERFISBUNDIÐ ===")
# Set avatar for key ancestors and match existing cache
avatar_mappings = {
    "I212097023483": "images/cache/ib_7750895_1.jpg",
    "I212565204711": "images/cache/ib_6203244_1.jpg", # Einar Sigjón Þorvarðarson
    "I212565580541": "images/cache/ib_15509356_1.jpg", # Ingunn Jónsdóttir
    "I212565204698": "images/cache/ib_10397548_1.jpg", # Benedikt Kristjánsson
    "I212565204661": "images/cache/ib_7251820_1.jpg", # Álfheiður Sigurðardóttir
    "I212565201500": "images/cache/ib_520612_1.jpg", # Sigurgeir Guðmundsson
    "I212565201521": "images/cache/ib_9422395_1.jpg", # Þóra Ingibjörg Sigurjónsdóttir
    "I212565201806": "images/cache/ib_5023596_1.jpg", # Þorbjörg Benediktsdóttir
    "IADD231": "images/cache/ib_6072172_1.jpg", # Sigurborg Einarsdóttir
    "IADD233": "images/cache/ib_9000605_1.jpg", # Guðleif Einarsdóttir
    "IADD236": "images/cache/ib_1615662_1.jpg", # Kristján Benediktsson
    "IADD239": "images/cache/ib_3319660_1.jpg", # Unnar Benediktsson
    "I212565580190": "images/cache/ib_1809924_1.jpg", # Bergur Benediktsson
    "I212565603296": "images/cache/ib_10856300_1.jpg", # Guðrún Benediktsdóttir
    "IADD2": "images/cache/ib_8712540_1.jpg", # Rannveig Einarsdóttir
    "I272771958737": "images/cache/I272771958737_img_0.jpg", # Lóa
}

# Auto-match by person ID in cache
for img_path in glob.glob("images/cache/*"):
    basename = os.path.basename(img_path)
    # Check if starts with person ID (e.g. I212097023483_..., I272771958754_...)
    m = re.match(r"(I[0-9A-Z_]+?)_", basename)
    if m:
        pid = m.group(1)
        if pid not in avatar_mappings:
            avatar_mappings[pid] = img_path

for pid, av_path in avatar_mappings.items():
    if os.path.exists(av_path):
        conn.execute("UPDATE people SET avatar_url=? WHERE id=?", (av_path, pid))
        print(f"  📷 Tengdi mynd við {pid}: {av_path}")

conn.commit()
conn.close()
print("\n🎉 Búið að laga maka og tengja allar prófílmyndir!")
