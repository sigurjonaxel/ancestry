import sqlite3

conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# Eyða öllum dönskum fataverslunum, sjónvarpsþáttum, Wikipedia nafnagreiningum og öðru rusli
cursor.execute("""
    DELETE FROM sources 
    WHERE link LIKE '%bing.com%' 
       OR title LIKE '%AXEL%' 
       OR title LIKE '%Aarhus%' 
       OR title LIKE '%Vera%' 
       OR title LIKE '%Wikipedia%'
       OR snippet LIKE '%Eksklusivt modetøj%'
""")

cursor.execute("""
    DELETE FROM ai_suggestions 
    WHERE url LIKE '%bing.com%' 
       OR title LIKE '%AXEL%' 
       OR title LIKE '%Aarhus%' 
       OR title LIKE '%Vera%' 
       OR title LIKE '%Wikipedia%'
       OR description LIKE '%Eksklusivt modetøj%'
""")

conn.commit()
conn.close()
print("✓ Hreinsaði burt allar danskar fataverslanir og Bing rusltengla!")
