import sqlite3
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

from ai_research import run_ai_research_for_person
from google import genai

api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
client = genai.Client(api_key=api_key) if api_key else None

def get_olafia_family_group():
    conn = sqlite3.connect('ancestry.db')
    conn.row_factory = sqlite3.Row
    target_id = 'I272771958737'

    parents = [r['related_id'] for r in conn.execute('SELECT related_id FROM relations WHERE person_id=? AND relation_type IN ("father","mother")', (target_id,)).fetchall()]
    siblings = []
    for p in parents:
        ch = [r['related_id'] for r in conn.execute('SELECT related_id FROM relations WHERE person_id=? AND relation_type="child"', (p,)).fetchall()]
        siblings.extend(ch)
    siblings = list(set(siblings) - {target_id})

    grandparents = []
    for p in parents:
        gp = [r['related_id'] for r in conn.execute('SELECT related_id FROM relations WHERE person_id=? AND relation_type IN ("father","mother")', (p,)).fetchall()]
        grandparents.extend(gp)
    grandparents = list(set(grandparents))

    descendants = set()
    for gp in grandparents:
        gp_children = [r['related_id'] for r in conn.execute('SELECT related_id FROM relations WHERE person_id=? AND relation_type="child"', (gp,)).fetchall()]
        descendants.update(gp_children)
        for gpc in gp_children:
            gp_grandchildren = [r['related_id'] for r in conn.execute('SELECT related_id FROM relations WHERE person_id=? AND relation_type="child"', (gpc,)).fetchall()]
            descendants.update(gp_grandchildren)

    all_ids = list(set([target_id] + parents + siblings + grandparents + list(descendants)))
    
    people = []
    for pid in all_ids:
        p = conn.execute('SELECT id, name, birth_year, death_year FROM people WHERE id=?', (pid,)).fetchone()
        if p and p['name'] and len(p['name'].strip()) > 2:
            people.append(dict(p))
    conn.close()
    return people

def generate_bio_for_person(person_id, name, birth_year, death_year):
    conn = sqlite3.connect('ancestry.db')
    conn.row_factory = sqlite3.Row
    sources = [dict(r) for r in conn.execute('SELECT * FROM sources WHERE person_id=?', (person_id,)).fetchall()]
    sugs = [dict(r) for r in conn.execute('SELECT * FROM ai_suggestions WHERE person_id=? AND status="pending"', (person_id,)).fetchall()]
    rels = [dict(r) for r in conn.execute('SELECT r.relation_type, p.name FROM relations r JOIN people p ON p.id=r.related_id WHERE r.person_id=?', (person_id,)).fetchall()]
    conn.close()

    context = f"Einstaklingur: {name} (f. {birth_year or 'óvíst'}, d. {death_year or 'lifandi'})\n"
    if rels:
        rel_strs = [f"{r['relation_type']}: {r['name']}" for r in rels]
        context += "Fjölskyldutengsl: " + ", ".join(rel_strs) + "\n"
    
    all_evidence = sources + sugs
    if all_evidence:
        context += "\nStaðfestar heimildir og gögn úr rannsókn:\n"
        for s in all_evidence:
            context += f"- {s.get('title')}: {s.get('description') or s.get('snippet')} (Tengill: {s.get('url') or s.get('link','')})\n"

    prompt = f"""
    Þú ert íslenskur ættfræðingur. Skrifaðu hnitmiðaða, nákvæma og raunsæja samantekt á íslensku fyrir {name} byggt eingöngu á raunverulegum gögnum.

    {context}

    STRÖNG FYRIRMÆLI:
    - Bannað er að búa til skáldskap, upplogna starfsferla, almennar lofræður eða gervilýsingar á áhugamálum (t.d. 'ábyrgðarkona', 'starfsævi' fyrir ungt fólk eða börn).
    - Ef lítið eða ekkert er vitað nema ættartengsl eða fæðingarár, haltu samantektinni stuttri og segðu aðeins frá staðreyndum (foreldrar, systkini, maki, börn og fæðingar-/dánarár).
    - Ef raunverulegar heimildir, minningargreinar, nám eða störf eru til staðar, dragðu þær skýrt og skipulega saman í örstuttum málsgreinum eða punktum.

    Uppsetning í Markdown:
    # {name}
    ## 1. Yfirlit & Fjölskylda
    ## 2. Lífshlaup & Heimildir (aðeins ef gögn eru til staðar)
    ## 3. Tímalína (aðeins raunveruleg ártöl)
    """

    generated = None
    if client:
        for model_candidate in ['gemini-3.5-flash', 'gemini-3.7-flash', 'gemini-2.5-flash']:
            try:
                resp = client.models.generate_content(model=model_candidate, contents=prompt)
                if resp and resp.text:
                    generated = resp.text.strip()
                    break
            except Exception as e:
                pass

    if not generated:
        dates_str = f"f. {birth_year or 'óþekkt'}" + (f" - d. {death_year}" if death_year else '')
        
        foreldrar = [r['name'] for r in rels if r['relation_type'] in ('father', 'mother')]
        systkini = [r['name'] for r in rels if r['relation_type'] == 'sibling']
        maki = [r['name'] for r in rels if r['relation_type'] == 'spouse']
        born = [r['name'] for r in rels if r['relation_type'] == 'child']
        
        bio_parts = [
            f"# {name}",
            f"\n## 1. Yfirlit & Fjölskylda\n{name} ({dates_str}).",
        ]
        
        if foreldrar:
            bio_parts.append(f"- **Foreldrar:** {', '.join(foreldrar)}")
        if maki:
            bio_parts.append(f"- **Maki:** {', '.join(maki)}")
        if born:
            bio_parts.append(f"- **Börn:** {', '.join(born)}")
        if systkini:
            bio_parts.append(f"- **Systkini:** {', '.join(systkini)}")

        if all_evidence:
            bio_parts.append(f"\n## 2. Staðfestar heimildir")
            for s in all_evidence:
                bio_parts.append(f"- **{s.get('title')}**: {s.get('description') or s.get('snippet','')}")

        bio_parts.append(f"\n## 3. Tímalína")
        if birth_year:
            bio_parts.append(f"- **{birth_year}:** Fæðing")
        if death_year:
            bio_parts.append(f"- **{death_year}:** Andlát")

        generated = "\n".join(bio_parts)

    conn = sqlite3.connect('ancestry.db')
    conn.execute('UPDATE people SET notes = ? WHERE id = ?', (generated, person_id))
    conn.commit()
    conn.close()
    return generated

