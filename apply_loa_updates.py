import sys
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def update_loa_tree():
    blocks = parse_gedcom_blocks('loa.ged')
    
    # We will build maps of existing names/IDs
    name_to_id = {}
    fams = {}
    
    for b in blocks:
        if b.type == 'INDI':
            name = b.get_value(['NAME'])
            if name:
                name_clean = name.replace('/', '').strip().lower()
                name_to_id[name_clean] = b.id
        elif b.type == 'FAM':
            fams[b.id] = b

    new_id_counter = 1
    def get_new_indi_id():
        nonlocal new_id_counter
        # Make sure we don't conflict with existing IDs
        while f"I_ADD_{new_id_counter}" in [b.id for b in blocks if b.id]:
            new_id_counter += 1
        return f"I_ADD_{new_id_counter}"

    # 1. Add Lóa's siblings to family @F133@ (Ingólfur Árni Sveinsson & Svana Sigtryggsdóttir)
    # Lóa: Ólafía Ingólfsdóttir (I272771958737)
    # Siblings to add:
    loa_siblings = [
        ("Unnsteinn Fannar Ingólfsson", "M", "2 Sep 1975", ""),
        ("Jón Loftur Ingólfsson", "M", "8 Feb 1980", ""),
        ("Guðbjörg Lilja Ingólfsdóttir", "F", "5 Dec 1985", "")
    ]
    f133_block = fams.get('F133')
    if f133_block:
        for name, sex, birth, death in loa_siblings:
            name_clean = name.lower().strip()
            if name_clean not in name_to_id:
                sid = get_new_indi_id()
                new_block = GedcomBlock(f"0 @{sid}@ INDI")
                new_block.add_tag(1, "NAME", name)
                new_block.add_tag(1, "SEX", sex)
                new_block.add_tag(1, "BIRT")
                new_block.add_tag(2, "DATE", birth)
                new_block.add_tag(1, "FAMC", "@F133@")
                blocks.append(new_block)
                f133_block.add_tag(1, "CHIL", f"@{sid}@")
                name_to_id[name_clean] = sid
                print(f"Added Lóa sibling: {name} (@{sid}@)")

    # 2. Add Svana's siblings to family @F143@ (Sigtryggur Runólfsson & Guðbjörg Sigurpálsdóttir)
    svana_siblings = [
        ("Jón Guðlaugur Sigtryggsson", "M", "1944", ""),
        ("Fríða Hrönn Sigtryggsdóttir", "F", "1946", "2009"),
        ("Rósa Pálína Sigtryggsdóttir", "F", "1947", ""),
        ("Magnús Arnar Sigtryggsson", "M", "1948", "1990"),
        ("Sigrún Sigtryggsdóttir", "F", "1949", ""),
        ("Vilberg Smári Sigtryggsson", "M", "1951", ""),
        ("Hreinn Ómar Sigtryggsson", "M", "1952", ""),
        ("Runólfur Sigtryggsson", "M", "1955", ""),
        ("Svala Sigtryggsdóttir", "F", "1956", ""),
        ("Sveinbarn Sigtryggsson", "M", "1958", "1959")
    ]
    f143_block = fams.get('F143')
    if f143_block:
        for name, sex, birth, death in svana_siblings:
            name_clean = name.lower().strip()
            if name_clean not in name_to_id:
                sid = get_new_indi_id()
                new_block = GedcomBlock(f"0 @{sid}@ INDI")
                new_block.add_tag(1, "NAME", name)
                new_block.add_tag(1, "SEX", sex)
                new_block.add_tag(1, "BIRT")
                new_block.add_tag(2, "DATE", birth)
                if death:
                    new_block.add_tag(1, "DEAT")
                    new_block.add_tag(2, "DATE", death)
                new_block.add_tag(1, "FAMC", "@F143@")
                blocks.append(new_block)
                f143_block.add_tag(1, "CHIL", f"@{sid}@")
                name_to_id[name_clean] = sid
                print(f"Added Svana sibling: {name} (@{sid}@)")

    # 3. Add Lilja's other children to family @F31@ (Loftur Jóhannsson & Lilja Árnadóttir)
    lilja_children = [
        ("Jónína", "F", "25 Aug 1949", ""),
        ("Jóhann Bjarni", "M", "12 Oct 1950", ""),
        ("Gíslunn", "F", "13 Dec 1952", ""),
        ("Heimir Sæberg", "M", "5 May 1959", "")
    ]
    f31_block = fams.get('F31')
    if f31_block:
        for name, sex, birth, death in lilja_children:
            name_clean = name.lower().strip()
            # If name is short (like Jónína), let's make it Jónína Loftsdóttir or keep as is.
            # In the obituary it is listed as Jónína, Jóhann Bjarni etc.
            # Let's add them as Jónína, Jóhann Bjarni, Gíslunn, Heimir Sæberg.
            if name_clean not in name_to_id:
                sid = get_new_indi_id()
                new_block = GedcomBlock(f"0 @{sid}@ INDI")
                new_block.add_tag(1, "NAME", name)
                new_block.add_tag(1, "SEX", sex)
                new_block.add_tag(1, "BIRT")
                new_block.add_tag(2, "DATE", birth)
                new_block.add_tag(1, "FAMC", "@F31@")
                blocks.append(new_block)
                f31_block.add_tag(1, "CHIL", f"@{sid}@")
                name_to_id[name_clean] = sid
                print(f"Added Lilja child: {name} (@{sid}@)")

    # Move 0 TRLR to the end of blocks if it exists
    trailer = next((b for b in blocks if b.type == 'TRLR'), None)
    if trailer:
        blocks.remove(trailer)
        blocks.append(trailer)

    # Save to loa.ged
    save_gedcom_blocks(blocks, 'loa.ged')
    print("loa.ged successfully updated!")

if __name__ == '__main__':
    update_loa_tree()
