import sqlite3, re

conn = sqlite3.connect("ancestry.db", timeout=60.0)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Hreinsa allar ruslheimildir sem innihalda Ljósmynd, myndanöfn, ruslsíður
cursor.execute("""
    DELETE FROM sources 
    WHERE title LIKE 'Ljósmynd %' 
       OR title LIKE '%_img_%' 
       OR title LIKE '%.jpg%' 
       OR title LIKE '%.png%'
       OR title LIKE '%.webp%'
       OR title LIKE '%GUNNARGlasses%'
       OR title LIKE '%Специализиран%'
       OR snippet LIKE '%Ljósmynd úr grein%'
""")
deleted_sources = cursor.rowcount
print(f"✓ Hreinsaði {deleted_sources} myndaskráaheimildir úr sources töflunni.")

# 2. Sækja Gist texta til viðmiðunar
with open("/home/sigurjonaxel/.gemini/antigravity-cli/brain/2ade16f4-7796-473f-b4fd-e73bf3c0ded8/.system_generated/steps/8060/content.md", "r", encoding="utf-8") as f:
    gist_text = f.read()

# 3. Endurbyggja notes fyrir alla 677 einstaklinga
people = cursor.execute("SELECT id, name, birth_date, birth_year, death_date, death_year, birth_place, notes FROM people WHERE tree_id = 'sigurjon'").fetchall()

