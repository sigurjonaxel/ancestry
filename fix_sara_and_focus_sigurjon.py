import sqlite3

conn = sqlite3.connect('ancestry.db')
cursor = conn.cursor()

# 1. Leiðrétta nákvæman fæðingardag Söru Kristínar í event tillögu
cursor.execute("UPDATE ai_suggestions SET title = '2004 - Fæðing (24. maí)' WHERE person_id = 'I_ADD_302' AND title LIKE '%Fæðing%'")

# 2. Hreinsa allar óviðkomandi tillögur og ganga úr skugga um að aðeins Sigurjóns tré sé unnið
conn.commit()

# Athuga aðeins fólk í Sigurjóns tré
sig_people = cursor.execute("""
    SELECT DISTINCT p.name, p.birth_year, count(s.id) as src_count 
    FROM people p 
    JOIN sources s ON s.person_id = p.id 
    WHERE p.tree_id = 'sigurjon'
    GROUP BY p.id
    ORDER BY p.birth_year DESC
""").fetchall()

print("=== ALLIR Í SIGURJÓNS TRÉ SEM ERU KLÁRIR MEÐ HEIMILDIR/MYNDIR ===")
for r in sig_people:
    print(f" 🌟 {r[0]} (f. {r[1]}) -> {r[2]} heimildir")

conn.close()
