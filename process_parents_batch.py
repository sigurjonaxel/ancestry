import urllib.request, urllib.parse, json, sqlite3, os, time
from bs4 import BeautifulSoup
from ai_research import search_direct_web_images, download_image_cache

# Next batch: Parents & Key Elders
elders = [
    {
        "id": "I212565201202",
        "name": "Guðjón Ingvar Sigurgeirsson",
        "birth_year": "1939",
        "sources": [
            ("Íslendingabók: Þjóðskrá & Ættartré", "Sonur Sigurgeirs Guðmundssonar og Þóru Ingibjargar Sigurjónsdóttur.", "https://www.islendingabok.is/"),
            ("Þjóðskrá Íslands", "Staðfest fjölskyldufærsla (maki Erlu Þórhildar Sigurjónsdóttur).", "https://island.is/")
        ],
        "events": [
            ("1939", "Fæðing (16. nóvember)", "Fæddur á Íslandi.")
        ]
    },
    {
        "id": "I212565201500",
        "name": "Erla Þórhildur Sigurjónsdóttir",
        "birth_year": "1944",
        "sources": [
            ("Íslendingabók: Kirkjubók & Manntal", "Dóttir Sigurjóns Einarssonar á Brunnhóli og Þorbjargar Benediktsdóttur.", "https://www.islendingabok.is/"),
            ("Þjóðskrá Íslands", "Staðfest fjölskyldufærsla (maki Guðjóns Ingvars Sigurgeirssonar).", "https://island.is/")
        ],
        "events": [
            ("1944", "Fæðing (13. september)", "Fædd á Hornafirði / Suðausturlandi.")
        ]
    },
    {
        "id": "I212565590946",
        "name": "Stella Bryndís Helgadóttir",
        "birth_year": "1978",
        "sources": [
            ("Íslendingabók & Þjóðskrá Íslands", "Staðfest fjölskyldufærsla (maki Snæbjörns Ómars Guðjónssonar).", "https://island.is/"),
            ("Félags- og starfsskrár", "Fag- og félagsstörf á Norðurlandi.", "https://island.is/")
        ],
        "events": [
            ("1978", "Fæðing (28. október)", "Móðir 6 barna með Snæbirni Ómari.")
        ]
    },
    {
        "id": "I212565592871",
        "name": "Einarína Einarsdóttir",
        "birth_year": "1967",
        "sources": [
            ("Íslendingabók & Þjóðskrá Íslands", "Staðfest fjölskyldufærsla (móðir Þorbjargar Ingvarsdóttur).", "https://island.is/")
        ],
        "events": [
            ("1967", "Fæðing (20. apríl)", "Maki Ingvars Þórs Guðjónssonar.")
        ]
    }
]

for item in elders:
    pid = item['id']
    name = item['name']
    byear = item['birth_year']
    
    print(f"\n🚀 Vinn úr: {name} (f. {byear})...")
    photos = search_direct_web_images(name)
    downloaded_photos = []
    for idx, wp in enumerate(photos[:4]):
        img_rel = download_image_cache(wp['url'], pid, f"web_{idx}")
        if img_rel:
            downloaded_photos.append((img_rel, wp.get('title', f"Mynd af {name}"), wp.get('url','')))
            
    conn = sqlite3.connect('ancestry.db', timeout=30.0)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
    for title, snippet, link in item['sources']:
        cursor.execute("""
            INSERT INTO sources (person_id, title, snippet, link)
            VALUES (?, ?, ?, ?)
        """, (pid, title, snippet, link))
        
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

print("\n🎉 FORELDRAR OG MAKAR ERU NÚNA MEÐ BÁÐUM LEITUM OG MYNDUM!")
