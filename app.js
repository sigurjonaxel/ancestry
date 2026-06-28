/**
 * Saga — Ættfræðiaðstoð
 * Client-side JavaScript logic for GEDCOM parsing, OCR, and timeline drafting.
 */

// Application State
const state = {
  trees: {},            // Map of treeName -> { people: Map, families: Map }
  selectedTreeId: null, // Currently selected tree key
  selectedPersonId: null,// Currently selected person ID
  ocrImage: null,       // File/Blob of the uploaded image
  toastTimeout: null
};

// Initialize the Application on Load
document.addEventListener('DOMContentLoaded', () => {
  initUIEvents();
  loadSavedNotesCount();
  lucide.createIcons();
});

// ==========================================
// 1. GEDCOM Parser & Relationship Resolver
// ==========================================

/**
 * Parses a raw GEDCOM text string into structured people and families.
 */
function parseGEDCOM(text) {
  const people = new Map();
  const families = new Map();
  
  const lines = text.split(/\r?\n/);
  
  let currentEntity = null; // Can be 'INDI' or 'FAM'
  let currentId = null;
  let activePerson = null;
  let activeFamily = null;
  let dateType = null; // 'BIRT' or 'DEAT' or 'MARR'

  for (let line of lines) {
    line = line.trim();
    if (!line) continue;

    // Match level, tag, and value
    // E.g., "0 @I1@ INDI" or "1 NAME Jón /Jónsson/" or "2 DATE 12 JUN 1920"
    const match = line.match(/^(\d+)\s+(@\w+@)?\s*(\w+)?\s*(.*)$/);
    if (!match) continue;

    const level = parseInt(match[1]);
    const pointer = match[2];
    const tag = match[3];
    const value = match[4];

    if (level === 0) {
      // Start of a new top-level record
      if (value === 'INDI' && pointer) {
        currentEntity = 'INDI';
        currentId = pointer;
        activePerson = {
          id: pointer,
          firstName: '',
          lastName: '',
          fullName: 'Óþekkt nafn',
          birthDate: '',
          birthPlace: '',
          deathDate: '',
          deathPlace: '',
          famc: null, // Family they are child of
          fams: [],   // Families they are spouse of
          fatherId: null,
          motherId: null,
          spouses: [],
          children: []
        };
        people.set(pointer, activePerson);
      } else if (value === 'FAM' && pointer) {
        currentEntity = 'FAM';
        currentId = pointer;
        activeFamily = {
          id: pointer,
          husband: null,
          wife: null,
          children: []
        };
        families.set(pointer, activeFamily);
      } else {
        currentEntity = null;
        currentId = null;
      }
      dateType = null;
    } else {
      // Properties under the current record
      if (currentEntity === 'INDI' && activePerson) {
        if (tag === 'NAME') {
          // Extract name and clean slashes (e.g. Jón /Jónsson/ -> Jón Jónsson)
          let rawName = value;
          let cleanName = rawName.replace(/\//g, '').trim();
          activePerson.fullName = cleanName;
          
          // Try to split into first and last name
          const parts = rawName.split('/');
          activePerson.firstName = parts[0] ? parts[0].trim() : '';
          activePerson.lastName = parts[1] ? parts[1].trim() : '';
        } else if (tag === 'BIRT') {
          dateType = 'BIRT';
        } else if (tag === 'DEAT') {
          dateType = 'DEAT';
        } else if (tag === 'DATE') {
          if (dateType === 'BIRT') activePerson.birthDate = cleanGedcomDate(value);
          if (dateType === 'DEAT') activePerson.deathDate = cleanGedcomDate(value);
        } else if (tag === 'PLAC') {
          if (dateType === 'BIRT') activePerson.birthPlace = value;
          if (dateType === 'DEAT') activePerson.deathPlace = value;
        } else if (tag === 'FAMC') {
          activePerson.famc = value;
        } else if (tag === 'FAMS') {
          activePerson.fams.push(value);
        }
      } else if (currentEntity === 'FAM' && activeFamily) {
        if (tag === 'HUSB') {
          activeFamily.husband = value;
        } else if (tag === 'WIFE') {
          activeFamily.wife = value;
        } else if (tag === 'CHIL') {
          activeFamily.children.push(value);
        }
      }
    }
  }

  // Resolve Relationships: Parents, Spouses, and Children
  for (let [id, person] of people.entries()) {
    // 1. Resolve Parents via FAMC
    if (person.famc) {
      const parentFam = families.get(person.famc);
      if (parentFam) {
        person.fatherId = parentFam.husband || null;
        person.motherId = parentFam.wife || null;
      }
    }

    // 2. Resolve Spouses & Children via FAMS
    person.fams.forEach(famId => {
      const fam = families.get(famId);
      if (fam) {
        // Find spouse
        let spouseId = null;
        if (fam.husband === id) spouseId = fam.wife;
        else if (fam.wife === id) spouseId = fam.husband;
        
        if (spouseId && !person.spouses.includes(spouseId)) {
          person.spouses.push(spouseId);
        }

        // Add children from this family
        fam.children.forEach(childId => {
          if (!person.children.includes(childId)) {
            person.children.push(childId);
          }
        });
      }
    });
  }

  return { people, families };
}

/**
 * Translates English GEDCOM dates into cleaner formats (e.g. 12 JUN 1920 -> 12. júní 1920)
 */
function cleanGedcomDate(gedDate) {
  if (!gedDate) return '';
  
  const months = {
    'JAN': 'janúar', 'FEB': 'febrúar', 'MAR': 'mars', 'APR': 'apríl',
    'MAY': 'maí', 'JUN': 'júní', 'JUL': 'júlí', 'AUG': 'ágúst',
    'SEP': 'september', 'OCT': 'október', 'NOV': 'nóvember', 'DEC': 'desember'
  };

  let clean = gedDate;
  // Match DD MMM YYYY
  const parts = gedDate.split(' ');
  if (parts.length === 3) {
    const day = parts[0];
    const monthEng = parts[1].toUpperCase();
    const year = parts[2];
    if (months[monthEng]) {
      return `${day}. ${months[monthEng]} ${year}`;
    }
  } else if (parts.length === 2) {
    const monthEng = parts[0].toUpperCase();
    const year = parts[1];
    if (months[monthEng]) {
      return `${months[monthEng]} ${year}`;
    }
  }
  
  return clean;
}

// ==========================================
// 2. Mock Data Generator
// ==========================================

function loadMockTrees() {
  const lolaGedcom = `
0 @I1@ INDI
1 NAME Lóa Margrét /Sveinsdóttir/
1 BIRT
2 DATE 14 MAR 1994
2 PLAC Reykjavík, Ísland
1 FAMC @F1@
0 @I2@ INDI
1 NAME Sveinn /Hallgrímsson/
1 BIRT
2 DATE 8 OCT 1962
2 PLAC Akureyri, Ísland
1 FAMS @F1@
1 FAMC @F2@
0 @I3@ INDI
1 NAME Margrét /Jónsdóttir/
1 BIRT
2 DATE 24 DEC 1965
2 PLAC Húsavík, Ísland
1 FAMS @F1@
1 FAMC @F3@
0 @I4@ INDI
1 NAME Hallgrímur /Sveinsson/
1 BIRT
2 DATE 12 APR 1932
2 PLAC Seyðisfjörður, Ísland
1 DEAT
2 DATE 4 SEP 2012
2 PLAC Reykjavík, Ísland
1 FAMS @F2@
0 @I5@ INDI
1 NAME Sigrún /Guðmundsdóttir/
1 BIRT
2 DATE 3 JUL 1935
2 PLAC Eskifjörður, Ísland
1 DEAT
2 DATE 19 FEB 2018
2 PLAC Reykjavík, Ísland
1 FAMS @F2@
0 @I6@ INDI
1 NAME Jón /Einarsson/
1 BIRT
2 DATE 17 JUN 1928
2 PLAC Húsavík, Ísland
1 DEAT
2 DATE 15 MAY 2004
2 PLAC Akureyri, Ísland
1 FAMS @F3@
0 @I7@ INDI
1 NAME Kristín /Pétursdóttir/
1 BIRT
2 DATE 5 NOV 1933
2 PLAC Kópasker, Ísland
1 DEAT
2 DATE 22 AUG 2021
2 PLAC Húsavík, Ísland
1 FAMS @F3@
0 @F1@ FAM
1 HUSB @I2@
1 WIFE @I3@
1 CHIL @I1@
0 @F2@ FAM
1 HUSB @I4@
1 WIFE @I5@
1 CHIL @I2@
0 @F3@ FAM
1 HUSB @I6@
1 WIFE @I7@
1 CHIL @I3@
`;

  const sigurjonGedcom = `
0 @I10@ INDI
1 NAME Sigurjón Axel /Guðjónsson/
1 BIRT
2 DATE 20 JUL 1990
2 PLAC Reykjavík, Ísland
1 FAMC @F10@
0 @I11@ INDI
1 NAME Guðjón /Axelsson/
1 BIRT
2 DATE 3 JUN 1958
2 PLAC Ísafjörður, Ísland
1 FAMS @F10@
1 FAMC @F11@
0 @I12@ INDI
1 NAME Sigurjóna /Sigurðardóttir/
1 BIRT
2 DATE 11 SEP 1961
2 PLAC Vestmannaeyjar, Ísland
1 FAMS @F10@
1 FAMC @F12@
0 @I13@ INDI
1 NAME Axel /Guðjónsson/
1 BIRT
2 DATE 19 AUG 1925
2 PLAC Flateyri, Ísland
1 DEAT
2 DATE 8 APR 2009
2 PLAC Ísafjörður, Ísland
1 FAMS @F11@
0 @I14@ INDI
1 NAME Anna /Halldórsdóttir/
1 BIRT
2 DATE 15 OCT 1928
2 PLAC Bolungarvík, Ísland
1 DEAT
2 DATE 30 NOV 2015
2 PLAC Ísafjörður, Ísland
1 FAMS @F11@
0 @I15@ INDI
1 NAME Sigurður /Bjarnason/
1 BIRT
2 DATE 25 MAY 1930
2 PLAC Vestmannaeyjar, Ísland
1 DEAT
2 DATE 12 JUL 2014
2 PLAC Selfoss, Ísland
1 FAMS @F12@
0 @I16@ INDI
1 NAME Helga /Ólafsdóttir/
1 BIRT
2 DATE 8 JAN 1933
2 PLAC Vestmannaeyjar, Ísland
1 DEAT
2 DATE 4 MAY 2020
2 PLAC Reykjavík, Ísland
1 FAMS @F12@
0 @F10@ FAM
1 HUSB @I11@
1 WIFE @I12@
1 CHIL @I10@
0 @F11@ FAM
1 HUSB @I13@
1 WIFE @I14@
1 CHIL @I11@
0 @F12@ FAM
1 HUSB @I15@
1 WIFE @I16@
1 CHIL @I12@
`;

  state.trees['Lóa — Ættartré'] = parseGEDCOM(lolaGedcom);
  state.trees['Sigurjón Axel — Ættartré'] = parseGEDCOM(sigurjonGedcom);
  
  updateTreeSelector();
  selectTree('Sigurjón Axel — Ættartré');
  showToast('Dæmatré hlaðin inn!');
}

// ==========================================
// 3. UI Interactions & Event Handlers
// ==========================================

function initUIEvents() {
  // Tree Loading
  document.getElementById('btn-load-mock').addEventListener('click', loadMockTrees);
  document.getElementById('btn-load-mock-2').addEventListener('click', loadMockTrees);
  
  const fileInput = document.getElementById('gedcom-file-input');
  fileInput.addEventListener('change', handleGedcomUpload);
  
  const uploadZone = document.getElementById('upload-zone');
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });
  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
  });
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleGedcomUpload();
    }
  });

  // Tree Selector
  const treeSelect = document.getElementById('tree-select');
  treeSelect.addEventListener('change', (e) => {
    selectTree(e.target.value);
  });

  // Search Input
  document.getElementById('search-input').addEventListener('input', handleSearch);

  // Tabs
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
      
      tab.classList.add('active');
      const contentId = tab.getAttribute('data-tab');
      document.getElementById(contentId).style.display = 'block';
    });
  });

  // OCR Upload / Paste
  const ocrDropzone = document.getElementById('ocr-dropzone');
  const ocrFileInput = document.getElementById('ocr-file-input');
  
  ocrFileInput.addEventListener('change', handleOcrImageUpload);
  ocrDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    ocrDropzone.classList.add('dragover');
  });
  ocrDropzone.addEventListener('dragleave', () => {
    ocrDropzone.classList.remove('dragover');
  });
  ocrDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    ocrDropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      ocrFileInput.files = e.dataTransfer.files;
      handleOcrImageUpload();
    }
  });

  // Paste image handler (Ctrl+V)
  window.addEventListener('paste', (e) => {
    // Only handle paste if OCR tab is active or we have a selected person
    if (!state.selectedPersonId) return;
    
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (let item of items) {
      if (item.type.indexOf('image') === 0) {
        const file = item.getAsFile();
        state.ocrImage = file;
        showImagePreview(file);
        
        // Switch to OCR tab
        document.querySelector('[data-tab="tab-ocr"]').click();
        showToast('Mynd límd inn úr klemmuspjaldi!');
        break;
      }
    }
  });

  document.getElementById('btn-clear-image').addEventListener('click', clearImagePreview);
  document.getElementById('btn-run-ocr').addEventListener('click', runOCR);
  document.getElementById('btn-format-to-bio').addEventListener('click', () => {
    // Switch to Bio tab
    document.querySelector('[data-tab="tab-bio"]').click();
    // Copy OCR text over to bio draft area if empty
    const rawText = document.getElementById('ocr-raw-text').value;
    const formattedBio = document.getElementById('formatted-bio-text');
    if (rawText && !formattedBio.value) {
      applyTemplate('bio', rawText);
    }
  });

  // Biography Templates
  document.getElementById('template-bio-btn').addEventListener('click', () => {
    applyTemplate('bio');
  });
  document.getElementById('template-timeline-btn').addEventListener('click', () => {
    applyTemplate('timeline');
  });
  document.getElementById('template-simple-btn').addEventListener('click', () => {
    applyTemplate('simple');
  });

  document.getElementById('btn-copy-bio').addEventListener('click', copyBioToClipboard);
  document.getElementById('btn-save-note').addEventListener('click', saveNoteLocally);
  document.getElementById('btn-extract-events').addEventListener('click', extractEventsFromText);

  // Help Modal
  document.getElementById('btn-show-help').addEventListener('click', () => {
    document.getElementById('help-modal').style.display = 'flex';
  });
  document.getElementById('btn-close-help').addEventListener('click', () => {
    document.getElementById('help-modal').style.display = 'none';
  });

  // Click clickable relations (parents)
  document.getElementById('p-father-info').addEventListener('click', handleRelationClick);
  document.getElementById('p-mother-info').addEventListener('click', handleRelationClick);
}

