import re

with open('loa.ged', 'r') as f:
    lines = f.readlines()

new_lines = []
in_sigtryggur = False
for line in lines:
    if line.startswith('0 @I272771958762@ INDI'):
        in_sigtryggur = True
    elif line.startswith('0 @') and in_sigtryggur:
        # End of Sigtryggur's record, add the NOTE before this line
        note = """1 NOTE Rannsóknarferill:
2 CONT ● Aðferð: Vefleit (Tímarit.is & Morgunblaðið)
2 CONT - Aðgerð: Leitað að minningargreinum til að finna atvik úr lífi hans.
2 CONT - Niðurstaða: Fannst grein um eldsvoða á heimili hans í Rvík (jan 1958). Staðfest að hann bjó áður á Innri-Kleif sem bóndi. Heimildir færðar í gagnagrunn.
"""
        new_lines.extend(note.splitlines(True))
        in_sigtryggur = False
    new_lines.append(line)

# Handle case if he was the last record
if in_sigtryggur:
    note = """1 NOTE Rannsóknarferill:
2 CONT ● Aðferð: Vefleit (Tímarit.is & Morgunblaðið)
2 CONT - Aðgerð: Leitað að minningargreinum til að finna atvik úr lífi hans.
2 CONT - Niðurstaða: Fannst grein um eldsvoða á heimili hans í Rvík (jan 1958). Staðfest að hann bjó áður á Innri-Kleif sem bóndi. Heimildir færðar í gagnagrunn.
"""
    new_lines.extend(note.splitlines(True))

with open('loa.ged', 'w') as f:
    f.writelines(new_lines)
