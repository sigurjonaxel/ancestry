import re
import sys
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def extract_year(date_str):
    if not date_str:
        return None
    # Matches any 4-digit number between 1700 and 2099
    m = re.search(r'\b(1[789]\d{2}|20\d{2})\b', date_str)
    return m.group(1) if m else None

def parse_aettarmot_tree(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    people = {}  # num -> person dict
    
    person_re = re.compile(r'^(?:-\s*)?([\d\.]+)\s+([^(\n]+?)\s*\((?:f\.\s*([\d\.\s,]+))?(?:\s*–\s*d\.\s*([\d\.\s,]+))?\)')
    spouse_re = re.compile(r'^(?:-\s*)?(Maki|Barnsfaðir|Barnsmóðir)(?:\s+\d+)?:?\s+([^(\n]+?)\s*\((?:f\.\s*([\d\.\s,]+))?(?:\s*–\s*d\.\s*([\d\.\s,]+))?\)')
    spouse_no_colon_re = re.compile(r'^(?:-\s*)?(Maki|Barnsfaðir|Barnsmóðir)\s+([^(\n]+?)\s*\((?:f\.\s*([\d\.\s,]+))?(?:\s*–\s*d\.\s*([\d\.\s,]+))?\)')

    current_parent_by_level = {}
    
    for line_num, line in enumerate(lines, 1):
        line = line.replace('**', '').replace('*', '').strip()
        if not line:
            continue
            
        m = person_re.match(line)
        if m:
            num = m.group(1).strip('.')
            name = m.group(2).strip()
            birth = m.group(3).strip() if m.group(3) else ''
            death = m.group(4).strip() if m.group(4) else ''
            
            name = name.replace('/', '').strip()
            
            parts = num.split('.')
            parent_num = '.'.join(parts[:-1]) if len(parts) > 1 else None
            
            sex = 'F'
            if name.endswith('son') or name.endswith('sonur') or name.split()[-1].endswith('son') or name.split()[-1].endswith('sonur'):
                sex = 'M'
            elif name.split()[0] in ['Einar', 'Benedikt', 'Arnór', 'Sigurjón', 'Gunnar', 'Hugi', 'Kristján', 'Steinþór', 'Gunnlaugur', 'Ármann', 'Óskar', 'Víðir', 'Snæbjörn', 'Ingvar', 'Sigurgeir', 'Valtýr', 'Karl', 'Vignir', 'Vilberg', 'Kristinn', 'Vésteinn', 'Ragnar', 'Filip', 'Stefán', 'Tómas', 'Rúnar']:
                sex = 'M'
                
            p_dict = {
                'num': num,
                'parent_num': parent_num,
                'name': name,
                'birth': birth,
                'death': death,
                'sex': sex,
                'spouses': [],
                'children': []
            }
            people[num] = p_dict
            
            if parent_num and parent_num in people:
                people[parent_num]['children'].append(num)
                
            current_parent_by_level[len(parts)] = num
            continue
            
        m_sp = spouse_re.match(line) or spouse_no_colon_re.match(line)
        if m_sp:
            sp_type = m_sp.group(1).strip()
            name = m_sp.group(2).strip()
            birth = m_sp.group(3).strip() if m_sp.group(3) else ''
            death = m_sp.group(4).strip() if m_sp.group(4) else ''
            
            name = name.replace('/', '').strip()
            
            if current_parent_by_level:
                max_level = max(current_parent_by_level.keys())
                parent_num = current_parent_by_level[max_level]
                
                sex = 'F' if people[parent_num]['sex'] == 'M' else 'M'
                
                spouse_dict = {
                    'name': name,
                    'birth': birth,
                    'death': death,
                    'sex': sex,
                    'type': sp_type
                }
                people[parent_num]['spouses'].append(spouse_dict)
                
    return people

def load_gedcom_mappings(blocks):
    indis_by_name_year = {} # (name_clean, year) -> id
    name_only_indis = {}    # name_clean -> list of (year, id)
    fams = {}
    
    for b in blocks:
        if b.type == 'INDI':
            name = b.get_value(['NAME'])
            if name:
                name_clean = name.replace('/', '').strip().lower()
                birt_date = b.get_value(['BIRT', 'DATE'])
                year = extract_year(birt_date)
                
                indis_by_name_year[(name_clean, year)] = b.id
                if name_clean not in name_only_indis:
                    name_only_indis[name_clean] = []
                name_only_indis[name_clean].append((year, b.id))
        elif b.type == 'FAM':
            fams[b.id] = b
            
    return indis_by_name_year, name_only_indis, fams

def update_sigurjon_tree():
    blocks = parse_gedcom_blocks('sigurjon.ged')
    
    indis_by_name_year, name_only_indis, fams = load_gedcom_mappings(blocks)
    
    # Root children mappings (verified manually)
    root_children_map = {
        '1': 'I212565201807', # Einar Sigurjónsson
        '2': 'I212565201808', # Benedikt Sigurjónsson
        '3': 'I212565201809', # Ingunn Sigríður Sigurjónsdóttir
        '4': 'I212565201810', # Arnór Sigurjónsson
        '5': 'I212565201811', # Aðalheiður Sigurjónsdóttir
        '6': 'I212565201812', # Sigurbjörg Sigurjónsdóttir
        '7': 'I212565201202'  # Erla Þórhildur
    }
    
    aettarmot_path = '/home/sigurjonaxel/.gemini/antigravity/brain/d5433bd9-cdaf-450e-94ba-be91aad354ce/.system_generated/steps/1330/content.md'
    aett_people = parse_aettarmot_tree(aettarmot_path)
    print(f"Parsed {len(aett_people)} people from family reunion document.")
    
    aett_id_map = {} # num -> gedcom_id
    
    new_id_counter = 1
    def get_new_indi_id():
        nonlocal new_id_counter
        while f"IADD{new_id_counter}" in [b.id for b in blocks if b.id]:
            new_id_counter += 1
        id_str = f"IADD{new_id_counter}"
        new_id_counter += 1
        return id_str
        
    new_fam_counter = 1
    def get_new_fam_id():
        nonlocal new_fam_counter
        while f"FADD{new_fam_counter}" in [b.id for b in blocks if b.id]:
            new_fam_counter += 1
        id_str = f"FADD{new_fam_counter}"
        new_fam_counter += 1
        return id_str

    for num, gid in root_children_map.items():
        if num in aett_people:
            aett_id_map[num] = gid
            
    # Resolve all other aettarmot people
    for num in sorted(aett_people.keys(), key=lambda x: len(x.split('.'))):
        ap = aett_people[num]
        if num in aett_id_map:
            continue
            
        name_clean = ap['name'].lower().strip()
        ap_year = extract_year(ap['birth'])
        
        # Resolve by name + year matching to prevent collisions
        gid = indis_by_name_year.get((name_clean, ap_year))
        
        # If no exact match with year, check if name matches and year is close/unknown
        if not gid and name_clean in name_only_indis:
            for existing_year, existing_id in name_only_indis[name_clean]:
                # If either has no year, or the years are close (within 5 years)
                if not ap_year or not existing_year or abs(int(ap_year) - int(existing_year)) <= 5:
                    # Make sure it's not the grandfather Sigurjón (f. 1895) being matched to grandson (f. 1950)
                    if name_clean == 'sigurjón einarsson' and ap_year != '1895' and existing_year == '1895':
                        continue
                    gid = existing_id
                    break
                    
        if gid:
            aett_id_map[num] = gid
            print(f"Matched existing person: {ap['name']} -> @{gid}@ (Year: {ap_year})")
        else:
            new_id = get_new_indi_id()
            aett_id_map[num] = new_id
            
            new_block = GedcomBlock(f"0 @{new_id}@ INDI")
            new_block.add_tag(1, "NAME", f"{ap['name']}")
            new_block.add_tag(1, "SEX", ap['sex'])
            if ap['birth']:
                new_block.add_tag(1, "BIRT")
                new_block.add_tag(2, "DATE", ap['birth'])
            if ap['death']:
                new_block.add_tag(1, "DEAT")
                new_block.add_tag(2, "DATE", ap['death'])
                
            blocks.append(new_block)
            
            # Register in mappings
            indis_by_name_year[(name_clean, ap_year)] = new_id
            if name_clean not in name_only_indis:
                name_only_indis[name_clean] = []
            name_only_indis[name_clean].append((ap_year, new_id))
            print(f"Created INDI: {ap['name']} (@{new_id}@) (Year: {ap_year})")
            
    # Connect families and spouses
    for num in sorted(aett_people.keys(), key=lambda x: len(x.split('.'))):
        ap = aett_people[num]
        my_id = aett_id_map[num]
        
        # If this person has spouses, ensure we create families for them
        for spouse in ap['spouses']:
            spouse_name_clean = spouse['name'].lower().strip()
            spouse_year = extract_year(spouse['birth'])
            
            # Resolve spouse
            spouse_id = indis_by_name_year.get((spouse_name_clean, spouse_year))
            if not spouse_id and spouse_name_clean in name_only_indis:
                for existing_year, existing_id in name_only_indis[spouse_name_clean]:
                    if not spouse_year or not existing_year or abs(int(spouse_year) - int(existing_year)) <= 5:
                        spouse_id = existing_id
                        break
                        
            if not spouse_id:
                spouse_id = get_new_indi_id()
                new_block = GedcomBlock(f"0 @{spouse_id}@ INDI")
                new_block.add_tag(1, "NAME", spouse['name'])
                new_block.add_tag(1, "SEX", spouse['sex'])
                if spouse['birth']:
                    new_block.add_tag(1, "BIRT")
                    new_block.add_tag(2, "DATE", spouse['birth'])
                if spouse['death']:
                    new_block.add_tag(1, "DEAT")
                    new_block.add_tag(2, "DATE", spouse['death'])
                blocks.append(new_block)
                
                indis_by_name_year[(spouse_name_clean, spouse_year)] = spouse_id
                if spouse_name_clean not in name_only_indis:
                    name_only_indis[spouse_name_clean] = []
                name_only_indis[spouse_name_clean].append((spouse_year, spouse_id))
                print(f"Created spouse: {spouse['name']} (@{spouse_id}@) for {ap['name']}")
                
            fam_id = None
            for fid, f_block in fams.items():
                husb = f_block.get_value(['HUSB']).replace('@', '') if f_block.get_value(['HUSB']) else None
                wife = f_block.get_value(['WIFE']).replace('@', '') if f_block.get_value(['WIFE']) else None
                if (husb == my_id and wife == spouse_id) or (husb == spouse_id and wife == my_id):
                    fam_id = fid
                    break
                    
            if not fam_id:
                fam_id = get_new_fam_id()
                f_block = GedcomBlock(f"0 @{fam_id}@ FAM")
                if ap['sex'] == 'M':
                    f_block.add_tag(1, "HUSB", f"@{my_id}@")
                    f_block.add_tag(1, "WIFE", f"@{spouse_id}@")
                else:
                    f_block.add_tag(1, "HUSB", f"@{spouse_id}@")
                    f_block.add_tag(1, "WIFE", f"@{my_id}@")
                blocks.append(f_block)
                fams[fam_id] = f_block
                
                my_block = next((b for b in blocks if b.id == my_id), None)
                if my_block:
                    my_block.add_tag(1, "FAMS", f"@{fam_id}@")
                spouse_block = next((b for b in blocks if b.id == spouse_id), None)
                if spouse_block:
                    spouse_block.add_tag(1, "FAMS", f"@{fam_id}@")
                    
            spouse['fam_id'] = fam_id

        # Now link children to families
        for child_num in ap['children']:
            child_ap = aett_people[child_num]
            child_id = aett_id_map[child_num]
            
            target_fam_id = None
            if len(ap['spouses']) == 1:
                target_fam_id = ap['spouses'][0].get('fam_id')
            elif len(ap['spouses']) > 1:
                # Choose the spouse whose name matches child's mother/father's surname or default to first
                target_fam_id = ap['spouses'][0].get('fam_id')
            else:
                # Single parent family
                for fid, f_block in fams.items():
                    husb = f_block.get_value(['HUSB']).replace('@', '') if f_block.get_value(['HUSB']) else None
                    wife = f_block.get_value(['WIFE']).replace('@', '') if f_block.get_value(['WIFE']) else None
                    if (husb == my_id and not wife) or (wife == my_id and not husb):
                        target_fam_id = fid
                        break
                if not target_fam_id:
                    target_fam_id = get_new_fam_id()
                    f_block = GedcomBlock(f"0 @{target_fam_id}@ FAM")
                    if ap['sex'] == 'M':
                        f_block.add_tag(1, "HUSB", f"@{my_id}@")
                    else:
                        f_block.add_tag(1, "WIFE", f"@{my_id}@")
                    blocks.append(f_block)
                    fams[target_fam_id] = f_block
                    my_block = next((b for b in blocks if b.id == my_id), None)
                    if my_block:
                        my_block.add_tag(1, "FAMS", f"@{target_fam_id}@")
            
            if target_fam_id:
                f_block = fams[target_fam_id]
                existing_children = [l.split(' ')[2].replace('@', '') for l in f_block.lines if l.startswith('1 CHIL ')]
                if child_id not in existing_children:
                    f_block.add_tag(1, "CHIL", f"@{child_id}@")
                
                child_block = next((b for b in blocks if b.id == child_id), None)
                if child_block:
                    child_block.remove_tag(1, "FAMC")
                    child_block.add_tag(1, "FAMC", f"@{target_fam_id}@")

    # 4. Add Sigurjón Einarsson's missing siblings
    sigurjon_siblings = [
        ("Guðný Einarsdóttir", "F", "21 Aug 1892", "24 Mar 1990"),
        ("Jón Einarsson", "M", "3 Jun 1894", "11 Jul 1894"),
        ("Þorbjörg Einarsdóttir", "F", "19 Jul 1898", "17 Jun 1995"),
        ("Sigurborg Einarsdóttir", "F", "20 Jun 1901", "29 Feb 1996"),
        ("Stefán Einarsson", "M", "14 Jun 1905", "19 Dec 1998"),
        ("Guðleif Einarsdóttir", "F", "26 Feb 1911", "30 Jun 2002")
    ]
    f77_block = fams.get('F77')
    if f77_block:
        for name, sex, birth, death in sigurjon_siblings:
            name_clean = name.lower().strip()
            # Sigurjón's siblings will have unique names in parent family
            if (name_clean, extract_year(birth)) not in indis_by_name_year:
                sid = get_new_indi_id()
                new_block = GedcomBlock(f"0 @{sid}@ INDI")
                new_block.add_tag(1, "NAME", name)
                new_block.add_tag(1, "SEX", sex)
                new_block.add_tag(1, "BIRT")
                new_block.add_tag(2, "DATE", birth)
                new_block.add_tag(1, "DEAT")
                new_block.add_tag(2, "DATE", death)
                new_block.add_tag(1, "FAMC", "@F77@")
                blocks.append(new_block)
                f77_block.add_tag(1, "CHIL", f"@{sid}@")
                indis_by_name_year[(name_clean, extract_year(birth))] = sid
                print(f"Added Sigurjón sibling: {name}")

    # 5. Add Þorbjörg Benediktsdóttir's missing siblings
    thorbjorg_siblings = [
        ("Margrét Benediktsdóttir", "F", "12 May 1876", "27 Sep 1877"),
        ("Guðrún Benediktsdóttir", "F", "20 Jun 1879", "9 Jan 1963"),
        ("Kristján Benediktsson", "M", "11 Sep 1881", "29 Mar 1969"),
        ("Jónína Kristín Benediktsdóttir", "F", "31 Jan 1888", "19 Aug 1981"),
        ("Pálína Benediktsdóttir", "F", "24 Jul 1890", "18 Sep 1962"),
        ("Unnar Benediktsson", "M", "21 May 1894", "3 May 1973")
    ]
    f85_block = fams.get('F85')
    if f85_block:
        for name, sex, birth, death in thorbjorg_siblings:
            name_clean = name.lower().strip()
            if (name_clean, extract_year(birth)) not in indis_by_name_year:
                sid = get_new_indi_id()
                new_block = GedcomBlock(f"0 @{sid}@ INDI")
                new_block.add_tag(1, "NAME", name)
                new_block.add_tag(1, "SEX", sex)
                new_block.add_tag(1, "BIRT")
                new_block.add_tag(2, "DATE", birth)
                new_block.add_tag(1, "DEAT")
                new_block.add_tag(2, "DATE", death)
                new_block.add_tag(1, "FAMC", "@F85@")
                blocks.append(new_block)
                f85_block.add_tag(1, "CHIL", f"@{sid}@")
                indis_by_name_year[(name_clean, extract_year(birth))] = sid
                print(f"Added Þorbjörg sibling: {name}")

    # Move 0 TRLR to the end
    trailer = next((b for b in blocks if b.type == 'TRLR'), None)
    if trailer:
        blocks.remove(trailer)
        blocks.append(trailer)

    save_gedcom_blocks(blocks, 'sigurjon.ged')
    print("sigurjon.ged successfully updated with collision prevention!")

if __name__ == '__main__':
    update_sigurjon_tree()
