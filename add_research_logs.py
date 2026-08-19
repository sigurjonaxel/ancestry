import sys
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def add_logs_to_sigurjon():
    blocks = parse_gedcom_blocks('sigurjon.ged')
    
    logs = {
        'I212565201805': (
            "[Lokið] Rannsóknarferill:\n"
            "● Aðferð: Innskráð leit (Íslendingabók)\n"
            "   - Aðgerð: Leitað að alsystkinum Sigurjóns Einarssonar (f. 1895).\n"
            "   - Niðurstaða: Fundust 7 alsystkini sem vantaði í tréð. Þau voru skráð og tengd (Guðný, Jón, Þorbjörg, Sigurborg, Stefán, Guðleif).\n"
            "● Aðferð: Vefleit (Tímarit.is & Morgunblaðið)\n"
            "   - Aðgerð: Leitað að andláts- og útfarartilkynningum (d. 1983).\n"
            "   - Niðurstaða: Staðfest andlát 28. febrúar 1983. Jarðsunginn frá Brunnhólskirkju 7. mars 1983. Gullbrúðkaupsafmæli (1969) staðfest."
        ),
        'I212565201806': (
            "[Lokið] Rannsóknarferill:\n"
            "● Aðferð: Innskráð leit (Íslendingabók)\n"
            "   - Aðgerð: Leitað að alsystkinum Þorbjargar Benediktsdóttur (f. 1898).\n"
            "   - Niðurstaða: Fundust 6 alsystkini sem vantaði. Þau voru skráð og tengd (Margrét, Guðrún, Kristján, Jónína, Pálína, Unnar).\n"
            "● Aðferð: Vefleit (Tímarit.is & Morgunblaðið)\n"
            "   - Aðgerð: Leitað að andlátstilkynningu (d. 1992).\n"
            "   - Niðurstaða: Staðfest andlát 27. febrúar 1992 á hjúkrunarheimilinu Skjólgarði á Höfn."
        ),
        'I212565201807': (
            "[Lokið] Rannsóknarferill:\n"
            "● Aðferð: Skráagreining (Ættarmót.md)\n"
            "   - Aðgerð: Borinn saman texti við innflutta ættartréð.\n"
            "   - Niðurstaða: Bætt við 5 börnum (Steinþór, Sigurjón, Hugi, Rannveig, Kristján) og mökum þeirra, auk allra afkomenda. Tekið tillit til nafnaárekstra (Sigurjón Einarsson f. 1950 er nú sjálfstæður einstaklingur)."
        )
    }
    
    for bid, log_text in logs.items():
        b = next((x for x in blocks if x.id == bid), None)
        if b:
            b.remove_tag(1, "NOTE")
            b.remove_tag(2, "CONC")
            b.remove_tag(2, "CONT")
            
            lines = log_text.split('\n')
            b.add_tag(1, "NOTE", lines[0])
            for line in lines[1:]:
                b.add_tag(2, "CONT", line)
            print(f"Added structured note to Sigurjón tree individual: {bid}")
            
    save_gedcom_blocks(blocks, 'sigurjon.ged')

def add_logs_to_loa():
    blocks = parse_gedcom_blocks('loa.ged')
    
    logs = {
        'I272771958737': (
            "[Lokið] Rannsóknarferill:\n"
            "● Aðferð: Vefleit (Tímarit.is & Morgunblaðið)\n"
            "   - Aðgerð: Leit í minningargreinum foreldra hennar (Ingólfs Árna Sveinssonar d. 2002 og Svönu Sigtryggsdóttur d. 2020).\n"
            "   - Niðurstaða: Fundust tvær dætur hennar með Jóni Óskari Péturssyni sem vantaði: Vala Björk Jónsdóttir og Sara Kristín Jónsdóttir. Þær voru skráðar og tengdar í loa.ged ásamt Viktor Inga."
        ),
        'I272771958754': (
            "[Lokið] Rannsóknarferill:\n"
            "● Aðferð: Vefleit (Morgunblaðið Greinasafn)\n"
            "   - Aðgerð: Leitað að minningargreinum um Ingólf Árna Sveinsson (d. 2002).\n"
            "   - Niðurstaða: Minningargrein fannst og staðfesti fjölskyldu og barnabörn (þar á meðal börn Ólafíu Rósbjargar og Jóns Óskars: Viktor Inga, Vala Björk og Sara Kristín). Allt skráð í loa.ged."
        ),
        'I272771958746': (
            "[Lokið] Rannsóknarferill:\n"
            "● Aðferð: Vefleit (Morgunblaðið Greinasafn)\n"
            "   - Aðgerð: Leitað að minningargrein um Svönu Sigtryggsdóttur (d. 2020).\n"
            "   - Niðurstaða: Minningargrein frá maí 2020 fannst. Hún staðfesti 10 systkini hennar og barnabörn hennar (börn Ólafíu Rósbjargar og Jóns Óskars: Viktor Inga, Vala Björk og Sara Kristín). Allt skráð í loa.ged."
        )
    }
    
    for bid, log_text in logs.items():
        b = next((x for x in blocks if x.id == bid), None)
        if b:
            b.remove_tag(1, "NOTE")
            b.remove_tag(2, "CONC")
            b.remove_tag(2, "CONT")
            
            lines = log_text.split('\n')
            b.add_tag(1, "NOTE", lines[0])
            for line in lines[1:]:
                b.add_tag(2, "CONT", line)
            print(f"Added structured note to Lóa tree individual: {bid}")
            
    save_gedcom_blocks(blocks, 'loa.ged')

def update_minningargreinar_doc():
    # Let's append Sigurjón and Þorbjörg's obituary findings to minningargreinar.md
    path = '/home/sigurjonaxel/repos/github/ancestry/heimildir/minningargreinar.md'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "# Heimildir og Minningargreinar\n"
        
    addition = (
        "\n## Sigurjón Einarsson (1895–1983) & Þorbjörg Benediktsdóttir (1898–1992)\n"
        "> **Búseta:** Árbær á Mýrum, Austur-Skaftafellssýsla\n"
        "\n"
        "### Dánartilkynning Sigurjóns (Morgunblaðið, 5. mars 1983)\n"
        "* Sigurjón Einarsson frá Árbæ lést 28. febrúar 1983. Hann var jarðsunginn frá Brunnhólskirkju mánudaginn 7. mars 1983.\n"
        "* Eftirlifandi maki: Þorbjörg Benediktsdóttir, og börn þeirra.\n"
        "\n"
        "### Dánartilkynning Þorbjargar (Morgunblaðið, 29. febrúar 1992)\n"
        "* Þorbjörg Benediktsdóttir frá Árbæ lést 27. febrúar 1992 á hjúkrunarheimilinu Skjólgarði á Höfn.\n"
    )
    
    if "Sigurjón Einarsson (1895–1983)" not in content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content + addition)
        print("Updated minningargreinar.md with Sigurjón and Þorbjörg details.")

if __name__ == '__main__':
    add_logs_to_sigurjon()
    add_logs_to_loa()
    update_minningargreinar_doc()
    print("Research logs successfully updated!")
