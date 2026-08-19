import sys
from print_tree_details import parse_gedcom

def get_descendants(indi_id, indis, fams, visited=None, depth=0):
    if visited is None:
        visited = set()
    if indi_id in visited:
        return []
    visited.add(indi_id)
    
    p = indis.get(indi_id)
    if not p:
        return []
        
    descendants = []
    # Find all families where this person is a spouse
    for fam_id in p['fams']:
        if fam_id in fams:
            f = fams[fam_id]
            for child_id in f['chil']:
                child = indis.get(child_id)
                if child:
                    descendants.append((child, depth + 1, fam_id))
                    descendants.extend(get_descendants(child_id, indis, fams, visited, depth + 1))
    return descendants

def analyze_ancestor(file_path, name_query):
    indis, fams = parse_gedcom(file_path)
    from print_tree_details import get_person_by_name
    matches = get_person_by_name(indis, name_query)
    
    if not matches:
        print(f"No person found matching '{name_query}'")
        return
        
    for p in matches:
        print("=" * 60)
        print(f"DESCENDANTS OF: {p['name']} ({p['id']})")
        print(f"Birth: {p['birth']} | Death: {p['death']}")
        
        # Spouses
        spouses = []
        for fam_id in p['fams']:
            if fam_id in fams:
                f = fams[fam_id]
                sp_id = f['wife'] if p['sex'] == 'M' else f['husb']
                sp = indis.get(sp_id) if sp_id else None
                if sp:
                    spouses.append(f"{sp['name']} (B: {sp['birth']}) via {fam_id}")
        print(f"Spouses: {', '.join(spouses)}")
        
        desc = get_descendants(p['id'], indis, fams)
        print(f"Total descendants: {len(desc)}")
        
        # Print descendants hierarchy
        for child, depth, fam_id in desc:
            indent = "  " * depth
            # Find child's spouses
            c_spouses = []
            for c_fam_id in child['fams']:
                if c_fam_id in fams:
                    cf = fams[c_fam_id]
                    csp_id = cf['wife'] if child['sex'] == 'M' else cf['husb']
                    csp = indis.get(csp_id) if csp_id else None
                    if csp:
                        c_spouses.append(f"{csp['name']} (B: {csp['birth']})")
            sp_str = f" [Maki: {', '.join(c_spouses)}]" if c_spouses else ""
            print(f"{indent}- {child['name']} (B: {child['birth']}, D: {child['death']}){sp_str}")
            
        # Siblings of this ancestor
        if p['famc'] and p['famc'] in fams:
            f = fams[p['famc']]
            siblings = [indis[c] for c in f['chil'] if c != p['id'] and c in indis]
            if siblings:
                print(f"Siblings of {p['name']}:")
                for s in siblings:
                    # Find sibling spouses
                    s_spouses = []
                    for s_fam_id in s['fams']:
                        if s_fam_id in fams:
                            sf = fams[s_fam_id]
                            ssp_id = sf['wife'] if s['sex'] == 'M' else sf['husb']
                            ssp = indis.get(ssp_id) if ssp_id else None
                            if ssp:
                                s_spouses.append(f"{ssp['name']} (B: {ssp['birth']})")
                    ssp_str = f" [Maki: {', '.join(s_spouses)}]" if s_spouses else ""
                    print(f"  - {s['name']} (B: {s['birth']}, D: {s['death']}){ssp_str}")
        print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) > 2:
        analyze_ancestor(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python3 find_descendants.py <ged_file> <name>")
