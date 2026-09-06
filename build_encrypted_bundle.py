#!/usr/bin/env python3
import os, sys, sqlite3, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

DEFAULT_PASSWORD = os.environ.get("SAGA_AUTH_PASSWORD", "Saga2026")

def build_and_encrypt(password=DEFAULT_PASSWORD):
    print(f"🔒 Building and encrypting static bundle with password protection...")
    conn = sqlite3.connect('ancestry.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    def get_all(query):
        c.execute(query)
        return [dict(r) for r in c.fetchall()]

    data = {
        'trees': get_all('SELECT * FROM trees'),
        'people': get_all('SELECT * FROM people'),
        'relations': get_all('SELECT * FROM relations'),
        'sources': get_all('SELECT * FROM sources'),
        'suggestions': get_all('SELECT * FROM ai_suggestions'),
        'person_history': get_all('SELECT * FROM person_history'),
        'tree_snapshots': get_all('SELECT * FROM tree_snapshots')
    }

    plaintext = json.dumps(data, ensure_ascii=False).encode('utf-8')
    print(f"  ✓ Database exported: {len(data['people'])} people, {len(plaintext)} bytes")

    # Encrypt with AES-256-GCM + PBKDF2
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = kdf.derive(password.encode('utf-8'))
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    combined = salt + iv + ciphertext
    with open('docs/static_data.enc', 'wb') as f:
        f.write(combined)
    print(f"  ✓ Encrypted bundle written to docs/static_data.enc ({len(combined)} bytes)")

    # Replace docs/static_data.json with stub so no unencrypted data is on GitHub!
    stub = {
        "status": "encrypted",
        "message": "Gagnagrunnurinn er dulkóðaður með AES-256. Notið vefviðmót Sögu til að afkóða gögnin með aðgangsorði."
    }
    with open('docs/static_data.json', 'w', encoding='utf-8') as f:
        json.dump(stub, f, ensure_ascii=False, indent=2)
    print("  ✓ Cleansed docs/static_data.json (stub only, no plaintext)")

if __name__ == '__main__':
    pwd = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PASSWORD
    build_and_encrypt(pwd)
