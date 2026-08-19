"""Fix the remaining exact duplicates found in both trees."""
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

def merge_exact_duplicates(filename, merge_pairs):
    """
    merge_pairs: list of (duplicate_id, canonical_id)
    """
    print(f"\n=== Fixing {filename} ===")
    blocks = parse_gedcom_blocks(filename)
    
    dup_map = {d: c for d, c in merge_pairs}
    
    # Replace all references
    for b in blocks:
        new_lines = []
        for line in b.lines:
            modified = line
            for dup_id, canon_id in dup_map.items():
                if f"@{dup_id}@" in modified:
                    modified = modified.replace(f"@{dup_id}@", f"@{canon_id}@")
                    print(f"  Replaced ref in {b.id}: @{dup_id}@ -> @{canon_id}@")
            new_lines.append(modified)
        b.lines = new_lines
    
    # Remove duplicate INDI blocks
    removed = 0
    for dup_id in dup_map:
        b = next((x for x in blocks if x.id == dup_id), None)
        if b:
            name = b.get_value(['NAME']) or b.id
            blocks.remove(b)
            print(f"  Removed duplicate: {dup_id} ({name})")
            removed += 1
    
    # Deduplicate children in families
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
    
    save_gedcom_blocks(blocks, filename)
    print(f"  Done! Removed {removed} duplicates from {filename}")

# sigurjon.ged: Benedikt Bergsson (f. 1794) - I212565587151 is dup of I212565586303
# sigurjon.ged: Benedikt Bergsson prófastur (f. 1735) - I212565599108 is dup of I212565587054
merge_exact_duplicates('sigurjon.ged', [
    ('I212565587151', 'I212565586303'),  # Benedikt Bergsson f. 1794
    ('I212565599108', 'I212565587054'),  # Benedikt Bergsson prófastur f. 1735
])

# loa.ged: Jón Jónsson (f. abt 1831) - I272771959265 is dup of I272771958992
merge_exact_duplicates('loa.ged', [
    ('I272771959265', 'I272771958992'),  # Jón Jónsson f. 1831
])

print("\nAll remaining duplicates fixed!")
