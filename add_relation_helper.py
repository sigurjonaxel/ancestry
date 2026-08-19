import sys
import os
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def get_next_indi_id(blocks):
    new_id_counter = 500
    existing_ids = set(b.id for b in blocks if b.id)
    while f"I_ADD_{new_id_counter}" in existing_ids:
        new_id_counter += 1
    return f"I_ADD_{new_id_counter}"

def get_next_fam_id(blocks):
    new_id_counter = 500
    existing_ids = set(b.id for b in blocks if b.id)
    while f"F_ADD_{new_id_counter}" in existing_ids:
        new_id_counter += 1
    return f"F_ADD_{new_id_counter}"

def add_relation_to_gedcom(gedcom_path, person_id, rel_type, rel_name, rel_sex):
    if not os.path.exists(gedcom_path):
        return False, f"GEDCOM file {gedcom_path} not found."

    blocks = parse_gedcom_blocks(gedcom_path)
    clean_person_id = person_id.replace('@', '')
    
    person_block = next((b for b in blocks if b.id == clean_person_id), None)
    if not person_block:
        return False, f"Person {clean_person_id} not found in GEDCOM."

    if rel_type == 'child':
        sex = person_block.get_value(['SEX'])
        role = 'HUSB' if sex == 'M' else 'WIFE'
        
        fam_block = None
        for b in blocks:
            if b.type == 'FAM' and b.get_value([role]) == f"@{clean_person_id}@":
                fam_block = b
                break
                
        if not fam_block:
            fam_id = get_next_fam_id(blocks)
            fam_block = GedcomBlock(f"0 @{fam_id}@ FAM")
            fam_block.add_tag(1, role, f"@{clean_person_id}@")
            blocks.append(fam_block)
            person_block.add_tag(1, 'FAMS', f"@{fam_id}@")
        else:
            fam_id = fam_block.id

        child_id = get_next_indi_id(blocks)
        child_block = GedcomBlock(f"0 @{child_id}@ INDI")
        
        parts = rel_name.strip().split()
        if len(parts) > 1:
            name_val = f"{' '.join(parts[:-1])} /{parts[-1]}/"
        else:
            name_val = f"{rel_name} /"
            
        child_block.add_tag(1, "NAME", name_val)
        child_block.add_tag(2, "GIVN", ' '.join(parts[:-1]) if len(parts) > 1 else rel_name)
        child_block.add_tag(2, "SURN", parts[-1] if len(parts) > 1 else "")
        child_block.add_tag(1, "SEX", rel_sex.upper())
        child_block.add_tag(1, "FAMC", f"@{fam_id}@")
        blocks.append(child_block)
        
        fam_block.add_tag(1, "CHIL", f"@{child_id}@")
        print(f"Added child {rel_name} (@{child_id}@) to family @{fam_id}@")

    elif rel_type == 'spouse':
        sex = person_block.get_value(['SEX'])
        role = 'HUSB' if sex == 'M' else 'WIFE'
        spouse_role = 'WIFE' if sex == 'M' else 'HUSB'
        spouse_sex = 'F' if sex == 'M' else 'M'
        
        spouse_id = get_next_indi_id(blocks)
        spouse_block = GedcomBlock(f"0 @{spouse_id}@ INDI")
        parts = rel_name.strip().split()
        if len(parts) > 1:
            name_val = f"{' '.join(parts[:-1])} /{parts[-1]}/"
        else:
            name_val = f"{rel_name} /"
        spouse_block.add_tag(1, "NAME", name_val)
        spouse_block.add_tag(2, "GIVN", ' '.join(parts[:-1]) if len(parts) > 1 else rel_name)
        spouse_block.add_tag(2, "SURN", parts[-1] if len(parts) > 1 else "")
        spouse_block.add_tag(1, "SEX", spouse_sex)
        blocks.append(spouse_block)
        
        fam_id = get_next_fam_id(blocks)
        fam_block = GedcomBlock(f"0 @{fam_id}@ FAM")
        fam_block.add_tag(1, role, f"@{clean_person_id}@")
        fam_block.add_tag(1, spouse_role, f"@{spouse_id}@")
        blocks.append(fam_block)
        
        person_block.add_tag(1, 'FAMS', f"@{fam_id}@")
        spouse_block.add_tag(1, 'FAMS', f"@{fam_id}@")

    elif rel_type in ('father', 'mother'):
        fam_id = person_block.get_value(['FAMC'])
        if fam_id:
            fam_id = fam_id.replace('@', '')
            fam_block = next((b for b in blocks if b.id == fam_id), None)
        else:
            fam_block = None

        if not fam_block:
            fam_id = get_next_fam_id(blocks)
            fam_block = GedcomBlock(f"0 @{fam_id}@ FAM")
            blocks.append(fam_block)
            person_block.add_tag(1, 'FAMC', f"@{fam_id}@")
            fam_block.add_tag(1, 'CHIL', f"@{clean_person_id}@")
            
        parent_role = 'HUSB' if rel_type == 'father' else 'WIFE'
        parent_sex = 'M' if rel_type == 'father' else 'F'
        
        existing_parent = fam_block.get_value([parent_role])
        if existing_parent:
            return False, f"Parent ({rel_type}) already exists for this person."
            
        parent_id = get_next_indi_id(blocks)
        parent_block = GedcomBlock(f"0 @{parent_id}@ INDI")
        parts = rel_name.strip().split()
        if len(parts) > 1:
            name_val = f"{' '.join(parts[:-1])} /{parts[-1]}/"
        else:
            name_val = f"{rel_name} /"
        parent_block.add_tag(1, "NAME", name_val)
        parent_block.add_tag(2, "GIVN", ' '.join(parts[:-1]) if len(parts) > 1 else rel_name)
        parent_block.add_tag(2, "SURN", parts[-1] if len(parts) > 1 else "")
        parent_block.add_tag(1, "SEX", parent_sex)
        parent_block.add_tag(1, 'FAMS', f"@{fam_id}@")
        blocks.append(parent_block)
        
        fam_block.add_tag(1, parent_role, f"@{parent_id}@")
        
    else:
        return False, f"Unknown relation type: {rel_type}"

    # Move TRLR to the end
    trailer = next((b for b in blocks if b.type == 'TRLR'), None)
    if trailer:
        blocks.remove(trailer)
        blocks.append(trailer)

    save_gedcom_blocks(blocks, gedcom_path)
    return True, f"Tengsl við {rel_name} ({rel_type}) hafa verið vistuð í {os.path.basename(gedcom_path)}."