function showToast(message) {
  const toast = document.getElementById('toast');
  document.getElementById('toast-message').textContent = message;
  toast.classList.add('show');
  
  if (state.toastTimeout) clearTimeout(state.toastTimeout);
  state.toastTimeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// ==========================================
// 4. File Upload & Tree Selection
// ==========================================

function handleGedcomUpload() {
  const fileInput = document.getElementById('gedcom-file-input');
  if (fileInput.files.length === 0) return;

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = function(e) {
    const text = e.target.result;
    try {
      const parsedTree = parseGEDCOM(text);
      const treeName = file.name;
      state.trees[treeName] = parsedTree;
      
      updateTreeSelector();
      selectTree(treeName);
      showToast(`Ættartré „${treeName}“ hlaðið inn!`);
    } catch (err) {
      console.error(err);
      alert('Ekki tókst að lesa GEDCOM skrána. Gakktu úr skugga um að hún sé á réttu sniði.');
    }
  };

  reader.readAsText(file);
}

function updateTreeSelector() {
  const select = document.getElementById('tree-select');
  select.innerHTML = '';
  
  const treeNames = Object.keys(state.trees);
  if (treeNames.length > 0) {
    select.style.display = 'block';
    document.getElementById('upload-zone').style.padding = '0.75rem 0.5rem';
    
    treeNames.forEach(name => {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    });
  } else {
    select.style.display = 'none';
  }
}

function selectTree(treeId) {
  state.selectedTreeId = treeId;
  const select = document.getElementById('tree-select');
  select.value = treeId;

  const tree = state.trees[treeId];
  
  // Show total stats
  document.getElementById('tree-stats').textContent = `${tree.people.size} færslur`;

  // Render People List
  renderPeopleList();

  // Reset workspace
  state.selectedPersonId = null;
  document.getElementById('empty-state-view').style.display = 'flex';
  document.getElementById('person-workspace-view').style.display = 'none';
}

function renderPeopleList(filteredPeople = null) {
  const container = document.getElementById('people-list-container');
  container.innerHTML = '';

  const tree = state.trees[state.selectedTreeId];
  if (!tree) return;

  const peopleToRender = filteredPeople || Array.from(tree.people.values());

  if (peopleToRender.length === 0) {
    container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.9rem;">Ekkert fólk fannst</div>`;
    return;
  }

  // Sort people alphabetically
  peopleToRender.sort((a, b) => a.fullName.localeCompare(b.fullName, 'is'));

  peopleToRender.forEach(person => {
    const item = document.createElement('div');
    item.className = 'person-item';
    if (state.selectedPersonId === person.id) {
      item.classList.add('active');
    }
    
    const nameSpan = document.createElement('span');
    nameSpan.className = 'person-name';
    nameSpan.textContent = person.fullName;
    
    const datesSpan = document.createElement('span');
    datesSpan.className = 'person-dates';
    
    const bYear = person.birthDate ? person.birthDate.split(' ').pop() : '?';
    const dYear = person.deathDate ? person.deathDate.split(' ').pop() : (person.deathDate === '' ? 'lifir' : '?');
    datesSpan.textContent = `${bYear} – ${dYear}`;

    item.appendChild(nameSpan);
    item.appendChild(datesSpan);
    
    item.addEventListener('click', () => {
      selectPerson(person.id);
    });

    container.appendChild(item);
  });
}

function handleSearch(e) {
  const query = e.target.value.toLowerCase().trim();
  const tree = state.trees[state.selectedTreeId];
  if (!tree) return;

  if (!query) {
    renderPeopleList();
    return;
  }

  const matches = [];
  for (let person of tree.people.values()) {
    const nameMatch = person.fullName.toLowerCase().includes(query);
    const dateMatch = (person.birthDate && person.birthDate.includes(query)) || 
                      (person.deathDate && person.deathDate.includes(query));
    if (nameMatch || dateMatch) {
      matches.push(person);
    }
  }

  renderPeopleList(matches);
}

// ==========================================
// 5. Person Workspace & Details
// ==========================================

function selectPerson(personId) {
  state.selectedPersonId = personId;
  const tree = state.trees[state.selectedTreeId];
  if (!tree) return;

  const person = tree.people.get(personId);
  if (!person) return;

  // Highlight in list
  document.querySelectorAll('.person-item').forEach(item => {
    const name = item.querySelector('.person-name').textContent;
    if (name === person.fullName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Show Workspace View
  document.getElementById('empty-state-view').style.display = 'none';
  document.getElementById('person-workspace-view').style.display = 'grid';

  // Fill Details
  document.getElementById('p-full-name').textContent = person.fullName;
  
  const bYear = person.birthDate ? person.birthDate.split(' ').pop() : '?';
  const dYear = person.deathDate ? person.deathDate.split(' ').pop() : '';
  document.getElementById('p-life-dates').textContent = dYear ? `${bYear} – ${dYear}` : `f. ${person.birthDate || '?'}`;

  document.getElementById('p-birth-info').textContent = 
    (person.birthDate || '-') + (person.birthPlace ? ` (${person.birthPlace})` : '');
  
  document.getElementById('p-death-info').textContent = 
    (person.deathDate || '-') + (person.deathPlace ? ` (${person.deathPlace})` : '');

  // Parents
  const fatherEl = document.getElementById('p-father-info');
  if (person.fatherId && tree.people.has(person.fatherId)) {
    const father = tree.people.get(person.fatherId);
    fatherEl.textContent = father.fullName;
    fatherEl.dataset.id = person.fatherId;
    fatherEl.classList.add('clickable');
  } else {
    fatherEl.textContent = '-';
    fatherEl.dataset.id = '';
    fatherEl.classList.remove('clickable');
  }

  const motherEl = document.getElementById('p-mother-info');
  if (person.motherId && tree.people.has(person.motherId)) {
    const mother = tree.people.get(person.motherId);
    motherEl.textContent = mother.fullName;
    motherEl.dataset.id = person.motherId;
    motherEl.classList.add('clickable');
  } else {
    motherEl.textContent = '-';
    motherEl.dataset.id = '';
    motherEl.classList.remove('clickable');
  }

  // Spouses
  const spouseEl = document.getElementById('p-spouse-info');
  if (person.spouses.length > 0) {
    spouseEl.innerHTML = person.spouses.map(spouseId => {
      const spouse = tree.people.get(spouseId);
      return spouse ? `<span class="clickable" onclick="window.selectPersonFromExternal('${spouseId}')">${spouse.fullName}</span>` : '';
    }).join(', ');
  } else {
    spouseEl.textContent = '-';
  }

  // Children
  const childrenContainer = document.getElementById('p-children-list');
  childrenContainer.innerHTML = '';
  if (person.children.length > 0) {
    person.children.forEach(childId => {
      const child = tree.people.get(childId);
      if (child) {
        const item = document.createElement('span');
        item.className = 'relation-value clickable';
        item.textContent = child.fullName;
        item.addEventListener('click', () => {
          selectPerson(childId);
        });
        childrenContainer.appendChild(item);
      }
    });
  } else {
    childrenContainer.innerHTML = '<span class="relation-value">-</span>';
  }

  // Setup Search Links
  setupSearchLinks(person);

  // Clear workspace inputs for new person (or load cached data)
  clearWorkspaceInputsForNewPerson();
  loadSavedNotes();
  
  // Return to Tab 1 (OCR) as default for research
  document.querySelector('[data-tab="tab-ocr"]').click();
}

window.selectPersonFromExternal = function(id) {
  selectPerson(id);
};

function handleRelationClick(e) {
  const id = e.target.dataset.id;
  if (id) {
    selectPerson(id);
  }
}

function setupSearchLinks(person) {
  const fullNameEncoded = encodeURIComponent(person.fullName);
  // Extract clean name without middle names if searching is too narrow
  const firstAndLast = encodeURIComponent(person.firstName + ' ' + person.lastName);
  
  const birthYear = person.birthDate ? person.birthDate.split(' ').pop() : '';
  const deathYear = person.deathDate ? person.deathDate.split(' ').pop() : '';

  // 1. Tímarit.is
  // We query exact name + birth/death range if available
  let timaritQuery = `"${person.fullName}"`;
  if (birthYear) timaritQuery += ` OR "${person.firstName} ${person.lastName}" ${birthYear}`;
  document.getElementById('link-timarit').href = `https://timarit.is/search?q=${encodeURIComponent(timaritQuery)}`;

  // 2. Mbl.is Minningar
  let mblQuery = `${person.fullName}`;
  document.getElementById('link-mbl').href = `https://www.mbl.is/greinasafn/leit/?q=${encodeURIComponent(mblQuery)}`;

  // 3. Legstaðaleit
  let legQuery = `${person.firstName} ${person.lastName}`;
  document.getElementById('link-legstadir').href = `https://www.legstadaleit.is/leit?q=${encodeURIComponent(legQuery)}`;

  // 4. Íslendingabók
  document.getElementById('link-islendingabok').href = `https://www.islendingabok.is`;
}

function clearWorkspaceInputsForNewPerson() {
  clearImagePreview();
  document.getElementById('ocr-raw-text').value = '';
  document.getElementById('formatted-bio-text').value = '';
  document.getElementById('dynamic-timeline').innerHTML = `
    <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">
      Smelltu á „Greina atburði úr texta“ til að finna sjálfkrafa ártöl og viðburði í textanum.
    </div>
  `;
}

// ==========================================
// 6. OCR (Optical Character Recognition)
// ==========================================

function handleOcrImageUpload() {
  const ocrFileInput = document.getElementById('ocr-file-input');
  if (ocrFileInput.files.length === 0) return;

  const file = ocrFileInput.files[0];
  state.ocrImage = file;
  showImagePreview(file);
}

function showImagePreview(file) {
  const previewContainer = document.getElementById('ocr-preview-container');
  const previewImage = document.getElementById('ocr-image-preview');
  const dropzone = document.getElementById('ocr-dropzone');
  
  const reader = new FileReader();
  reader.onload = function(e) {
    previewImage.src = e.target.result;
    previewContainer.style.display = 'flex';
    dropzone.style.display = 'none';
    document.getElementById('btn-run-ocr').disabled = false;
  };
  reader.readAsDataURL(file);
}

function clearImagePreview() {
  state.ocrImage = null;
  document.getElementById('ocr-file-input').value = '';
  document.getElementById('ocr-preview-container').style.display = 'none';
  document.getElementById('ocr-dropzone').style.display = 'flex';
  document.getElementById('btn-run-ocr').disabled = true;
  document.getElementById('ocr-status').innerHTML = '';
}

function runOCR() {
  if (!state.ocrImage) return;

  const statusEl = document.getElementById('ocr-status');
  statusEl.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; display: inline-block;"></span> Les texta...`;
  
  const rawTextarea = document.getElementById('ocr-raw-text');
  
  // Use Tesseract.js to read Icelandic text
  Tesseract.recognize(
    state.ocrImage,
    'isl', // Icelandic
    {
      logger: m => {
        if (m.status === 'recognizing text') {
          statusEl.innerHTML = `<span class="spinner" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle;"></span> Les: ${Math.round(m.progress * 100)}%`;
        } else {
          statusEl.textContent = 'Hleður málskrá...';
        }
      }
    }
  ).then(({ data: { text } }) => {
    statusEl.innerHTML = `<span style="color: var(--status-success);"><i data-lucide="check" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle;"></i> Lokið</span>`;
    lucide.createIcons();
    
    // Clean up OCR spacing issues common in Icelandic scanned text
    let cleanText = cleanOcrIcelandicText(text);
    rawTextarea.value = cleanText;
    showToast('Textalestri lokið!');
  }).catch(err => {
    console.error(err);
    statusEl.innerHTML = `<span style="color: red;">Villa við lestur</span>`;
    alert('Villa kom upp við að lesa myndina. Gakktu úr skugga um að nettenging sé virk.');
  });
}

/**
 * Standard OCR cleanups for Icelandic:
 * - Fixes common letter substitutions (e.g. '|' for 'I', 'ð' or 'o' mixups)
 * - Fixes word break hyphens at the end of lines
 */
function cleanOcrIcelandicText(text) {
  let clean = text;
  
  // 1. Join hyphenated words split across line breaks
  // E.g., "minning- \nargrein" -> "minningargrein"
  clean = clean.replace(/(\w+)-\s*\r?\n\s*(\w+)/g, '$1$2');
  
  // 2. Remove multiple blank lines
  clean = clean.replace(/\n\s*\n/g, '\n\n');
  
  // 3. Fix typical OCR scanning errors for Icelandic letters
  // (Tesseract 5 does well, but standard corrections help)
  clean = clean.replace(/\bI\b/g, 'í'); // Single capital I in mid-sentence is often í
  
  return clean.trim();
}

// ==========================================
// 7. Timeline & Event Extraction
// ==========================================

function extractEventsFromText() {
  const text = document.getElementById('ocr-raw-text').value;
  if (!text) {
    alert('Sláðu inn eða lestu inn texta fyrst.');
    return;
  }

  const timelineContainer = document.getElementById('dynamic-timeline');
  timelineContainer.innerHTML = '';

  const tree = state.trees[state.selectedTreeId];
  const person = tree.people.get(state.selectedPersonId);

  // Match years (e.g. 1945, 1899, 2012)
  const yearRegex = /\b(18\d{2}|19\d{2}|20\d{2})\b/g;
  const sentences = text.split(/[.!?]\s+/);
  const events = [];

  sentences.forEach(sentence => {
    const yearsInSentence = sentence.match(yearRegex);
    if (yearsInSentence) {
      yearsInSentence.forEach(year => {
        // Avoid duplicate events for same sentence
        if (!events.some(e => e.sentence === sentence.trim())) {
          events.push({
            year: parseInt(year),
            sentence: sentence.trim()
          });
        }
      });
    }
  });

  // Sort events chronologically
  events.sort((a, b) => a.year - b.year);

  if (events.length === 0) {
    timelineContainer.innerHTML = `
      <div style="font-size: 0.85rem; color: var(--text-muted); font-style: italic;">
        Engin ártöl (1800-2099) fundust í textanum.
      </div>
    `;
    return;
  }

  events.forEach(event => {
    const item = document.createElement('div');
    item.className = 'timeline-event';
    
    const yearSpan = document.createElement('div');
    yearSpan.className = 'timeline-event-year';
    yearSpan.textContent = event.year;

    const descSpan = document.createElement('div');
    descSpan.className = 'timeline-event-desc';
    descSpan.textContent = event.sentence;

    item.appendChild(yearSpan);
    item.appendChild(descSpan);
    
    // Add click to edit/include event
    item.style.cursor = 'pointer';
    item.title = 'Smelltu til að bæta við ævisögu';
    item.addEventListener('click', () => {
      const bioTextarea = document.getElementById('formatted-bio-text');
      const prefix = bioTextarea.value ? bioTextarea.value + '\n' : '';
      bioTextarea.value = prefix + `* **${event.year}**: ${event.sentence}`;
      showToast(`Ártali ${event.year} bætt við ævisögu!`);
    });

    timelineContainer.appendChild(item);
  });

  showToast(`Fann ${events.length} ártöl í textanum!`);
}

// ==========================================
// 8. Biography Templating & Clipboard
// ==========================================

function applyTemplate(type, customText = '') {
  const tree = state.trees[state.selectedTreeId];
  const person = tree.people.get(state.selectedPersonId);
  if (!person) return;

  const rawText = customText || document.getElementById('ocr-raw-text').value;
  const formattedBio = document.getElementById('formatted-bio-text');

  let text = '';
  const father = person.fatherId ? tree.people.get(person.fatherId) : null;
  const mother = person.motherId ? tree.people.get(person.motherId) : null;

  if (type === 'bio') {
    text = `## Ævisaga: ${person.fullName}\n\n`;
    text += `${person.fullName} fæddist ${person.birthDate ? 'þann ' + person.birthDate : 'á óþekktum tíma'}`;
    if (person.birthPlace) text += ` á ${person.birthPlace}`;
    text += `.\n`;
    
    if (father || mother) {
      text += `Foreldrar hennar/hans voru `;
      if (father && mother) text += `${father.fullName} og ${mother.fullName}.`;
      else if (father) text += `${father.fullName}.`;
      else if (mother) text += `${mother.fullName}.`;
      text += `\n`;
    }
    
    if (person.deathDate) {
      text += `Lést ${person.deathDate ? 'þann ' + person.deathDate : ''}`;
      if (person.deathPlace) text += ` í/á ${person.deathPlace}`;
      text += `.\n`;
    }

    if (rawText) {
      text += `\n### Minningargrein (Útdráttur):\n> ${rawText.substring(0, 500)}...\n\n`;
    }

    text += `### Tímatal og viðburðir\n`;
    if (person.birthDate) text += `* **${person.birthDate.split(' ').pop()}**: Fæðing\n`;
    if (person.deathDate) text += `* **${person.deathDate.split(' ').pop()}**: Andlát\n`;
  } 
  
  else if (type === 'timeline') {
    text = `### Tímatal: ${person.fullName}\n\n`;
    if (person.birthDate) text += `* **${person.birthDate.split(' ').pop()}**: Fæddist ${person.birthDate} ${person.birthPlace ? 'á ' + person.birthPlace : ''}\n`;
    if (person.deathDate) text += `* **${person.deathDate.split(' ').pop()}**: Lést ${person.deathDate} ${person.deathPlace ? 'í ' + person.deathPlace : ''}\n`;
    
    // Append any timeline items from text
    const timelineEvents = document.querySelectorAll('.timeline-event');
    if (timelineEvents.length > 0) {
      timelineEvents.forEach(el => {
        const yr = el.querySelector('.timeline-event-year').textContent;
        const desc = el.querySelector('.timeline-event-desc').textContent;
        text += `* **${yr}**: ${desc}\n`;
      });
    }
  } 
  
  else if (type === 'simple') {
    text = `${person.fullName} (${person.birthDate ? person.birthDate.split(' ').pop() : '?'} – ${person.deathDate ? person.deathDate.split(' ').pop() : '?'})\n\n`;
    if (rawText) {
      text += rawText;
    } else {
      text += `Fædd/ur ${person.birthDate ? 'þann ' + person.birthDate : ''}. Lést ${person.deathDate ? 'þann ' + person.deathDate : ''}.`;
    }
  }

  formattedBio.value = text;
  showToast('Sniðmát virkjað!');
}

function copyBioToClipboard() {
  const bioText = document.getElementById('formatted-bio-text').value;
  if (!bioText) {
    alert('Ekkert efni er í lokautgáfu til að afrita.');
    return;
  }

  navigator.clipboard.writeText(bioText).then(() => {
    showToast('Texti afritaður í klemmuspjald!');
  }).catch(err => {
    console.error('Ekki tókst að afrita texta', err);
    alert('Ekki tókst að afrita texta sjálfkrafa. Vinsamlegast veldu textann og afritaðu með Ctrl+C.');
  });
}

// ==========================================
// 9. Local Storage & Backups
// ==========================================

function loadSavedNotesCount() {
  const countSpan = document.getElementById('saved-notes-count');
  let count = 0;
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.startsWith('saga_note_')) {
      count++;
    }
  }
  countSpan.textContent = count;
}

function saveNoteLocally() {
  const bioText = document.getElementById('formatted-bio-text').value;
  if (!bioText) {
    alert('Sláðu inn texta til að vista.');
    return;
  }

  const tree = state.trees[state.selectedTreeId];
  const person = tree.people.get(state.selectedPersonId);
  if (!person) return;

  const noteKey = `saga_note_${state.selectedTreeId}_${person.id}_${Date.now()}`;
  const noteData = {
    treeName: state.selectedTreeId,
    personId: person.id,
    personName: person.fullName,
    text: bioText,
    timestamp: new Date().toISOString()
  };

  localStorage.setItem(noteKey, JSON.stringify(noteData));
  showToast('Minning vistuð staðbundið í Saga!');
  loadSavedNotesCount();
  loadSavedNotes();
}

function loadSavedNotes() {
  const container = document.getElementById('saved-notes-list');
  container.innerHTML = '';

  const personId = state.selectedPersonId;
  const treeId = state.selectedTreeId;
  const notes = [];

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.startsWith(`saga_note_${treeId}_${personId}_`)) {
      const data = JSON.parse(localStorage.getItem(key));
      notes.push({ key, ...data });
    }
  }

  // Sort notes newest first
  notes.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  if (notes.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.9rem;">
        Engin vistuð gögn fyrir þessa persónu enn sem komið er.
      </div>
    `;
    return;
  }

  notes.forEach(note => {
    const item = document.createElement('div');
    item.className = 'card';
    item.style.padding = '1rem';
    item.style.marginBottom = '0.5rem';
    item.style.background = 'rgba(13, 15, 18, 0.4)';
    
    const dateStr = new Date(note.timestamp).toLocaleDateString('is', {
      year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    const meta = document.createElement('div');
    meta.style.display = 'flex';
    meta.style.justify = 'space-between';
    meta.style.fontSize = '0.75rem';
    meta.style.color = 'var(--text-muted)';
    meta.style.marginBottom = '0.5rem';
    meta.innerHTML = `<span>Vistun: ${dateStr}</span>`;

    const content = document.createElement('pre');
    content.style.whiteSpace = 'pre-wrap';
    content.style.fontSize = '0.85rem';
    content.style.color = 'var(--text-primary)';
    content.style.maxHeight = '150px';
    content.style.overflowY = 'auto';
    content.style.padding = '0.5rem';
    content.style.background = 'rgba(0,0,0,0.2)';
    content.style.borderRadius = '4px';
    content.textContent = note.text;

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '1rem';
    actions.style.marginTop = '0.5rem';
    
    const loadBtn = document.createElement('button');
    loadBtn.className = 'btn btn-secondary';
    loadBtn.style.padding = '0.3rem 0.6rem';
    loadBtn.style.fontSize = '0.75rem';
    loadBtn.textContent = 'Hlaða inn';
    loadBtn.addEventListener('click', () => {
      document.getElementById('formatted-bio-text').value = note.text;
      document.querySelector('[data-tab="tab-bio"]').click();
      showToast('Minning hlaðin inn í ritil!');
    });

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-secondary';
    deleteBtn.style.padding = '0.3rem 0.6rem';
    deleteBtn.style.fontSize = '0.75rem';
    deleteBtn.style.color = '#ff6b6b';
    deleteBtn.textContent = 'Eyða';
    deleteBtn.addEventListener('click', () => {
      if (confirm('Ertu viss um að þú viljir eyða þessari vistun?')) {
        localStorage.removeItem(note.key);
        loadSavedNotesCount();
        loadSavedNotes();
        showToast('Vistun eytt!');
      }
    });

    actions.appendChild(loadBtn);
    actions.appendChild(deleteBtn);

    item.appendChild(meta);
    item.appendChild(content);
    item.appendChild(actions);

    container.appendChild(item);
  });
}
