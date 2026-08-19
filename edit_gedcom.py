import re

class GedcomBlock:
    def __init__(self, header_line):
        self.header = header_line.strip()
        self.lines = [self.header]
        
        # Parse ID and Type from header, e.g. "0 @I123@ INDI" -> id="I123", type="INDI"
        # or "0 HEAD" -> id=None, type="HEAD"
        parts = self.header.split(' ', 2)
        self.id = None
        self.type = None
        if len(parts) > 2:
            if parts[1].startswith('@') and parts[1].endswith('@'):
                self.id = parts[1].replace('@', '')
                self.type = parts[2]
            else:
                self.type = parts[1]
        elif len(parts) > 1:
            self.type = parts[1]
            
    def add_line(self, line):
        self.lines.append(line.strip())
        
    def get_value(self, tag_path):
        # tag_path is like ['NAME'] or ['BIRT', 'DATE']
        current_lines = self.lines[1:]
        for depth, tag in enumerate(tag_path, 1):
            matching_line = None
            prefix = f"{depth} {tag}"
            for line in current_lines:
                if line.startswith(prefix + " ") or line == prefix:
                    matching_line = line
                    break
            if not matching_line:
                return None
            if depth == len(tag_path):
                parts = matching_line.split(' ', 2)
                return parts[2] if len(parts) > 2 else ''
            # Filter current_lines to only sub-lines of this tag
            # (which have level > depth and appear before the next level <= depth line)
            # For simplicity, we just find the index of the matching line
            # and take lines after it that have higher levels.
            idx = current_lines.index(matching_line)
            sub_lines = []
            for l in current_lines[idx+1:]:
                l_parts = l.split(' ', 1)
                l_level = int(l_parts[0])
                if l_level <= depth:
                    break
                sub_lines.append(l)
            current_lines = sub_lines
        return None

    def add_tag(self, level, tag, value=""):
        line = f"{level} {tag}"
        if value:
            line += f" {value}"
        self.lines.append(line)
        
    def remove_tag(self, level, tag):
        prefix = f"{level} {tag}"
        self.lines = [l for l in self.lines if not (l.startswith(prefix + " ") or l == prefix)]

    def serialize(self):
        return "\n".join(self.lines)

def parse_gedcom_blocks(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    blocks = []
    current_block = None
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
        if line_strip.startswith('0 '):
            if current_block:
                blocks.append(current_block)
            current_block = GedcomBlock(line)
        else:
            if current_block:
                current_block.add_line(line)
            else:
                # Malformed line before first 0 level, ignore or print
                pass
                
    if current_block:
        blocks.append(current_block)
        
    return blocks

def save_gedcom_blocks(blocks, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        for b in blocks:
            f.write(b.serialize() + "\n")
            
if __name__ == '__main__':
    # Test reading
    blocks = parse_gedcom_blocks('sigurjon.ged')
    indis = [b for b in blocks if b.type == 'INDI']
    fams = [b for b in blocks if b.type == 'FAM']
    print(f"Read {len(blocks)} blocks. INDIs: {len(indis)}, FAMs: {len(fams)}")
    # Print first INDI name
    if indis:
        print(f"First INDI: {indis[0].id} - NAME: {indis[0].get_value(['NAME'])}")
