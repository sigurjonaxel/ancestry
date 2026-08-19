import sys
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def add_daughters():
    blocks = parse_gedcom_blocks('loa.ged')
    
    loa_id = 'I272771958737'
    
    # Find Jón Óskar's family ID (F_ADD_200)
    jon_fam_id = 'F_ADD_200'
    fam_block = next((b for b in blocks if b.id == jon_fam_id), None)
    
    if not fam_block:
        # Fallback search
        for b in blocks:
            if b.type == 'FAM' and b.get_value(['WIFE']) == f"@{loa_id}@" and (b.get_value(['DIV']) == 'Y' or b.get_value(['HUSB']) == '@I_ADD_200@'):
                fam_block = b
                jon_fam_id = b.id
                break
                
    if not fam_block:
        print("Could not find family for Lóa and Jón Óskar.")
        return

    # Helper to get unique INDI IDs
    def get_new_indi_id(base_num):
        num = base_num
        while f"I_ADD_{num}" in [b.id for b in blocks if b.id]:
            num += 1
        return f"I_ADD_{num}"

    # 1. Add Vala Björk Jónsdóttir
    vala_id = get_new_indi_id(301)
    vala_block = GedcomBlock(f"0 @{vala_id}@ INDI")
    vala_block.add_tag(1, "NAME", "Vala Björk /Jónsdóttir/")
    vala_block.add_tag(2, "GIVN", "Vala Björk")
    vala_block.add_tag(2, "SURN", "Jónsdóttir")
    vala_block.add_tag(1, "SEX", "F")
    vala_block.add_tag(1, "FAMC", f"@{jon_fam_id}@")
    blocks.append(vala_block)
    fam_block.add_tag(1, "CHIL", f"@{vala_id}@")
    print(f"Added Vala Björk Jónsdóttir (@{vala_id}@)")

    # 2. Add Sara Kristín Jónsdóttir
    sara_id = get_new_indi_id(302)
    sara_block = GedcomBlock(f"0 @{sara_id}@ INDI")
    sara_block.add_tag(1, "NAME", "Sara Kristín /Jónsdóttir/")
    sara_block.add_tag(2, "GIVN", "Sara Kristín")
    sara_block.add_tag(2, "SURN", "Jónsdóttir")
    sara_block.add_tag(1, "SEX", "F")
    sara_block.add_tag(1, "FAMC", f"@{jon_fam_id}@")
    blocks.append(sara_block)
    fam_block.add_tag(1, "CHIL", f"@{sara_id}@")
    print(f"Added Sara Kristín Jónsdóttir (@{sara_id}@)")

    # Move TRLR to the end
    trailer = next((b for b in blocks if b.type == 'TRLR'), None)
    if trailer:
        blocks.remove(trailer)
        blocks.append(trailer)

    save_gedcom_blocks(blocks, 'loa.ged')
    print("loa.ged successfully updated with Vala Björk and Sara Kristín!")

if __name__ == '__main__':
    add_daughters()
