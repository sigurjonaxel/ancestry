import sqlite3

conn = sqlite3.connect('ancestry.db')

# Purge the noisy 47 junk/unverified image suggestions for Sigurjón
conn.execute("DELETE FROM ai_suggestions WHERE person_id='I212097023483'")
print(f"Hreinsaði allar ómarkvissar uppástungur úr bið.")

conn.commit()
conn.close()
