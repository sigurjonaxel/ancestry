import os
import json
import re
from db import init_db, get_db

def parse_birth_year(date_str):
    if not date_str:
        return ""
    match = re.search(r'\b(1\d{3}|20\d{2})\b', date_str)
    return match.group(1) if match else ""

def migrate():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    print("--- 1. Migrating GEDCOM Files ---")
    ged_files = [
        ("loa.ged", "Lóa ættartré"),
        ("sigurjon.ged", "Sigurjón ættartré")
    ]

    for filename, tree_name in ged_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(filepath):
            print(f"Skipping missing file: {filename}")
            continue

        tree_id = filename.replace('.ged', '')
        cursor.execute("INSERT OR REPLACE INTO trees (id, filename, name) VALUES (?, ?, ?)",
                       (tree_id, filename, tree_name))

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        current_indi = None
        indi_data = {}
        last_event = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(' ', 2)
            level = parts[0]
            tag = parts[1]
            val = parts[2] if len(parts) > 2 else ''

            if len(parts) > 2 and parts[2] == 'INDI':
                if current_indi and indi_data:
                    save_person(cursor, tree_id, current_indi, indi_data)
                current_indi = parts[1].replace('@', '')
                indi_data = {'name': '', 'birth_date': '', 'death_date': '', 'sex': ''}
                last_event = None
            elif current_indi:
                if tag == 'NAME':
                    indi_data['name'] = val.replace('/', '').strip()
                elif tag == 'SEX':
                    indi_data['sex'] = val
                elif tag == 'BIRT':
                    last_event = 'BIRT'
                elif tag == 'DEAT':
                    last_event = 'DEAT'
                elif tag == 'DATE':
                    if last_event == 'BIRT':
                        indi_data['birth_date'] = val
                        last_event = None
                    elif last_event == 'DEAT':
                        indi_data['death_date'] = val
                        last_event = None
                elif level == '1':
                    last_event = None

        if current_indi and indi_data:
            save_person(cursor, tree_id, current_indi, indi_data)

    print("--- 2. Migrating person_sources.json ---")
    sources_file = os.path.join(os.path.dirname(__file__), "person_sources.json")
    if os.path.exists(sources_file):
        try:
            with open(sources_file, 'r', encoding='utf-8') as f:
                sources_data = json.load(f)

            for person_id, data in sources_data.items():
                clean_id = person_id.replace('@', '')
                entries = data.get('entries', []) if isinstance(data, dict) else data
                for entry in entries:
                    cursor.execute("""
                        INSERT INTO sources (person_id, title, snippet, link, image_url, favicon)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        clean_id,
                        entry.get('title', 'Staðfest heimild'),
                        entry.get('snippet', entry.get('description', '')),
                        entry.get('link', entry.get('url', '')),
                        entry.get('image', entry.get('image_url', '')),
                        entry.get('favicon', '')
                    ))
            print("Migrated person_sources.json successfully.")
        except Exception as e:
            print(f"Error migrating person_sources.json: {e}")

    print("--- 3. Migrating suggestions.json ---")
    suggestions_file = os.path.join(os.path.dirname(__file__), "suggestions.json")
    if os.path.exists(suggestions_file):
        try:
            with open(suggestions_file, 'r', encoding='utf-8') as f:
                sug_data = json.load(f)

            for person_id, sugs in sug_data.items():
                clean_id = person_id.replace('@', '')
                for s in sugs:
                    rel_details = s.get('relation_details')
                    rel_json = json.dumps(rel_details, ensure_ascii=False) if rel_details else None
                    status = 'rejected' if s.get('rejected') else 'pending'
                    cursor.execute("""
                        INSERT INTO ai_suggestions 
                        (person_id, type, source, url, image_url, local_path, title, description, confidence, relation_details, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        clean_id,
                        s.get('type', 'event'),
                        s.get('source', ''),
                        s.get('url', ''),
                        s.get('image_url', s.get('image', '')),
                        s.get('local_path', ''),
                        s.get('title', ''),
                        s.get('description', s.get('body', '')),
                        s.get('confidence', 70),
                        rel_json,
                        status
                    ))
            print("Migrated suggestions.json successfully.")
        except Exception as e:
            print(f"Error migrating suggestions.json: {e}")

    conn.commit()
    conn.close()
    print("=== Migration complete! SQLite database ready. ===")

def save_person(cursor, tree_id, person_id, data):
    b_date = data.get('birth_date', '')
    d_date = data.get('death_date', '')
    b_year = parse_birth_year(b_date)
    d_year = parse_birth_year(d_date)

    cursor.execute("""
        INSERT OR REPLACE INTO people 
        (id, tree_id, name, sex, birth_date, birth_year, death_date, death_year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (person_id, tree_id, data.get('name', ''), data.get('sex', ''), b_date, b_year, d_date, d_year))

if __name__ == "__main__":
    migrate()