def add_media_to_gedcom(gedcom_path, person_id, filename, is_profile=True):
    if not os.path.exists(gedcom_path):
        return False, f"GEDCOM skrá {gedcom_path} fannst ekki."

    blocks = parse_gedcom_blocks(gedcom_path)
    clean_person_id = person_id.replace('@', '')
    
    person_block = next((b for b in blocks if b.id == clean_person_id), None)
    if not person_block:
        return False, f"Einstaklingur {clean_person_id} fannst ekki í GEDCOM."

    # If setting as profile picture, downgrade any existing profile picture titles to standard Mynd
    if is_profile:
        for i, line in enumerate(person_block.lines):
            if line.startswith('2 TITL ') and ('prófíl' in line.lower() or 'profile' in line.lower()):
                person_block.lines[i] = '2 TITL Mynd'

    # Clean out any broken OBJE blocks where the FILE does not exist on disk
    cleaned_lines = []
    skip_block = False
    for line in person_block.lines:
        if line.startswith('1 OBJE'):
            skip_block = False
            cleaned_lines.append(line)
        elif line.startswith('2 FILE '):
            fpath = line.strip().split(' ', 2)[-1]
            check_path = fpath.lstrip('/')
            if not os.path.exists(check_path) and not fpath.startswith('http'):
                skip_block = True
                if cleaned_lines and cleaned_lines[-1].startswith('1 OBJE'):
                    cleaned_lines.pop()
            else:
                cleaned_lines.append(line)
        elif skip_block and line.strip().split() and line.strip().split()[0].isdigit() and int(line.strip().split()[0]) >= 2:
            continue
        else:
            skip_block = False
            cleaned_lines.append(line)
    person_block.lines = cleaned_lines

    # Find where to insert the new OBJE tags (right after the NAME tag, or at index 1)
    insert_idx = 1
    name_found = False
    for i, line in enumerate(person_block.lines):
        if line.startswith('1 NAME'):
            name_found = True
            insert_idx = i + 1
        elif name_found:
            parts = line.strip().split()
            if parts and parts[0].isdigit() and int(parts[0]) > 1:
                insert_idx = i + 1
            else:
                break
            
    # Detect form/format from extension
    ext = filename.split('.')[-1].upper()
    if ext == 'JPG':
        ext = 'JPEG'

    # Insert new OBJE tags without trailing newlines (serialize() will add them)
    title = "Prófílmynd" if is_profile else "Mynd"
    new_obje_lines = [
        '1 OBJE',
        f'2 FILE {filename}',
        f'2 FORM {ext}',
        f'2 TITL {title}'
    ]
    person_block.lines = person_block.lines[:insert_idx] + new_obje_lines + person_block.lines[insert_idx:]
    
    save_gedcom_blocks(blocks, gedcom_path)
    return True, f"Mynd hefur verið vistuð sem {title.lower()} fyrir viðkomandi."

