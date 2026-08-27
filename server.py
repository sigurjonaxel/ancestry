import http.server
import socketserver
import json
import os
import sys
import urllib.parse
import urllib.request
import cgi
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
from db import init_db, get_db, get_person_details, save_suggestion
from ai_research import run_ai_research_for_person

PORT = 8000
CACHE_BUST = str(int(time.time()))  # Changes every server restart

# Ensure database is initialized
init_db()

class AncestryHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_json({"error": message, "status": code}, status=code)

    def serve_index_html(self):
        """Serve index.html with a live-injected cache-busting version tag."""
        index_path = os.path.join(os.path.dirname(__file__), 'index.html')
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Inject live cache-busting version
            import re
            content = re.sub(r'app\.js\?v=[^"]+', f'app.js?v={CACHE_BUST}', content)
            encoded = content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        except Exception as e:
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = parsed_url.query

        if path == '/' or path == '/index.html':
            self.serve_index_html()
        elif path == '/api/trees':
            self.handle_get_trees()
        elif path == '/api/tree':
            self.handle_get_tree(query)
        elif path == '/api/person':
            self.handle_get_person(query)
        elif path == '/api/run_scraper':
            self.handle_run_scraper(query)
        elif path == '/api/proxy_image':
            self.handle_proxy_image(query)
        else:
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = parsed_url.query

        if path == '/api/upload_avatar':
            self.handle_upload_avatar(query)
        elif path == '/api/upload_gedcom':
            self.handle_upload_gedcom(query)
        elif path == '/api/confirm_suggestion':
            self.handle_confirm_suggestion(query)
        elif path == '/api/reject_suggestion':
            self.handle_reject_suggestion(query)
        elif path == '/api/add_media':
            self.handle_add_media(query)
        elif path == '/api/add_relation':
            self.handle_add_relation(query)
        elif path == '/api/save_settings':
            self.handle_save_settings(query)
        elif path == '/api/delete_source':
            self.handle_delete_source(query)
        elif path == '/api/set_profile_image':
            self.handle_set_profile_image(query)
        elif path == '/api/generate_bio':
            self.handle_generate_bio(query)
        else:
            self.send_error_response(404, "Endpoint not found.")

    def handle_generate_bio(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        person_id = params.get('person_id', [''])[0].replace('@', '')
        if not person_id:
            self.send_error_response(400, "Missing person_id")
            return

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM people WHERE id = ? OR id = ?", (person_id, f"@{person_id}@"))
            p_row = cursor.fetchone()
            if not p_row:
                self.send_error_response(404, "Person not found")
                return
            person = dict(p_row)
            
            cursor.execute("SELECT * FROM sources WHERE person_id = ? ORDER BY created_at ASC", (person_id,))
            sources = [dict(r) for r in cursor.fetchall()]
            
            cursor.execute("""
                SELECT r.relation_type, p.name FROM relations r 
                JOIN people p ON p.id = r.related_id 
                WHERE r.person_id = ?
            """, (person_id,))
            rels = [dict(r) for r in cursor.fetchall()]

        context = f"Einstaklingur: {person.get('name')} (f. {person.get('birth_year','')}, d. {person.get('death_year') or 'lifandi'})\n"
        if rels:
            context += f"Fjölskyldutengsl: {', '.join([f'{r.get('relation_type')}: {r.get('name')}' for r in rels])}\n"
        context += "\nStaðfestar heimildir og gögn úr gagnagrunni:\n"
        for s in sources:
            context += f"- {s.get('title')}: {s.get('snippet')} (Tengill: {s.get('link','')})\n"

        prompt = f"""
        Þú ert íslenskur ættfræðingur. Skrifaðu hnitmiðaða, nákvæma og raunsæja samantekt á íslensku fyrir {person.get('name')} byggt eingöngu á raunverulegum gögnum.

        {context}

        STRÖNG FYRIRMÆLI:
        - Bannað er að búa til skáldskap, upplogna starfsferla, almennar lofræður eða gervilýsingar á áhugamálum (t.d. 'ábyrgðarkona', 'ræktunarkona', 'starfsævi' fyrir ungt fólk eða börn).
        - Ef lítið eða ekkert er vitað nema ættartengsl eða fæðingarár, haltu samantektinni stuttri og segðu aðeins frá staðreyndum (foreldrar, systkini, maki, börn og fæðingar-/dánarár).
        - Ef raunverulegar heimildir, minningargreinar, nám eða störf eru til staðar, dragðu þær skýrt og skipulega saman í örstuttum málsgreinum eða punktum.

        Uppsetning í Markdown:
        # {person.get('name')}
        ## 1. Yfirlit & Fjölskylda
        ## 2. Lífshlaup & Heimildir (aðeins ef gögn eru til staðar)
        ## 3. Tímalína (aðeins raunveruleg ártöl)
        """

        generated_bio = None
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                for model_candidate in ['gemini-3.5-flash', 'gemini-3.7-flash', 'gemini-2.5-flash']:
                    try:
                        resp = client.models.generate_content(model=model_candidate, contents=prompt)
                        if resp and resp.text:
                            generated_bio = resp.text.strip()
                            break
                    except Exception as me:
                        print(f"[Bio Gen] Model {model_candidate} error: {me}")
            except Exception as e:
                print(f"[Bio Gen] General error: {e}")

        if not generated_bio:
            # Clean strict fallback template
            dates_str = f"f. {person.get('birth_year','óþekkt')}" + (f" - d. {person.get('death_year')}" if person.get('death_year') else '')
            lines = [f"# {person.get('name')}\n", f"## 1. Yfirlit & Fjölskylda\n{person.get('name')} ({dates_str}).\n"]
            if sources:
                lines.append("## 2. Staðfestar heimildir\n")
                for s in sources:
                    lines.append(f"- **{s.get('title')}**: {s.get('snippet','')}")
            generated_bio = "\n".join(lines)

        with get_db() as conn:
            conn.execute("UPDATE people SET notes = ? WHERE id = ? OR id = ?", (generated_bio, person_id, f"@{person_id}@"))
            conn.commit()

        details = get_person_details(person_id)
        self.send_json({"status": "ok", "message": "Samantekt endurgerð!", "bio": generated_bio, "details": details})

    def handle_delete_source(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        source_id = params.get('source_id', [''])[0]
        person_id = params.get('person_id', [''])[0]
        if not source_id:
            self.send_error_response(400, "Missing source_id")
            return
        with get_db() as conn:
            conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            conn.commit()
        details = get_person_details(person_id)
        self.send_json({"status": "ok", "details": details})

    def handle_set_profile_image(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        person_id = params.get('person_id', [''])[0]
        image_path = params.get('image_path', [''])[0]
        if not person_id or not image_path:
            self.send_error_response(400, "Missing person_id or image_path")
            return
        with get_db() as conn:
            conn.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (image_path, person_id))
            conn.commit()
        details = get_person_details(person_id)
        self.send_json({"status": "ok", "details": details})

    def handle_get_trees(self):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trees")
            trees = [dict(r) for r in cursor.fetchall()]
        self.send_json(trees)

    def handle_get_tree(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        tree_id = params.get('id', ['loa'])[0]
        
        with get_db() as conn:
            cursor = conn.cursor()
            # Only fetch fields needed for sidebar list — keeps payload small over tunnel
            cursor.execute("""
                SELECT id, tree_id, name, given_names, surname, birth_year, death_year, avatar_url
                FROM people WHERE tree_id = ?
            """, (tree_id,))
            people = [dict(r) for r in cursor.fetchall()]
            
        self.send_json({"id": tree_id, "people": people})

    def handle_get_person(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        person_id = params.get('id', [''])[0].replace('@', '')
        
        if not person_id:
            self.send_error_response(400, "Missing id parameter.")
            return
            
        details = get_person_details(person_id)
        self.send_json(details)

    def handle_run_scraper(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        person_id = params.get('id', [''])[0].replace('@', '')
        name = params.get('name', [''])[0]
        birth = params.get('birth', [''])[0]
        
        if not person_id or not name:
            self.send_error_response(400, "Missing id or name parameter.")
            return
            
        print(f"[API] Running Google AI Research for {name} ({person_id})...")
        res = run_ai_research_for_person(person_id, name, birth)
        
        # Return full updated details
        details = get_person_details(person_id)
        self.send_json({"result": res, "details": details})

    def handle_confirm_suggestion(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        sug_id = params.get('sug_id', [''])[0]
        person_id = params.get('id', [''])[0].replace('@', '')
        
        if not sug_id:
            self.send_error_response(400, "Missing sug_id parameter.")
            return

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_suggestions WHERE id = ?", (sug_id,))
            sug = cursor.fetchone()
            
            if not sug:
                self.send_error_response(404, "Suggestion not found.")
                return
                
            sug_dict = dict(sug)
            clean_id = sug_dict['person_id']
            
            # Update suggestion status to confirmed
            cursor.execute("UPDATE ai_suggestions SET status = 'confirmed' WHERE id = ?", (sug_id,))
            
            # If image, save it into Sögubók (sources gallery) WITHOUT overwriting the profile avatar!
            if sug_dict['type'] == 'image':
                img_path = sug_dict['local_path'] or sug_dict['image_url']
                cursor.execute("""
                    INSERT INTO sources (person_id, title, snippet, link, image_url)
                    VALUES (?, ?, ?, ?, ?)
                """, (clean_id, sug_dict['title'], sug_dict['description'], sug_dict['url'], img_path))
            else:
                cursor.execute("""
                    INSERT INTO sources (person_id, title, snippet, link, image_url)
                    VALUES (?, ?, ?, ?, ?)
                """, (clean_id, sug_dict['title'], sug_dict['description'], sug_dict['url'], sug_dict['image_url']))
                
            conn.commit()

        details = get_person_details(person_id)
        self.send_json({"status": "success", "message": "Uppástunga staðfest!", "details": details})

    def handle_reject_suggestion(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        sug_id = params.get('sug_id', [''])[0]
        person_id = params.get('id', [''])[0].replace('@', '')

        if not sug_id:
            self.send_error_response(400, "Missing sug_id parameter.")
            return

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE ai_suggestions SET status = 'rejected' WHERE id = ?", (sug_id,))
            conn.commit()

        details = get_person_details(person_id)
        self.send_json({"status": "success", "message": "Uppástungu hafnað.", "details": details})

    def handle_add_media(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        person_id = params.get('id', [''])[0].replace('@', '')
        url = params.get('url', [''])[0]
        is_profile = params.get('is_profile', ['false'])[0].lower() == 'true'

        if is_profile and url:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE people SET avatar_url = ? WHERE id = ? OR id = ?", (url, person_id, f"@{person_id}@"))
                conn.commit()

        details = get_person_details(person_id)
        self.send_json({"status": "success", "message": "Mynd vistuð!", "details": details})

    def handle_add_relation(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        person_id = params.get('id', [''])[0].replace('@', '')
        tree_id = params.get('tree', ['loa'])[0]
        rel_name = params.get('name', [''])[0]
        rel_type = params.get('type', ['spouse'])[0]

        if not rel_name:
            self.send_error_response(400, "Missing relation name.")
            return

        with get_db() as conn:
            cursor = conn.cursor()
            rel_id = f"I_ADD_{int(os.urandom(2).hex(), 16)}"
            cursor.execute("""
                INSERT INTO people (id, tree_id, name, sex)
                VALUES (?, ?, ?, ?)
            """, (rel_id, tree_id, rel_name, 'M'))
            
            cursor.execute("""
                INSERT INTO relations (tree_id, person_id, related_id, relation_type)
                VALUES (?, ?, ?, ?)
            """, (tree_id, person_id, rel_id, rel_type))
            conn.commit()

        details = get_person_details(person_id)
        self.send_json({"status": "success", "message": f"Tengsl við {rel_name} vistuð!", "details": details})

    def handle_upload_gedcom(self, query_str):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
        )
        
        if 'gedcom' not in form:
            self.send_error_response(400, "No GEDCOM file provided.")
            return

        fileitem = form['gedcom']
        if not fileitem.filename:
            self.send_error_response(400, "No filename provided.")
            return

        content = fileitem.file.read().decode('utf-8', errors='ignore')
        tree_name = fileitem.filename.replace('.ged', '')
        tree_id = re.sub(r'[^a-zA-Z0-9_]', '_', tree_name).lower()

        lines = content.splitlines()
        current_indi = None
        indi_data = {}
        last_event = None
        people_count = 0

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO trees (id, filename, name) VALUES (?, ?, ?)",
                           (tree_id, fileitem.filename, tree_name))

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
                        b_date = indi_data.get('birth_date', '')
                        d_date = indi_data.get('death_date', '')
                        b_year = re.search(r'\b(1\d{3}|20\d{2})\b', b_date).group(1) if re.search(r'\b(1\d{3}|20\d{2})\b', b_date) else ''
                        d_year = re.search(r'\b(1\d{3}|20\d{2})\b', d_date).group(1) if re.search(r'\b(1\d{3}|20\d{2})\b', d_date) else ''
                        cursor.execute("""
                            INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, death_date, death_year)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (current_indi, tree_id, indi_data.get('name', ''), indi_data.get('sex', ''), b_date, b_year, d_date, d_year))
                        people_count += 1

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

            if current_indi and indi_data:
                b_date = indi_data.get('birth_date', '')
                d_date = indi_data.get('death_date', '')
                b_year = re.search(r'\b(1\d{3}|20\d{2})\b', b_date).group(1) if re.search(r'\b(1\d{3}|20\d{2})\b', b_date) else ''
                d_year = re.search(r'\b(1\d{3}|20\d{2})\b', d_date).group(1) if re.search(r'\b(1\d{3}|20\d{2})\b', d_date) else ''
                cursor.execute("""
                    INSERT OR REPLACE INTO people (id, tree_id, name, sex, birth_date, birth_year, death_date, death_year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (current_indi, tree_id, indi_data.get('name', ''), indi_data.get('sex', ''), b_date, b_year, d_date, d_year))
                people_count += 1

            conn.commit()

        self.send_json({"status": "success", "message": f"Flutt inn {people_count} færslur í {tree_name}!", "tree_id": tree_id})

    def handle_upload_avatar(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        person_id = params.get('id', [''])[0].replace('@', '')
        
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
        )
        
        if 'avatar' not in form:
            self.send_error_response(400, "No avatar file provided.")
            return

        fileitem = form['avatar']
        if not fileitem.filename:
            self.send_error_response(400, "No filename in upload.")
            return

        cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        ext = fileitem.filename.rsplit('.', 1)[-1].lower() if '.' in fileitem.filename else 'jpg'
        filename = f"{person_id}_uploaded.{ext}"
        filepath = os.path.join(cache_dir, filename)
        rel_path = f"images/cache/{filename}"

        with open(filepath, 'wb') as f:
            f.write(fileitem.file.read())

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ? OR id = ?", (rel_path, person_id, f"@{person_id}@"))
            conn.commit()

        details = get_person_details(person_id)
        self.send_json({"status": "success", "message": "Prófílmynd uppfærð!", "details": details})

    def handle_save_settings(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        key = params.get('key', [''])[0].strip()
        cx = params.get('cx', [''])[0].strip()

        if key:
            os.environ["GEMINI_API_KEY"] = key
            env_file = os.path.join(os.path.dirname(__file__), ".env")
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(f"GEMINI_API_KEY={key}\n")
                if cx:
                    f.write(f"GOOGLE_CSE_CX={cx}\n")

        self.send_json({"status": "success", "message": "Stillingar vistaðar!"})

    def handle_proxy_image(self, query_str):
        params = urllib.parse.parse_qs(query_str)
        raw_url = params.get('url', [''])[0]
        if not raw_url:
            self.send_error_response(400, "Missing url parameter.")
            return

        if raw_url.startswith('images/'):
            local_path = os.path.join(os.path.dirname(__file__), raw_url)
            if os.path.exists(local_path):
                ext = local_path.rsplit('.', 1)[-1].lower()
                content_type = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
                with open(local_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(data)
                return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            req = urllib.request.Request(raw_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
                content_type = response.headers.get("Content-Type", "image/jpeg")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error_response(502, f"Could not fetch image: {str(e)}")

class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True  # Kill threads when server exits
    def server_bind(self):
        import socket
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass
        super().server_bind()

def run_server():
    ports_to_try = [8000, 8080, 8081, 5000]
    httpd = None
    active_port = None

    for p in ports_to_try:
        try:
            server_address = ('0.0.0.0', p)
            httpd = ReusableTCPServer(server_address, AncestryHandler)
            active_port = p
            break
        except OSError:
            continue

    if not httpd:
        print("ERROR: Could not bind to any port.")
        sys.exit(1)

    print(f"==================================================")
    print(f"  Saga Ancestry Server Running on http://localhost:{active_port}")
    print(f"  Network access: http://127.0.0.1:{active_port}")
    print(f"  SQLite Database Connected: ancestry.db")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
