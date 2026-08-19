"""
Find and merge duplicate INDI records in sigurjon.ged.
Duplicates are identified by having the same birth date AND death date AND similar name.
The "canonical" version is the one with the most data (most family links).
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

def find_duplicate_individuals(blocks):
    """Find INDI records that are duplicates (same birth+death dates, similar names)."""
    indis = []
    for b in blocks:
        if b.type != 'INDI':
            continue
        name = clean_name(b.get_value(['NAME']))
        birt = b.get_value(['BIRT', 'DATE']) or ''
        deat = b.get_value(['DEAT', 'DATE']) or ''
        birt_year = extract_year(birt)
        deat_year = extract_year(deat)
        
        # Count family links as a measure of "richness"
        fams_count = sum(1 for l in b.lines if '1 FAMS' in l)
        famc_count = sum(1 for l in b.lines if '1 FAMC' in l)
        
        indis.append({
            'block': b,
            'id': b.id,
            'name': name,
            'birt': birt,
            'deat': deat,
            'birt_year': birt_year,
            'deat_year': deat_year,
            'richness': fams_count + famc_count + len(b.lines)
        })
    
    # Group by (name, birth_year, death_year)
    groups = {}
    for indi in indis:
        if not indi['birt_year'] and not indi['deat_year']:
            continue  # Can't match without any date
        key = (indi['name'], indi['birt_year'], indi['deat_year'])
        if key not in groups:
            groups[key] = []
        groups[key].append(indi)
    
    # Find groups with >1 entry (duplicates)
    duplicates = {}  # duplicate_id -> canonical_id
    for key, group in groups.items():
        if len(group) < 2:
            continue
        # Sort by richness, most rich first
        group.sort(key=lambda x: x['richness'], reverse=True)
        canonical = group[0]
        for dup in group[1:]:
            duplicates[dup['id']] = canonical['id']
            print(f"  DUPLICATE: {dup['id']} ({dup['name']}, {dup['birt']}) -> {canonical['id']}")
    
    return duplicates

def merge_duplicates(filename):
    print(f"\n=== Merging duplicate individuals in {filename} ===")
    blocks = parse_gedcom_blocks(filename)
    
    duplicates = find_duplicate_individuals(blocks)
    
    if not duplicates:
        print("No duplicate individuals found.")
        return
    
    print(f"\nFound {len(duplicates)} duplicate individuals to merge.")
    
    # Replace all references to duplicate IDs with canonical IDs
    for b in blocks:
        new_lines = []
        for line in b.lines:
            modified_line = line
            for dup_id, canon_id in duplicates.items():
                if f"@{dup_id}@" in modified_line:
                    modified_line = modified_line.replace(f"@{dup_id}@", f"@{canon_id}@")
                    print(f"  Replaced ref in {b.id}: @{dup_id}@ -> @{canon_id}@")
            new_lines.append(modified_line)
        b.lines = new_lines
    
    # Remove duplicate INDI blocks
    blocks_to_remove = [b for b in blocks if b.type == 'INDI' and b.id in duplicates]
    for b in blocks_to_remove:
        name = b.get_value(['NAME']) or b.id
        blocks.remove(b)
        print(f"  Removed duplicate INDI: {b.id} ({name})")
    
    # Also remove families that now have duplicate children or are empty
    for b in blocks:
        if b.type != 'FAM':
            continue
        seen_children = set()
        new_lines = []
        for line in b.lines:
            if line.startswith('1 CHIL'):
                child_id = line.split()[-1]
                if child_id in seen_children:
                    print(f"  Removed duplicate CHIL {child_id} from {b.id}")
                    continue
                seen_children.add(child_id)
            new_lines.append(line)
        b.lines = new_lines
    
    # Remove families with no HUSB, no WIFE, and no CHIL (orphaned)
    orphaned = []
    for b in blocks:
        if b.type != 'FAM':
            continue
        has_husb = any('1 HUSB' in l for l in b.lines)
        has_wife = any('1 WIFE' in l for l in b.lines)
        has_chil = any('1 CHIL' in l for l in b.lines)
        if not has_husb and not has_wife and not has_chil:
            orphaned.append(b)
    for b in orphaned:
        blocks.remove(b)
        print(f"  Removed orphaned FAM: {b.id}")
    
    save_gedcom_blocks(blocks, filename)
    print(f"\n{filename} merged! Removed {len(blocks_to_remove)} duplicate individuals.")

if __name__ == '__main__':
    merge_duplicates('sigurjon.ged')