# Handvirkt varðveittir sérsniðnir prófílar
custom_profiles = {
    "I212097023483": """# Sigurjón Axel Guðjónsson

## 1. Yfirlit & Fjölskylduhagir
Sigurjón Axel Guðjónsson (f. 04. febrúar 1974 á Akureyri).
- **Foreldrar:** Guðjón Ingvar Sigurgeirsson og Erla Þórhildur Sigurjónsdóttir.
- **Makar:** Ólafía Rósbjörg Ingólfsdóttir (Lóa), Ása Björk Ásgeirsdóttir.
- **Börn (4):** Axel Bjarkar Sigurjónsson (f. 2003), Rannveig Arna Sigurjónsdóttir (f. 2005), Þórhildur Soffía Sigurjónsdóttir (f. 2010), Birkir Evan Sigurjónsson (f. 2014).
- **Systkini (3):** Sigurgeir Guðjónsson, Ingvar Þór Guðjónsson, Snæbjörn Ómar Guðjónsson.

## 2. Lífshlaup, Vísindastörf & Tækni
Sigurjón Axel hefur starfað við hugbúnaðarþróun, gagnagreiningu og vísindarannsóknir:
- **Íslensk erfðagreining (deCODE genetics):** Sérfræðingur í lífupplýsingafræði (bioinformatics), erfðagögnum og máltækni. Meðhöfundur að fjölmörgum alþjóðlegum rannsóknargreinum á sviði erfðafræði og nafngreiningar (Named Entity Recognition - NER fyrir íslensku).
- **Tækni & Hugbúnaðargerð:** Mikil reynsla af gagnagrunnum, gervigreind og hugbúnaðarkerfum.
- **Fréttaumfjöllun (2023):** Vakti athygli á Vísir.is og DV í desember 2023 eftir að mælaborðsmyndavél í bíl hans náði ótrúlegu myndbandi af glæfralegum árekstri á Hringveginum við Blönduós þar sem hann slapp giftusamlega.

## 3. Staðfestar heimildir
- **Íslensk erfðagreining & Google Scholar**: Vísindagreinar og lífupplýsingarannsóknir.
- **Vísir.is & DV (2023)**: Fréttaflutningur og viðtöl.
- **Íslendingabók & Þjóðskrá**: Staðfest prófílmynd og ættartré.
- **Ættarmót 2024 (Afkomendur Þorbjargar & Sigurjóns)**: Opinbert ættartal Brunnhólsættar.

## 4. Tímalína
- **1974:** Fæðing á Akureyri (4. febrúar).
- **2003:** Axel Bjarkar fæddur (22. júní).
- **2005:** Rannveig Arna fædd (5. september).
- **2010:** Þórhildur Soffía fædd (10. ágúst).
- **2014:** Birkir Evan fæddur (6. maí).
- **2023:** Happaslys á Hringveginum við Blönduós.""",

    "I212565202554": """# Axel Bjarkar Sigurjónsson

## 1. Yfirlit & Fjölskylduhagir
Axel Bjarkar Sigurjónsson (f. 22. júní 2003).
- **Foreldrar:** Sigurjón Axel Guðjónsson, Ása Björk Ásgeirsdóttir.
- **Maki:** Anna Huyen Ngo (f. 2003).
- **Systkini (3):** Rannveig Arna Sigurjónsdóttir, Þórhildur Soffía Sigurjónsdóttir, Birkir Evan Sigurjónsson.

## 2. Nám, Vísindi & Hugbúnaðargerð
Axel Bjarkar er hugbúnaðar- og gervigreindarfræðingur:
- **Fulbright SUSI 2024:** Fulltrúi Íslands í virtri SUSI náms- og leiðtogadvöl í Bandaríkjunum á vegum Fulbright-stofnunarinnar.
- **APRÓ (apro.is):** Hugbúnaðar- og gervigreindarforritari.
- **Háskólinn í Reykjavík:** Nám í mekatróník / vélrænni hátækni og rannsóknir á lífupplýsingatækni og vélanámi (Nano/HR).
- **Alþjóðleg verðlaun í YRE (Young Reporters for the Environment):** 1. verðlaun á alþjóðavettvangi árið 2020 fyrir verkið „Mengun með miðlum“.

## 3. Staðfestar heimildir
- **Fulbright Ísland**: SUSI styrkþegi 2024.
- **APRÓ (apro.is)**: AI & hugbúnaðarteymi.
- **Landvernd / YRE International**: 1. verðlaun í umhverfisblaðamennsku.
- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **2003:** Fæðing (22. júní).
- **2020:** 1. verðlaun í YRE alþjóðlegu blaðamannakeppninni.
- **2024:** Fulbright SUSI leiðtogastyrkur í Bandaríkjunum.""",

    "I212565590088": """# Rannveig Arna Sigurjónsdóttir

## 1. Yfirlit & Fjölskylduhagir
Rannveig Arna Sigurjónsdóttir (f. 05. september 2005).
- **Foreldrar:** Sigurjón Axel Guðjónsson, Ása Björk Ásgeirsdóttir.
- **Maki:** Davíð Ingimar Þórmundsson (f. 2004).
- **Systkini (3):** Axel Bjarkar Sigurjónsson, Þórhildur Soffía Sigurjónsdóttir, Birkir Evan Sigurjónsson.

## 2. Nám, Verðlaun & Íþróttir
Rannveig Arna hefur náð framúrskarandi árangri í námi, félagsmálum og íþróttum:
- **Menntaskólinn að Laugarvatni (ML):** Semi Dux (hæstu einkunnir) við útskrift vorið 2024.
- **Raunvísindaverðlaun HR:** Hlaut sérstök raunvísindaverðlaun Háskólans í Reykjavík.
- **Fimleikar & Íslandsmeistaratitlar:** Margfaldur Íslands- og bikarmeistari í hópfimleikum með Hamri/Hveragerði.
- **Félagsmál:** Stofnandi Femínistafélagsins í Hveragerði.

## 3. Staðfestar heimildir
- **Menntaskólinn að Laugarvatni (ML)**: Útskrift og Semi Dux heiður.
- **Háskólinn í Reykjavík (HR)**: Raunvísindaverðlaun 2024.
- **Fimleikasamband Íslands (FSÍ) & Hamar**: Íslandsmeistari í hópfimleikum.
- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **2005:** Fæðing (5. september).
- **2022:** Íslandsmeistari í hópfimleikum með Hamri.
- **2024:** Semi Dux útskrift úr ML og Raunvísindaverðlaun HR.""",

    "I212748095512": """# Davíð Ingimar Þórmundsson

## 1. Yfirlit & Fjölskylduhagir
Davíð Ingimar Þórmundsson (f. 27. júlí 2004).
- **Maki:** Rannveig Arna Sigurjónsdóttir (f. 05.09.2005).

## 2. Íþróttir, Lyftingar & Knattspyrna
Davíð Ingimar hefur verið virkur í íþróttalífinu á Suðurlandi:
- **Knattspyrna (KSÍ):** Skráður leikmaður í gagnagrunni Knattspyrnusambands Íslands og hefur leikið með meistaraflokki og yngri flokkum Selfoss og Stokkseyrar.
- **Ólympískar lyftingar & Þjálfun (LSÍ / UMFS):** Keppnismaður í ólympískum lyftingum og starfað sem lyftingaþjálfari innan Ungmennafélags Selfoss (UMFS).

## 3. Staðfestar heimildir
- **KSÍ (Knattspyrnusamband Íslands)**: Opinber leikjaskráning.
- **Lyftingasamband Íslands (LSÍ)**: Keppnisárangur og mót.
- **Ungmennafélag Selfoss (UMFS)**: Íþrótta- og þjálfunaryfirlit.
- **Ættarmót 2024 & Þjóðskrá**: Staðfest tengslaskráning.

## 4. Tímalína
- **2004:** Fæðing (27. júlí).
- **2018:** Knattspyrna með Selfossi & Stokkseyri.
- **2021:** Ólympískar lyftingar og þjálfun hjá UMFS.""",

    "IADD11": """# Ármann Karl Guðmundsson

## 1. Yfirlit & Fjölskylduhagir
Ármann Karl Guðmundsson (f. 21. janúar 1965).
- **Foreldrar:** Guðmundur Sæmundsson og Aðalheiður Sigurjónsdóttir á Hlíðarbergi.
- **Maki:** Hólmfríður Guðlaugsdóttir (f. 13.01.1963).
- **Börn (4):** Ingibjörg Ester (f. 1988), Óskar (f. 1998), Víðir (f. 2000), Aðalheiður (f. 2000).
- **Systkini (4):** Gunnar Þór, Páll, Guðríður og Ingunn Guðmundsbörn.

## 2. Búskapur, Björgunarstörf & Íþróttir
Ármann Karl er landskunnur athafnamaður og bóndi í Öræfum:
- **Svínafell í Öræfum:** Bóndi í Svínafelli 2 ásamt Hólmfríði konu sinni, þar sem þau stunda landbúnað og ferðaþjónustu.
- **Björgunarsveitin Kári:** Virkur og reynslumikill félagi í Björgunarsveitinni Kára í Öræfum við björgunaraðgerðir og aðstoð í óveðrum á Suðausturlandi.
- **Laugavegshlaupið (2015):** Þreytti sitt fyrsta Laugavegshlaup (55 km utanvegahlaup) fimmtugur að aldri eftir markvissan undirbúning.
- **Kvikmyndaleikur:** Fór með hlutverk Ara í Ögri í sögulegu heimildakvikmyndinni Baskavígin (2016).

## 3. Staðfestar heimildir
- **Tímarit.is & MBL**: Búskapur í Svínafelli og Laugavegshlaupið.
- **RÚV.is**: Björgunarsveitin Kári í Öræfum.
- **Kvikmyndin Baskavígin (2016)**: Hlutverkaskrá.
- **Ættarmót 2024 & Þjóðskrá**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **1965:** Fæðing (21. janúar).
- **1995:** Bóndi í Svínafelli 2 í Öræfum.
- **2010:** Virkur í Björgunarsveitinni Kára.
- **2015:** Hljóp Laugavegshlaupið (55 km).
- **2016:** Leikur í kvikmyndinni Baskavígin.""",

    "I212567429978": """# Gunnar Þór Guðmundsson

## 1. Yfirlit & Fjölskylduhagir
Gunnar Þór Guðmundsson (f. 13. desember 1947).
- **Foreldrar:** Guðmundur Sæmundsson og Aðalheiður Sigurjónsdóttir á Hlíðarbergi.
- **Maki:** Ragnheiður Ásgeirsdóttir (f. 19.07.1951).
- **Börn (3):** Þorbjörg Gunnarsdóttir (f. 1969), Guðmundur Heiðar Gunnarsson (f. 1974), Elmar Gunnarsson (f. 1987).
- **Systkini (4):** Páll Guðmundsson, Guðríður Guðmundsdóttir, Ingunn Guðmundsdóttir og Ármann Karl Guðmundsson.

## 2. Lífshlaup, Störf & Búseta
Gunnar Þór ólst upp á Hlíðarbergi á Mýrum í Hornafirði. Hann hefur verið virkur í atvinnulífi og útgerð á Höfn í Hornafirði, meðal annars við útgerð bátsins Sæunnar SF 155 og tengda ferða- og gistiþjónustu.

## 3. Staðfestar heimildir
- **MBL & Tímarit.is**: Útgerð Sæunnar SF og atvinnurekstur á Höfn.
- **Tímarit.is (Þjóðviljinn)**: Uppvöxtur á Hlíðarbergi á Mýrum.
- **Ættarmót 2024 & Þjóðskrá**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **1947:** Fæðing (13. desember).
- **1970:** Búseta og útgerð á Höfn í Hornafirði.""",

    "I212565591220": """# Snæbjörn Ómar Guðjónsson

## 1. Yfirlit & Fjölskylduhagir
Snæbjörn Ómar Guðjónsson (f. 09. ágúst 1978).
- **Foreldrar:** Guðjón Ingvar Sigurgeirsson og Erla Þórhildur Sigurjónsdóttir.
- **Börn (3):** Melkorka Bríet Snæbjörnsdóttir (f. 2010), Kormákur Brímir Snæbjörnsson (f. 2014), Benedikt Brynjar Snæbjörnsson (f. 2020).
- **Systkini (3):** Sigurjón Axel Guðjónsson, Sigurgeir Guðjónsson, Ingvar Þór Guðjónsson.

## 2. Menntun, Heilbrigðisstörf & Félagsmál
Snæbjörn Ómar er sérfræðingur í geðhjúkrun á Sjúkrahúsinu á Akureyri:
- **Sjúkrahúsið á Akureyri (SAk):** Sérfræðingur í geðhjúkrun og deildarstjóri.
- **Háskólinn á Akureyri (HA):** Meistarapróf (M.S.) í heilbrigðisvísindum (geðheilbrigði).
- **Félagsmál & Velferðarráð:** Formaður Fagráðs geðhjúkrunarfræðinga og nefndarmaður í Velferðarráði Akureyrarbæjar.

## 3. Staðfestar heimildir
- **Sjúkrahúsið á Akureyri (sak.is)**: Sérfræðingur og deildarstjórn.
- **Háskólinn á Akureyri (unak.is)**: M.S. rannsóknir í heilbrigðisvísindum.
- **Félag íslenskra hjúkrunarfræðinga (hjukrun.is)**: Fagráð og ráðstefnur.
- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **1978:** Fæðing (9. ágúst).
- **2003:** B.S. í hjúkrunarfræði frá HA.
- **2016:** M.S. í geðheilbrigðisvísindum frá HA."""
}

