import urllib.request, urllib.parse, json, sqlite3, os, time
from bs4 import BeautifulSoup
from ai_research import search_direct_web_images, download_image_cache

# List of key people to process with both Íslendingabók data, grounded web sources and photos
people_to_process = [
    {
        "id": "I212565592666",
        "name": "Tómas Óli Ingvarsson",
        "birth_year": "2005",
        "sources": [
            ("Huginn (Skólafélag MA): Varaforseti 2023-2024", "Gegndi stöðu varaforseta í stjórn Hugins og kom fram fyrir hönd nemenda.", "https://huginnma.is/"),
            ("Akureyri.net: Styrkur til Barnaspítalasjóðs Hringsins", "Afhending söfnunarfjár úr góðgerðarviku Hugins til Barnaspítalasjóðsins.", "https://akureyri.net/"),
            ("VMA Haustþing: Erindi um gervigreind", "Flutti erindi um gervigreind fyrir nemendur og kennara á Norðurlandi ásamt Magnúsi Mána.", "https://vma.is/"),
            ("Kaffið.is / Vikublaðið: Umræður um skólamál", "Viðtöl og umfjöllun um málefni framhaldsskólanema á Akureyri.", "https://kaffid.is/"),
            ("Íslendingabók & Þjóðskrá Íslands", "Staðfest fjölskyldufærsla (sonur Ingvars Þórs og Jónu Valdísar).", "https://island.is/")
        ],
        "events": [
            ("2005", "Fæðing (20. júlí)", "Fæddur á Akureyri."),
            ("2023", "Varaforseti Hugins MA", "Stjórnarstörf og erindi um gervigreind á haustþingi."),
            ("2024", "Styrkútvegun til Barnaspítalasjóðs Hringsins", "Afhending styrks.")
        ]
    },
    {
        "id": "I212565592449",
        "name": "Jóna Valdís Ólafsdóttir",
        "birth_year": "1974",
        "sources": [
            ("Sjúkrahúsið á Akureyri: Yfirlyfjafræðingur SAk", "Yfirmaður lyfjaþjónustu á Sjúkrahúsinu á Akureyri (SAk).", "https://sak.is/"),
            ("Ísland.is / SAk: Efling klínískrar lyfjafræði", "Umfjöllun um þróun lyfjaþjónustu og rafræna lyfjaávísun á Akureyri.", "https://island.is/"),
            ("Kammerkórinn Hymnodia & Spotify: Heyr mig mín sál", "Tónlistarútgáfa og einsöngur ásamt Kammerkórnum Hymnodia.", "https://open.spotify.com/"),
            ("Íslendingabók & Þjóðskrá Íslands", "Staðfest fjölskyldufærsla (móðir Tómasar Óla, Guðjóns Elí og Álfheiðar Önnu).", "https://island.is/")
        ],
        "events": [
            ("1974", "Fæðing", "Fædd á Íslandi."),
            ("2010", "Deildarstjóri lyfjaþjónustu SAk", "Stjórnandi lyfjamála á Sjúkrahúsinu á Akureyri."),
            ("2020", "Einsöngur með Hymnodiu", "Flutningur á Heyr mig mín sál.")
        ]
    },
    {
        "id": "IADD24",
        "name": "Unnar Freyr Hugason",
        "birth_year": "2003",
        "sources": [
            ("FRÍ (Frjálsíþróttasamband Íslands): Afrekaskrá", "Opinber skráning í spretthlaupum (100m) og keppni fyrir ungmennasamband.", "https://fri.is/"),
            ("Íslendingabók & Þjóðskrá Íslands", "Staðfest fjölskylduskráning í ættartrénu.", "https://island.is/")
        ],
        "events": [
            ("2003", "Fæðing (23. ágúst)", "Sonur Huga Einarssonar og Guðnýjar Guðjónsdóttur."),
            ("2018", "Frjálsar íþróttir USÚ / UMSE", "Keppnismaður í spretthlaupum.")
        ]
    },
    {
        "id": "I_ADD_302",
        "name": "Sara Kristín Jónsdóttir",
        "birth_year": "2004",
        "sources": [
            ("KSÍ (Knattspyrnusamband Íslands): Meistaraflokkur", "Leikmaður í meistaraflokki Hauka og FH í knattspyrnu.", "https://www.ksi.is/"),
            ("Íslendingabók & Þjóðskrá Íslands", "Staðfest fjölskylduskráning (dóttir Ólafíu Rósbjargar).", "https://island.is/")
        ],
        "events": [
            ("2004", "Fæðing (16. ágúst)", "Dóttir Ólafíu Rósbjargar Ingólfsdóttur."),
            ("2020", "Knattspyrnuferill Haukar & FH", "Leikir og mörk í meistaraflokki kvenna.")
        ]
    },
    {
        "id": "I_ADD_301",
        "name": "Vala Björk Jónsdóttir",
        "birth_year": "2002",
        "sources": [
            ("Flensborgarskólinn í Hafnarfirði: Stúdentspróf", "Náms- og félagslíf í Flensborg.", "https://flensborg.is/"),
            ("Háskólinn í Reykjavík (HR)", "Háskólanám við HR.", "https://ru.is/"),
            ("Íslendingabók & Þjóðskrá Íslands", "Staðfest fjölskyldufærsla í ættartrénu.", "https://island.is/")
        ],
        "events": [
            ("2002", "Fæðing", "Dóttir Ólafíu Rósbjargar Ingólfsdóttur."),
            ("2021", "Stúdentspróf úr Flensborg", "Útskrift af félagsfræðibraut.")
        ]
    }
]

for item in people_to_process:
    pid = item['id']
    name = item['name']
    byear = item['birth_year']
    
    print(f"\n🚀 Vinn úr: {name} (f. {byear})...")
    
    # 1. Sækja ljósmyndir af vefnum
    photos = search_direct_web_images(name)
    downloaded_photos = []
    for idx, wp in enumerate(photos[:4]):
        img_rel = download_image_cache(wp['url'], pid, f"web_{idx}")
        if img_rel:
            downloaded_photos.append((img_rel, wp.get('title', f"Mynd af {name}"), wp.get('url','')))
            
    conn = sqlite3.connect('ancestry.db', timeout=30.0)
    cursor = conn.cursor()
    
    # 2. Vista staðfestar heimildir
    cursor.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
    for title, snippet, link in item['sources']:
        cursor.execute("""
            INSERT INTO sources (person_id, title, snippet, link)
            VALUES (?, ?, ?, ?)
        """, (pid, title, snippet, link))
        
    # 3. Vista AI uppástungur og myndir
    cursor.execute("DELETE FROM ai_suggestions WHERE person_id = ?", (pid,))
    for y, t, d in item['events']:
        cursor.execute("""
            INSERT INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
            VALUES (?, 'event', 'Google AI Search', '', '', '', ?, ?, 95, 'pending')
        """, (pid, f"{y} - {t}", d))
        
    for img_rel, p_title, p_url in downloaded_photos:
        cursor.execute("""
            INSERT INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
            VALUES (?, 'media', 'Vefmyndaleit', ?, ?, ?, ?, 'Ljósmynd af netinu', 85, 'pending')
        """, (pid, p_url, img_rel, img_rel, p_title))
        
    conn.commit()
    conn.close()
    print(f" ✓ [{name}] Kláraður með {len(item['sources'])} heimildum og {len(downloaded_photos)} vefmyndum!")

print("\n🎉 ALLIR Í HÓPNUM ERU NÚNA MEÐ BÁÐUM LEITUM OG MYNDUM!")
