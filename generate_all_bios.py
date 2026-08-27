import os, time, sqlite3
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get key ancestors and family members in Sigurjon tree to polish bios
people = cursor.execute('''
    SELECT id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place, notes
    FROM people 
    WHERE tree_id = 'sigurjon'
    AND (notes LIKE '%Íslendingabók%' OR id LIKE 'IB_%' OR id IN ('I212097023484', 'I212565201202', 'I212565201500', 'I212565201521', 'I212565201807'))
''').fetchall()

print(f'Hef vandaða ævisögugerð með Gemini 2.5 Flash fyrir {len(people)} einstaklinga...')

for idx, p in enumerate(people):
    if p['id'] == 'I212097023483':
        continue
    
    rels = cursor.execute('''
        SELECT r.relation_type, p2.name, p2.birth_year 
        FROM relations r 
        JOIN people p2 ON p2.id = r.related_id 
        WHERE r.person_id = ?
    ''', (p['id'],)).fetchall()
    
    parents = [r['name'] for r in rels if r['relation_type'] in ('father', 'mother')]
    spouses = [r['name'] for r in rels if r['relation_type'] == 'spouse']
    children = [r['name'] for r in rels if r['relation_type'] == 'child']
    siblings = [r['name'] for r in rels if r['relation_type'] == 'sibling']
    
    srcs = cursor.execute('SELECT title, snippet, link FROM sources WHERE person_id = ?', (p['id'],)).fetchall()
    src_text = '\n'.join([f'- {s["title"]}: {s["snippet"]}' for s in srcs]) if srcs else 'Íslendingabók / Þjóðskrá'
    
    prompt = f'''
    Þú ert vandaður íslenskur ættfræðingur. Skrifaðu nákvæma, faglega og raunsæja ævisögu / yfirlit á íslensku fyrir: {p['name']}.
    
    GÖGN:
    - Nafn: {p['name']}
    - Fæðing: {p['birth_date'] or p['birth_year']} ({p['birth_place'] or 'ótilgreint'})
    - Andlát: {p['death_date'] or p['death_year'] or 'Á lífi / ótilgreint'} ({p['death_place'] or ''})
    - Foreldrar: {', '.join(parents) if parents else 'Ótilgreint'}
    - Maki: {', '.join(spouses) if spouses else 'Ótilgreint'}
    - Börn: {', '.join(children) if children else 'Ótilgreint'}
    - Systkini: {', '.join(siblings) if siblings else 'Ótilgreint'}
    - Fyrri minnispunktar/störf: {p['notes'] or ''}
    - Staðfestar heimildir:
    {src_text}
    
    STRÖNG FYRIRMÆLI:
    - Ekki búa til skáldaðar staðreyndir eða ósannar sögur.
    - Hafðu textann fallegan, skýran og á réttu íslensku máli.
    
    Skipulag:
    # {p['name']}
    
    ## 1. Yfirlit & Fjölskylduhagir
    (Stutt samantekt um fæðingu, uppruna, maka og börn)
    
    ## 2. Lífshlaup, Störf & Búseta
    (Samantekt um störf, búsetu og staðfestar heimildir)
    
    ## 3. Tímalína
    - (Ártöl og helstu atburðir)
    '''
    
    # Retry loop with backoff for rate limits
    for attempt in range(5):
        try:
            resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            if resp and resp.text:
                new_notes = resp.text.strip()
                cursor.execute('UPDATE people SET notes = ? WHERE id = ?', (new_notes, p['id']))
                conn.commit()
                print(f' [{idx+1}/{len(people)}] ✓ Endursamdi ævisögu fyrir: {p["name"]}')
                time.sleep(13) # Respect 5 RPM free tier limit
                break
        except Exception as e:
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                print(f'   ⏳ [RPM Limit] Bíð í 25s áður en reynt er aftur við {p["name"]}...')
                time.sleep(25)
            else:
                print(f'   ⚠️ Villa: {e}')
                time.sleep(5)

conn.close()
print('\n🎉 Allar ævisögur hafa verið endursamdar með AI!')