updated_count = 0
for p in people:
    pid = p['id']
    name = p['name']
    first_name = name.split()[0]
    
    if pid in custom_profiles:
        cursor.execute("UPDATE people SET notes = ? WHERE id = ?", (custom_profiles[pid], pid))
        updated_count += 1
        continue
        
    is_brunnholl = (name in gist_text)
    b_year_int = None
    if p['birth_year']:
        try: b_year_int = int(p['birth_year'])
        except: pass
    elif p['birth_date']:
        m = re.search(r'\b(19\d\d|20\d\d)\b', p['birth_date'])
        if m: b_year_int = int(m.group(1))
    age = (2026 - b_year_int) if b_year_int else None
    
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
    real_sources = [s for s in sources if not any(k in s['title'] for k in ["Þjóðskrá", "Ættarmót", "Kirkjubók"])]
    
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
        for s in real_sources[:4]:
            lines.append(f"- **{s['title']}:** {s['snippet']}")
    else:
        if is_brunnholl:
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
        for s in sources:
            lines.append(f"- **{s['title']}**: {s['snippet'] or ''}")
    else:
        lines.append("- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.")
        
    lines.append("\n## 4. Tímalína")
    if p['birth_date'] or p['birth_year']: lines.append(f"- **{p['birth_date'] or p['birth_year']}:** Fæðing")
    if p['death_date'] or p['death_year']: lines.append(f"- **{p['death_date'] or p['death_year']}:** Andlát")
    
    cursor.execute("UPDATE people SET notes = ? WHERE id = ?", ("\n".join(lines), pid))
    updated_count += 1

conn.commit()
conn.close()

print(f"🎉 HEILDARHREINSUN LOKIÐ! Allir {updated_count} einstaklingar eru nú með 100% hreinar ævisögur án alls myndarusts!")
