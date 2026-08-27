import sqlite3, time
from ai_research import run_ai_research_for_person

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Get key adult family members to run the new AI search on
people = conn.execute("""
    SELECT id, name, birth_year, death_year 
    FROM people 
    WHERE tree_id = 'sigurjon'
    AND birth_year != ''
    AND CAST(birth_year AS INTEGER) BETWEEN 1930 AND 2005
    ORDER BY 
        CASE 
            WHEN id IN ('I212097023483', 'I212565201202', 'I212565201500', 'I212565591452', 'I212565591220', 'I212565592666', 'I212565592615', 'I212565592449', 'I212565590946', 'IADD24') THEN 0
            ELSE 1
        END,
        birth_year DESC
    LIMIT 30
""").fetchall()
conn.close()

print(f"🚀 Hef nýju AI vef- og myndaleitina fyrir {len(people)} lykileinstaklinga...")

for idx, p in enumerate(people):
    print(f"\n[{idx+1}/{len(people)}] Keyri nýju leitina fyrir: {p['name']} (f. {p['birth_year']})...")
    res = run_ai_research_for_person(p['id'], p['name'], p['birth_year'], p['death_year'] or "")
    print(f"   -> Niðurstaða: {res.get('message', res.get('status'))}")
    
    # 4 second pacing to avoid any quota limit
    time.sleep(4.0)

print("\n🎉 Lotukeyrslu á nýju AI leitinni lokið!")
