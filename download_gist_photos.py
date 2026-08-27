import urllib.request, os, sqlite3

images = [
    {
        "url": "https://drive.google.com/uc?export=view&id=17RHkheOvLqFDjM0vt7_Oy58YFXpKx4Ns",
        "title": "Forsíðumynd: Fjallasýn á Mýrum (Ljósm. Rakel Ösp)",
        "person_id": "I212565201805", # Sigurjón Einarsson á Brunnhóli
        "filename": "gist_brunnholl_fjallasyn.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=16hTs-r_l2LB11TfcBOMleqDB-W0NAY7J",
        "title": "Þorbjörg Benediktsdóttir og Sigurjón Einarsson á Brunnhóli",
        "person_id": "I212565201805",
        "person_id_2": "I212565201806",
        "filename": "gist_thorbjorg_sigurjon_brunnhol.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=17Vx14NfqkpsmBUPUaA46VlOwYQqIr9uM",
        "title": "Einar Sigurjónsson og Unnur Kristjánsdóttir (Lambleiksstöðum)",
        "person_id": "I212565201807", # Einar Sigurjónsson
        "filename": "gist_einar_unnur_lambleiksstodum.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=17aQfbeG-qKJUwkAvrJABE7c2AgG-zCPp",
        "title": "Benedikt Sigurjónsson og Sigríður Sigurðardóttir (Sigga)",
        "person_id": "I212565201809", # Benedikt Sigurjónsson
        "filename": "gist_benedikt_sigridur.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=17OU-Bv_5U_tUigqz69gGWsweomjAuLQw",
        "title": "Ingunn Sigríður Sigurjónsdóttir og Karl Björnsson",
        "person_id": "I212565201811", # Ingunn Sigríður
        "filename": "gist_ingunn_karl.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=17c2eXOhSEbLHd8t3EUoipb8eQR74sGdO",
        "title": "Arnór Sigurjónsson og Ragna Sigurðardóttir (Brunnhóli)",
        "person_id": "I212565201813", # Arnór Sigurjónsson
        "filename": "gist_arnor_ragna.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=17fiLS6PdIjzXOZ52C58BwNKTLGKZpn9e",
        "title": "Aðalheiður Sigurjónsdóttir og Guðmundur Sæmundsson (Hlíðarbergi)",
        "person_id": "I212567429770", # Aðalheiður
        "filename": "gist_adalheidur_gudmundur.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=17HusmRddN-avAG_LwirZ6UeLyZrYur4P",
        "title": "Sigurbjörg Sigurjónsdóttir og Sigurjón Bjarnason (Viðborðsseli)",
        "person_id": "I212605401062", # Sigurbjörg
        "filename": "gist_sigurbjorg_sigurjon.jpg"
    },
    {
        "url": "https://drive.google.com/uc?export=view&id=17B0aFUUGQJEUFtYYq9D-k_moy50Q7ZBW",
        "title": "Erla Þórhildur Sigurjónsdóttir og Guðjón Ingvar Sigurgeirsson",
        "person_id": "I212565201500", # Erla Þórhildur
        "person_id_2": "I212565201202", # Guðjón Ingvar
        "filename": "gist_erla_gudjon.jpg"
    }
]

cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
os.makedirs(cache_dir, exist_ok=True)

conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

print(f"Sæki {len(images)} sögulegar ættarmótsmyndir úr Gist skjalinu...")

for it in images:
    local_path = os.path.join(cache_dir, it['filename'])
    rel_path = f"images/cache/{it['filename']}"
    
    try:
        req = urllib.request.Request(it['url'], headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            with open(local_path, "wb") as f:
                f.write(content)
        print(f" ✓ Sótti mynd: {it['title']} ({len(content)} bæti)")
        
        # Bæta við í Sögubók (sources)
        pids = [it['person_id']]
        if 'person_id_2' in it:
            pids.append(it['person_id_2'])
            
        for pid in pids:
            cursor.execute("""
                INSERT OR IGNORE INTO sources (person_id, title, snippet, link, image_url)
                VALUES (?, ?, 'Söguleg ljósmynd úr ættartali Ættarmóts 2024 á Hornafirði.', 'https://gist.github.com/sigurjonaxel/55c6041f2bf745fc0e288d56a415bac9', ?)
            """, (pid, it['title'], rel_path))
            
            # Einnig setja sem uppástungu
            cursor.execute("""
                INSERT OR IGNORE INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
                VALUES (?, 'media', 'Ættarmót 2024', ?, ?, ?, ?, 'Ljósmynd úr ættarmótsskjali', 100, 'confirmed')
            """, (pid, it['url'], rel_path, rel_path, it['title']))
            
    except Exception as e:
        print(f" ❌ Villa við að sækja {it['title']}: {e}")

conn.commit()
conn.close()
print("\n🎉 ALLAR ÆTTARMÓTSMYNDIRNAR ERU KOMNAR Í SÖGUBÓKINA OG Á PRÓFÍLANA!")
