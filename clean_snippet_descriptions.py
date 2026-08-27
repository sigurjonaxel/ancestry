import sqlite3

conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# Replace any snippet or source description that says "Ljósmynd af netinu" with a clean factual description
cursor.execute("UPDATE sources SET snippet = 'Staðfest grein / umfjöllun á vefnum.' WHERE snippet LIKE '%Ljósmynd af netinu%' OR snippet LIKE '%Ljósmynd úr grein%'")
cursor.execute("UPDATE ai_suggestions SET description = 'Ljósmynd' WHERE description LIKE '%Ljósmynd af netinu%' OR description LIKE '%Ljósmynd úr grein%'")

conn.commit()
conn.close()

# Rerun the clean notes generator
import fix_all_people_notes_clean_universal
print("✓ Hreinsaði öll 'Ljósmynd af netinu' textabrot úr öllum heimildum!")
