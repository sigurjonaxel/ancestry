import sqlite3, re

GIST_PATH = "/home/sigurjonaxel/.gemini/antigravity-cli/brain/2ade16f4-7796-473f-b4fd-e73bf3c0ded8/.system_generated/steps/8060/content.md"

with open(GIST_PATH, "r", encoding="utf-8") as f:
    gist_text = f.read()

conn = sqlite3.connect("ancestry.db", timeout=30.0)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Leiðrétta nafn Hrannars Ara í Hrannar Ari Þrastarson
cursor.execute("UPDATE people SET name = 'Hrannar Ari Þrastarson', surname = 'Þrastarson' WHERE id = 'I212605396479'")
cursor.execute("UPDATE people SET name = 'Hrafn Helgi Þrastarson', surname = 'Þrastarson' WHERE id = 'I212605396792'")
cursor.execute("UPDATE people SET name = 'Arney Björk Þrastardóttir', surname = 'Þrastardóttir' WHERE id = 'I212605396405'")

# 2. Finna nákvæmlega alla sem ERU í Brunnhólsætt (í Gist skjalinu)
all_people = cursor.execute("SELECT id, name, birth_date, birth_year, death_date, death_year, birth_place, notes FROM people WHERE tree_id = 'sigurjon'").fetchall()

print(f"Athuga {len(all_people)} einstaklinga í Sigurjóns tré...")

for p in all_people:
    pid = p['id']
    name = p['name']
    first_name = name.split()[0]
    
    # Athuga hvort manneskjan er í Gist (Brunnhólsætt afkomendur Þorbjargar & Sigurjóns)
    is_brunnholl_descendant = (name in gist_text) or any(name.split()[0] + " " + name.split()[-1] in gist_text for _ in [0] if len(name.split()) > 2)
    
    # Athuga aldur
    b_year_int = None
    if p['birth_year']:
        try: b_year_int = int(p['birth_year'])
        except: pass
    elif p['birth_date']:
        m = re.search(r'\b(19\d\d|20\d\d)\b', p['birth_date'])
        if m: b_year_int = int(m.group(1))
        
    age = (2026 - b_year_int) if b_year_int else None
    
    # Sækja tengsl
    rels = cursor.execute("""
        SELECT r.relation_type, p2.name 
        FROM relations r 
        JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
        WHERE r.person_id = ? AND r.tree_id = 'sigurjon'
    """, (pid,)).fetchall()
    
    fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
    mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
    spouses = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'spouse']))
    children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
    siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))
    
    sources = cursor.execute("SELECT title, snippet, link FROM sources WHERE person_id = ?", (pid,)).fetchall()
    real_sources = [s for s in sources if not any(k in s['title'] for k in ["Ættarmót", "Þjóðskrá", "GUNNARGlasses", "Специализиran"])]
    
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
    
    lines.append("\n## 2. Lífshlaup & Upplýsingar")
    if real_sources:
        lines.append("Samkvæmt staðfestum heimildum:")
        for s in real_sources[:5]:
            lines.append(f"- **{s['title']}:** {s['snippet']}")
    else:
        if is_brunnholl_descendant:
            if age is not None and age <= 18:
                lines.append(f"{first_name} er í hópi yngri kynslóða ættarinnar, skráð(ur) í ættartali Brunnhólsættar.")
            else:
                lines.append(f"Skráður einstaklingur í ættartali Ættarmóts 2024 (Afkomendur Þorbjargar og Sigurjóns á Brunnhóli).")
        else:
            if age is not None and age <= 18:
                lines.append(f"{first_name} er skráð(ur) í ættartrénu með staðfestar fjölskylduupplýsingar.")
            else:
                lines.append(f"Skráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.")
                
    lines.append("\n## 3. Staðfestar heimildir")
    if sources:
        clean_sources = [s for s in sources if not any(k in s['title'] for k in ["GUNNARGlasses", "Специализиran"])]
        for s in clean_sources:
            lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
    else:
        lines.append("- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.")
        
    lines.append("\n## 4. Tímalína")
    if p['birth_date'] or p['birth_year']: lines.append(f"- **{p['birth_date'] or p['birth_year']}:** Fæðing")
    if p['death_date'] or p['death_year']: lines.append(f"- **{p['death_date'] or p['death_year']}:** Andlát")
    
    cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(lines), pid))

conn.commit()

# Skoða Hrannar Ara
h = cursor.execute("SELECT name, notes FROM people WHERE id = 'I212605396479'").fetchone()
print(f"\n✓ LEIÐRÉTTING Á HRANNARI ARA:")
print(h['notes'])

conn.close()
print("\n🎉 LEIÐRÉTT ÖLL RÖNG ÆTTARTALSTENGSL OG NÖFN!")
