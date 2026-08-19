import sys

def parse_gedcom(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    indis = {}
    fams = {}
    current_indi = None
    current_fam = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(' ', 2)
        level = parts[0]
        tag = parts[1]
        val = parts[2] if len(parts) > 2 else ''
        
        # Parse INDI
        if len(parts) > 2 and parts[2] == 'INDI':
            current_indi = parts[1].replace('@', '')
            current_fam = None
            indis[current_indi] = {
                'id': current_indi,
                'name': '',
                'birth': '',
                'birth_place': '',
                'death': '',
                'death_place': '',
                'sex': '',
                'fams': [],
                'famc': None,
                'last_event': None
            }
        # Parse FAM
        elif len(parts) > 2 and parts[2] == 'FAM':
            current_fam = parts[1].replace('@', '')
            current_indi = None
            fams[current_fam] = {
                'id': current_fam,
                'husb': None,
                'wife': None,
                'chil': []
            }
        elif current_indi:
            if tag == 'NAME':
                indis[current_indi]['name'] = val.replace('/', '').strip()
            elif tag == 'SEX':
                indis[current_indi]['sex'] = val
            elif tag == 'FAMS':
                indis[current_indi]['fams'].append(val.replace('@', ''))
            elif tag == 'FAMC':
                indis[current_indi]['famc'] = val.replace('@', '')
            elif tag == 'BIRT':
                indis[current_indi]['last_event'] = 'BIRT'
            elif tag == 'DEAT':
                indis[current_indi]['last_event'] = 'DEAT'
            elif tag == 'DATE':
                last_event = indis[current_indi].get('last_event')
                if last_event == 'BIRT':
                    indis[current_indi]['birth'] = val
                elif last_event == 'DEAT':
                    indis[current_indi]['death'] = val
            elif tag == 'PLAC':
                last_event = indis[current_indi].get('last_event')
                if last_event == 'BIRT':
                    indis[current_indi]['birth_place'] = val
                elif last_event == 'DEAT':
                    indis[current_indi]['death_place'] = val
            elif level == '1':
                indis[current_indi]['last_event'] = None
        elif current_fam:
            if tag == 'HUSB':
                fams[current_fam]['husb'] = val.replace('@', '')
            elif tag == 'WIFE':
                fams[current_fam]['wife'] = val.replace('@', '')
            elif tag == 'CHIL':
                fams[current_fam]['chil'].append(val.replace('@', ''))
                
    return indis, fams

def get_person_by_name(indis, name_query):
    query = name_query.lower()
    matches = []
    for k, v in indis.items():
        if query in v['name'].lower():
            matches.append(v)
    return matches

def print_tree_info(file_path, search_name=None):
    indis, fams = parse_gedcom(file_path)
    
    if search_name:
        matches = get_person_by_name(indis, search_name)
        print(f"Found {len(matches)} matches for '{search_name}':")
        for p in matches:
            print_person_card(p, indis, fams)
    else:
        # Just find some root or interesting people
        print(f"Total INDIs: {len(indis)}, FAMs: {len(fams)}")

def print_person_card(p, indis, fams):
    print("=" * 60)
    print(f"PERSON: {p['name']} ({p['id']})")
    print(f"  Sex: {p['sex']}")
    print(f"  Birth: {p['birth']} | Place: {p['birth_place']}")
    print(f"  Death: {p['death']} | Place: {p['death_place']}")
    
    # Parents
    if p['famc'] and p['famc'] in fams:
        f = fams[p['famc']]
        father = indis.get(f['husb']) if f['husb'] else None
        mother = indis.get(f['wife']) if f['wife'] else None
        f_name = father['name'] if father else "Unknown"
        m_name = mother['name'] if mother else "Unknown"
        print(f"  Parents (FAMC: {p['famc']}):")
        print(f"    Father: {f_name} ({f['husb']})")
        print(f"    Mother: {m_name} ({f['wife']})")
        
        # Siblings
        siblings = [indis[c] for c in f['chil'] if c != p['id'] and c in indis]
        if siblings:
            print("    Siblings:")
            for s in siblings:
                print(f"      - {s['name']} (B: {s['birth']})")
    else:
        print("  Parents: None listed in tree")
        
    # Spouses and Children
    if p['fams']:
        print("  Families as Spouse:")
        for fam_id in p['fams']:
            if fam_id in fams:
                f = fams[fam_id]
                spouse_id = f['wife'] if p['sex'] == 'M' else f['husb']
                spouse = indis.get(spouse_id) if spouse_id else None
                s_name = spouse['name'] if spouse else "Unknown"
                print(f"    Spouse ({fam_id}): {s_name} ({spouse_id})")
                
                children = [indis[c] for c in f['chil'] if c in indis]
                if children:
                    print("    Children:")
                    for c in children:
                        print(f"      - {c['name']} (B: {c['birth']})")
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print_tree_info(sys.argv[1], sys.argv[2])
    elif len(sys.argv) > 1:
        print_tree_info(sys.argv[1])
    else:
        print("Usage: python3 print_tree_details.py <ged_file> [search_name]")
