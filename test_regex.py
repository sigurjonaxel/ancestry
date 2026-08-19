import re

text = """0 @I123@ INDI
1 NAME Jón /Jónsson/
1 HUSB @I123@
0 @F17@ FAM
1 FAMS @F17@"""

pattern = re.compile(r'^(\d+)\s+(@\w+@)?\s*(\w+)?\s*(.*)$')
for line in text.split('\n'):
    m = pattern.match(line)
    if m:
        print(f"Line: {line}")
        print(f"1: {m.group(1)}")
        print(f"2: {m.group(2)}")
        print(f"3: {m.group(3)}")
        print(f"4: {m.group(4)}\n")
