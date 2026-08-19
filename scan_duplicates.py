"""
Comprehensive duplicate scan for both trees.
Also finds duplicates that might have slightly different name spellings
but same birth year and death year.
"""
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks
import re

def extract_year(date_str):
    if not date_str:
        return None
    m = re.search(r'\b(1[789]\d{2}|20\d{2})\b', date_str)
    return m.group(1) if m else None

def clean_name(name):
    if not name:
        return ''
    return name.replace('/', '').strip().lower()

def name_similarity(n1, n2):
    """Check if two names are similar enough to be the same person."""
    if n1 == n2:
        return True
    # Check if one name contains the other
    parts1 = set(n1.split())
    parts2 = set(n2.split())
    if not parts1 or not parts2:
        return False
    # If at least the surname matches and one given name
    overlap = parts1 & parts2
    if len(overlap) >= 2:
        return True
    # Check if surname matches (last word)
    words1 = n1.split()
    words2 = n2.split()
    if words1[-1] == words2[-1] and len(overlap) >= 1:
        return True
    return False

def scan_duplicates(filename):
    print(f"\n{'='*60}")
    print(f"  SCANNING: {filename}")
    print(f"{'='*60}")
    
    blocks = parse_gedcom_blocks(filename)
    
    indis = []
    for b in blocks:
        if b.type != 'INDI':
            continue
        name = clean_name(b.get_value(['NAME']))
        birt = b.get_value(['BIRT', 'DATE']) or ''
        deat = b.get_value(['DEAT', 'DATE']) or ''
        birt_year = extract_year(birt)
        deat_year = extract_year(deat)
        
        fams_count = sum(1 for l in b.lines if '1 FAMS' in l)
        famc_count = sum(1 for l in b.lines if '1 FAMC' in l)
        
        indis.append({
            'id': b.id,
            'name': name,
            'birt': birt,
            'deat': deat,
            'birt_year': birt_year,
            'deat_year': deat_year,
            'richness': fams_count + famc_count + len(b.lines)
        })
    
    print(f"Total individuals: {len(indis)}")
    
    # Method 1: Exact name + birth_year + death_year
    exact_dupes = {}
    for i, a in enumerate(indis):
        if not a['birt_year']:
            continue
        for b in indis[i+1:]:
            if not b['birt_year']:
                continue
            if a['birt_year'] == b['birt_year'] and a['name'] == b['name']:
                if a['deat_year'] == b['deat_year'] or not a['deat_year'] or not b['deat_year']:
                    key = tuple(sorted([a['id'], b['id']]))
                    if key not in exact_dupes:
                        exact_dupes[key] = (a, b)
    
    # Method 2: Similar name + same birth_year + same death_year
    fuzzy_dupes = {}
    for i, a in enumerate(indis):
        if not a['birt_year'] or not a['deat_year']:
            continue
        for b in indis[i+1:]:
            if not b['birt_year'] or not b['deat_year']:
                continue
            if a['birt_year'] == b['birt_year'] and a['deat_year'] == b['deat_year']:
                if a['name'] != b['name'] and name_similarity(a['name'], b['name']):
                    key = tuple(sorted([a['id'], b['id']]))
                    if key not in fuzzy_dupes and key not in exact_dupes:
                        fuzzy_dupes[key] = (a, b)
    
    if exact_dupes:
        print(f"\n--- EXACT DUPLICATES ({len(exact_dupes)}) ---")
        for key, (a, b) in sorted(exact_dupes.items()):
            richer = a if a['richness'] > b['richness'] else b
            poorer = b if richer == a else a
            print(f"  ❌ {poorer['name']} ({poorer['birt']}) [{poorer['id']}]")
            print(f"     -> KEEP: [{richer['id']}] (richness: {richer['richness']} vs {poorer['richness']})")
    else:
        print(f"\n✅ No exact duplicates found!")
    
    if fuzzy_dupes:
        print(f"\n--- FUZZY/SIMILAR DUPLICATES ({len(fuzzy_dupes)}) ---")
        for key, (a, b) in sorted(fuzzy_dupes.items()):
            print(f"  ⚠️  '{a['name']}' [{a['id']}] ({a['birt']} - {a['deat']})")
            print(f"      '{b['name']}' [{b['id']}] ({b['birt']} - {b['deat']})")
    else:
        print(f"✅ No fuzzy duplicates found!")
    
    # Method 3: Check for names appearing 3+ times
    name_counts = {}
    for indi in indis:
        if indi['name']:
            if indi['name'] not in name_counts:
                name_counts[indi['name']] = []
            name_counts[indi['name']].append(indi)
    
    triples = {k: v for k, v in name_counts.items() if len(v) >= 3}
    if triples:
        print(f"\n--- NAMES APPEARING 3+ TIMES ({len(triples)}) ---")
        for name, entries in sorted(triples.items()):
            print(f"  '{name}' appears {len(entries)} times:")
            for e in entries:
                print(f"    [{e['id']}] f. {e['birt'] or '?'} d. {e['deat'] or '?'}")
    
    return len(exact_dupes), len(fuzzy_dupes)

if __name__ == '__main__':
    e1, f1 = scan_duplicates('sigurjon.ged')
    e2, f2 = scan_duplicates('loa.ged')
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"sigurjon.ged: {e1} exact dupes, {f1} fuzzy dupes")
    print(f"loa.ged:      {e2} exact dupes, {f2} fuzzy dupes")