def batch_process_olafia_family():
    family = get_olafia_family_group()
    print(f"=== Hefjum heildarkeyrslu fyrir {len(family)} einstaklinga í ættarboga Ólafíu Rósbjargar ===")
    
    for idx, p in enumerate(family, 1):
        pid, name, birth, death = p['id'], p['name'], p['birth_year'], p['death_year']
        print(f"\n[{idx}/{len(family)}] Vinnur: {name} (f. {birth or '?'}, d. {death or 'lifandi'})...")
        
        # 1. Run Strict Grounded AI Research
        try:
            res = run_ai_research_for_person(pid, name, str(birth or ''), str(death or ''))
            print(f"  -> AI Leit: {res.get('status')} (Bætti við {res.get('added', 0)} uppástungum)")
        except Exception as e:
            print(f"  -> AI Leit villa: {e}")
        
        # Auto-promote high-confidence suggestions to confirmed sources & avatars
        conn = sqlite3.connect('ancestry.db')
        conn.row_factory = sqlite3.Row
        sugs = conn.execute('SELECT * FROM ai_suggestions WHERE person_id=? AND (confidence >= 80 OR type="image")', (pid,)).fetchall()
        for s in sugs:
            exists = conn.execute('SELECT id FROM sources WHERE person_id=? AND (title=? OR (link=? AND link!=""))', (pid, s['title'], s['url'])).fetchone()
            if not exists:
                conn.execute('INSERT INTO sources (person_id, title, snippet, link, image_url) VALUES (?, ?, ?, ?, ?)', (pid, s['title'], s['description'], s['url'], s['local_path'] or s['image_url']))
        
        # Auto set avatar if image found and none set
        cur_p = conn.execute('SELECT avatar_url FROM people WHERE id=?', (pid,)).fetchone()
        if not cur_p['avatar_url']:
            img = conn.execute('SELECT local_path, image_url FROM ai_suggestions WHERE person_id=? AND (local_path IS NOT NULL OR image_url IS NOT NULL) LIMIT 1', (pid,)).fetchone()
            if img:
                conn.execute('UPDATE people SET avatar_url=? WHERE id=?', (img['local_path'] or img['image_url'], pid))
        conn.commit()
        conn.close()

        # Rate limit safety delay
        time.sleep(3)
        
        # 2. Auto-generate / Regenerate Biography
        try:
            bio = generate_bio_for_person(pid, name, str(birth or ''), str(death or ''))
            print(f"  -> Samantekt: Tilbúin ({len(bio)} stafir)")
        except Exception as e:
            print(f"  -> Samantekt villa: {e}")
            
        time.sleep(2)
        
    print("\n=======================================================")
    print("✅ Allri AI keyrslu og samantektum lokið fyrir alla einstaklinga!")
    print("=======================================================")

if __name__ == '__main__':
    batch_process_olafia_family()
