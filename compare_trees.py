import re
import sys
from print_tree_details import parse_gedcom

def parse_aettarmot(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    people = []
    current_spouses = []
    
    # Regex to match lines like "1. Einar Sigurjónsson (f. 04.08.1920 – d. 15.07.2004)"
    # or "1.1. Steinþór Einarsson (f. 19.01.1949)"
    # or "- 1.1.3.1. Andrea Irena Denisdóttir (f. 02.07.2003)"
    person_re = re.compile(r'^(?:-\s*)?([\d\.]+)\s+([^(\n]+?)\s*\((?:f\.\s*([\d\.\s,]+))?(?:\s*–\s*d\.\s*([\d\.\s,]+))?\)')
    
    # Matches Maki: Name (f. Date)
    spouse_re = re.compile(r'^(?:-\s*)?Maki(?:\s+\d+)?:?\s+([^(\n]+?)\s*\((?:f\.\s*([\d\.\s,]+))?(?:\s*–\s*d\.\s*([\d\.\s,]+))?\)')
    
    # Also handle Maki without parentheses or with other formats
    # like "Maki Ásta Sigríður Jónsdóttir (f. 0909,1998)"
    
    # We will track current hierarchy
    last_person = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # Match person
        m = person_re.match(line)
        if m:
            num = m.group(1).strip('.')
            name = m.group(2).strip()
            birth = m.group(3).strip() if m.group(3) else ''
            death = m.group(4).strip() if m.group(4) else ''
            
            # Simple clean up of names
            name = name.replace('/', '').strip()
            
            # Parent num is the prefix (e.g. parent of 1.1.2 is 1.1)
            parts = num.split('.')
            parent_num = '.'.join(parts[:-1]) if len(parts) > 1 else None
            
            person_dict = {
                'num': num,
                'parent_num': parent_num,
                'name': name,
                'birth': birth,
                'death': death,
                'spouses': [],
                'type': 'descendant'
            }
            people.append(person_dict)
            last_person = person_dict
            continue
            
        # Match spouse
        m_sp = spouse_re.match(line)
        if m_sp:
            name = m_sp.group(1).strip()
            birth = m_sp.group(2).strip() if m_sp.group(2) else ''
            death = m_sp.group(3).strip() if m_sp.group(3) else ''
            
            name = name.replace('/', '').strip()
            
            spouse_dict = {
                'name': name,
                'birth': birth,
                'death': death,
                'type': 'spouse'
            }
            if last_person:
                last_person['spouses'].append(spouse_dict)
            continue
            
    return people

def compare(aettarmot_path, ged_path):
    aett_people = parse_aettarmot(aettarmot_path)
    ged_indis, ged_fams = parse_gedcom(ged_path)
    
    # De-duplicate aett_people by name
    seen_names = set()
    unique_aett_people = []
    for p in aett_people:
        name_key = p['name'].lower().strip()
        if name_key not in seen_names:
            seen_names.add(name_key)
            unique_aett_people.append(p)
            
    print(f"Loaded {len(unique_aett_people)} unique people from aettarmot.md")
    print(f"Loaded {len(ged_indis)} individuals from {ged_path}")
    
    # Check each person in aettarmot
    missing_descendants = []
    missing_spouses = []
    
    for ap in unique_aett_people:
        # Search by name in ged_indis
        matches = []
        ap_name_clean = ap['name'].lower().strip()
        for gk, gv in ged_indis.items():
            gv_name_clean = gv['name'].lower().strip()
            if ap_name_clean == gv_name_clean:
                matches.append(gv)
            elif ap_name_clean in gv_name_clean or gv_name_clean in ap_name_clean:
                # partial match
                matches.append(gv)
                
        if not matches:
            missing_descendants.append(ap)
        else:
            # Check spouses
            matched_g = matches[0] # assume first match
            # Get spouses from ged
            ged_spouses = []
            for fam_id in matched_g['fams']:
                if fam_id in ged_fams:
                    f = ged_fams[fam_id]
                    sp_id = f['wife'] if matched_g['sex'] == 'M' else f['husb']
                    sp = ged_indis.get(sp_id)
                    if sp:
                        ged_spouses.append(sp['name'].lower().strip())
            
            for asp in ap['spouses']:
                asp_name_clean = asp['name'].lower().strip()
                sp_matched = False
                for gsp in ged_spouses:
                    if asp_name_clean == gsp or asp_name_clean in gsp or gsp in asp_name_clean:
                        sp_matched = True
                        break
                if not sp_matched:
                    missing_spouses.append((ap['name'], asp))
                    
    print("\n=== MISSING DESCENDANTS IN GEDCOM ===")
    for md in sorted(missing_descendants, key=lambda x: x['num']):
        print(f"{md['num']}: {md['name']} (B: {md['birth']})")
        
    print("\n=== MISSING SPOUSES IN GEDCOM ===")
    seen_spouses = set()
    for p_name, ms in missing_spouses:
        spouse_key = f"{p_name.lower()} -> {ms['name'].lower()}"
        if spouse_key not in seen_spouses:
            seen_spouses.add(spouse_key)
            print(f"Spouse of {p_name}: {ms['name']} (B: {ms['birth']})")


if __name__ == '__main__':
    aettarmot_path = '/home/sigurjonaxel/.gemini/antigravity/brain/d5433bd9-cdaf-450e-94ba-be91aad354ce/.system_generated/steps/259/content.md'
    ged_path = 'sigurjon.ged'
    compare(aettarmot_path, ged_path)
