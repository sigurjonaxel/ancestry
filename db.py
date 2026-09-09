import sqlite3
import json
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "ancestry.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Trees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trees (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                name TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # People table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id TEXT PRIMARY KEY,
                tree_id TEXT NOT NULL,
                name TEXT NOT NULL,
                given_names TEXT,
                surname TEXT,
                sex TEXT,
                birth_date TEXT,
                birth_year TEXT,
                birth_place TEXT,
                death_date TEXT,
                death_year TEXT,
                death_place TEXT,
                avatar_url TEXT,
                notes TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Relations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tree_id TEXT NOT NULL,
                person_id TEXT NOT NULL,
                related_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                UNIQUE(tree_id, person_id, related_id, relation_type)
            )
        """)
        
        # Confirmed Sources & Media
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT NOT NULL,
                title TEXT NOT NULL,
                snippet TEXT,
                link TEXT,
                image_url TEXT,
                favicon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # AI Suggestions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id TEXT NOT NULL,
                type TEXT NOT NULL,
                source TEXT,
                url TEXT,
                image_url TEXT,
                local_path TEXT,
                title TEXT,
                description TEXT,
                confidence INTEGER DEFAULT 70,
                relation_details TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Feedback & Issues Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tree_id TEXT NOT NULL,
                person_id TEXT,
                user_note TEXT,
                screenshot_paths TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

def save_suggestion(person_id, sug_type, source, url, image_url, local_path, title, description, confidence=70, relation_details=None, status='pending'):
    clean_id = person_id.replace('@', '')
    rel_json = json.dumps(relation_details, ensure_ascii=False) if relation_details else None
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Do not re-add if already exists in confirmed sources!
        if url and url.strip():
            cursor.execute("SELECT id FROM sources WHERE person_id = ? AND link = ?", (clean_id, url))
            if cursor.fetchone():
                return
        if image_url or local_path:
            # Check by exact path or image hash
            cursor.execute("SELECT id, image_url FROM sources WHERE person_id = ?", (clean_id,))
            existing_srcs = cursor.fetchall()
            target_path = local_path or image_url
            if target_path and os.path.exists(target_path):
                target_hash = hashlib.md5(open(target_path, 'rb').read()).hexdigest()
                for es in existing_srcs:
                    es_path = es['image_url']
                    if es_path and os.path.exists(es_path):
                        if hashlib.md5(open(es_path, 'rb').read()).hexdigest() == target_hash:
                            return # Already in confirmed sources!

        if title and title.strip():
            cursor.execute("SELECT id FROM sources WHERE person_id = ? AND title = ?", (clean_id, title))
            if cursor.fetchone():
                return

        # 2. Do not re-add if already exists in ai_suggestions (pending OR rejected)
        if sug_type == 'image' and (image_url or local_path):
            target_path = local_path or image_url
            if target_path and os.path.exists(target_path):
                target_hash = hashlib.md5(open(target_path, 'rb').read()).hexdigest()
                cursor.execute("SELECT id, local_path, image_url FROM ai_suggestions WHERE person_id = ?", (clean_id,))
                for row in cursor.fetchall():
                    r_path = row['local_path'] or row['image_url']
                    if r_path and os.path.exists(r_path):
                        if hashlib.md5(open(r_path, 'rb').read()).hexdigest() == target_hash:
                            return # Already classified as pending or rejected!
        elif url and url.strip():
            cursor.execute("""
                SELECT id FROM ai_suggestions 
                WHERE person_id = ? AND (url = ? OR title = ?)
            """, (clean_id, url, title))
            if cursor.fetchone():
                return
        elif title and title.strip():
            cursor.execute("""
                SELECT id FROM ai_suggestions 
                WHERE person_id = ? AND title = ?
            """, (clean_id, title))
            if cursor.fetchone():
                return

        cursor.execute("""
            INSERT INTO ai_suggestions 
            (person_id, type, source, url, image_url, local_path, title, description, confidence, relation_details, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (clean_id, sug_type, source, url, image_url, local_path, title, description, confidence, rel_json, status))
        conn.commit()

def get_person_details(person_id):
    clean_id = person_id.replace('@', '')
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM people WHERE id = ? OR id = ?", (clean_id, f"@{clean_id}@"))
        person_row = cursor.fetchone()
        
        cursor.execute("SELECT * FROM sources WHERE person_id = ? ORDER BY created_at DESC", (clean_id,))
        sources = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM ai_suggestions WHERE person_id = ? ORDER BY id DESC", (clean_id,))
        suggestions = []
        for r in cursor.fetchall():
            d = dict(r)
            if d.get('relation_details'):
                try:
                    d['relation_details'] = json.loads(d['relation_details'])
                except Exception:
                    pass
            suggestions.append(d)
            
        cursor.execute("""
            SELECT r.relation_type, p.id, p.name, p.birth_year, p.death_year, p.sex, p.avatar_url
            FROM relations r 
            JOIN people p ON r.related_id = p.id 
            WHERE r.person_id = ?
        """, (clean_id,))
        raw_relations = [dict(r) for r in cursor.fetchall()]

        family = {
            "father": None,
            "mother": None,
            "spouse": [],
            "children": [],
            "siblings": []
        }
        for r in raw_relations:
            person_stub = {
                "id": r["id"], "name": r["name"],
                "birth_year": r["birth_year"], "death_year": r["death_year"],
                "sex": r["sex"], "avatar_url": r["avatar_url"]
            }
            rtype = r["relation_type"]
            if rtype == "father":
                family["father"] = person_stub
            elif rtype == "mother":
                family["mother"] = person_stub
            elif rtype == "spouse":
                if person_stub not in family["spouse"]:
                    family["spouse"].append(person_stub)
            elif rtype == "child":
                if person_stub not in family["children"]:
                    family["children"].append(person_stub)
            elif rtype == "sibling":
                if person_stub not in family["siblings"]:
                    family["siblings"].append(person_stub)

        return {
            "person": dict(person_row) if person_row else None,
            "sources": sources,
            "suggestions": suggestions,
            "family": family
        }

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
