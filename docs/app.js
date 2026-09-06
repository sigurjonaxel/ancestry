// Saga Ancestry Web App - Modernized & Simplified UI Engine
// Driven by SQLite Backend API (/api/person, /api/tree, /api/run_scraper)

const state = {
  selectedTreeId: 'sigurjon',
  selectedPersonId: 'I212097023483',
  people: [],
  personDetails: null,
  showRejected: false
};

function updateDebugBar(msg) {
  let bar = document.getElementById('debug-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'debug-bar';
    bar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#1a1a2e;color:#0f0;font-family:monospace;font-size:12px;padding:6px 12px;z-index:99999;border-top:1px solid #0f0;';
    document.body.appendChild(bar);
  }
  bar.textContent = msg;
}

async function fetchWithTimeout(url, timeoutMs = 10000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(id);
    return res;
  } catch (e) {
    clearTimeout(id);
    throw e;
  }
}

async function initApp() {
  updateDebugBar('⏳ Hleð inn gögnum...');
  initEventListeners();
  try {
    await loadTreesList();
  } catch(e) {
    console.error('loadTreesList failed:', e);
  }
  try {
    await loadTree(state.selectedTreeId);
  } catch(e) {
    console.error('loadTree failed:', e);
    updateDebugBar('⚠️ Gat ekki hlaðið tré sjálfkrafa, reyndu að velja tré úr listanum');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

function toggleMobileSidebar(forceState) {
  const sidebar = document.getElementById('app-sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (!sidebar) return;
  const isOpen = forceState !== undefined ? forceState : !sidebar.classList.contains('mobile-open');
  if (isOpen) {
    sidebar.classList.add('mobile-open');
    if (backdrop) backdrop.classList.add('active');
  } else {
    sidebar.classList.remove('mobile-open');
    if (backdrop) backdrop.classList.remove('active');
  }
}
window.toggleMobileSidebar = toggleMobileSidebar;

function initEventListeners() {
  const menuToggle = document.getElementById('mobile-menu-toggle');
  if (menuToggle) {
    menuToggle.addEventListener('click', () => toggleMobileSidebar());
  }

  const treeSelect = document.getElementById('tree-select');
  if (treeSelect) {
    const treeChangeListener = (e) => {
      state.selectedTreeId = e.target.value;
      loadTree(state.selectedTreeId);
    };
    treeSelect._treeChangeListener = treeChangeListener;
    treeSelect.addEventListener('change', treeChangeListener);
  }

  const fileInput = document.getElementById('gedcom-file-input');
  if (fileInput) {
    fileInput.addEventListener('change', handleGedcomFileUpload);
  }

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      filterPeopleList(e.target.value);
    });
  }

  const btnLoadLocal = document.getElementById('btn-load-local');
  if (btnLoadLocal) btnLoadLocal.addEventListener('click', () => loadTree('loa'));
  
  const btnLoadLocal2 = document.getElementById('btn-load-local-2');
  if (btnLoadLocal2) btnLoadLocal2.addEventListener('click', () => loadTree('loa'));

  const btnSettings = document.getElementById('btn-show-settings');
  if (btnSettings) btnSettings.addEventListener('click', openSettingsModal);
  
  const btnCloseSettings = document.getElementById('btn-close-settings');
  if (btnCloseSettings) btnCloseSettings.addEventListener('click', closeSettingsModal);
  
  const btnSaveSettings = document.getElementById('btn-save-settings');
  if (btnSaveSettings) btnSaveSettings.addEventListener('click', saveSettings);

  // Tab switching in workspace
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const targetTab = tab.getAttribute('data-tab');
      document.querySelectorAll('.tab-content').forEach(c => {
        c.style.display = c.id === targetTab ? 'block' : 'none';
      });
    });
  });

  // Copy Bio Text button
  const btnCopyBio = document.getElementById('btn-copy-bio');
  if (btnCopyBio) {
    btnCopyBio.addEventListener('click', () => {
      const txt = document.getElementById('formatted-bio-text');
      if (txt && txt.value) {
        navigator.clipboard.writeText(txt.value);
        showToast('Ævisaga afrituð á klippiborð!');
      }
    });
  }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toast-message');
  if (!toast || !toastMsg) return;
  toastMsg.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3500);
}

async function loadTreesList() {
  try {
    const res = await fetchWithTimeout('/api/trees');
    if (res.ok) {
      const trees = await res.json();
      const select = document.getElementById('tree-select');
      if (select && trees.length > 0) {
        // Temporarily remove the change listener so innerHTML update doesn't trigger loadTree again
        const oldListener = select._treeChangeListener;
        if (oldListener) select.removeEventListener('change', oldListener);

        select.innerHTML = trees.map(t => `<option value="${t.id}" ${t.id === state.selectedTreeId ? 'selected' : ''}>🌳 ${t.name}</option>`).join('');
        select.style.display = 'block';
        select.value = state.selectedTreeId;

        // Re-add the listener
        if (oldListener) select.addEventListener('change', oldListener);
      }
    }
  } catch (err) {
    console.error("Could not load trees list:", err);
  }
}

async function loadTree(treeId, targetPersonId = null) {
  try {
    // Show Workspace, Hide Empty State immediately
    const emptyView = document.getElementById('empty-state-view');
    const workspaceView = document.getElementById('person-workspace-view');
    if (emptyView) emptyView.style.display = 'none';
    if (workspaceView) workspaceView.style.display = 'grid';

    state.selectedTreeId = treeId;
    const select = document.getElementById('tree-select');
    if (select) select.value = treeId;

    const res = await fetchWithTimeout(`/api/tree?id=${treeId}`);
    if (!res.ok) throw new Error("Gat ekki sótt ættartré.");
    const data = await res.json();
    state.people = data.people || [];
    
    const stats = document.getElementById('tree-stats');
    if (stats) stats.textContent = `${state.people.length} færslur`;
    
    updateDebugBar(`✅ Tré hlaðið: ${state.people.length} einstaklingar í "${treeId}" — sláðu inn í leitarboxið`);
    
    // Check if user already typed in search input
    const searchInput = document.getElementById('search-input');
    if (searchInput && searchInput.value.trim()) {
      filterPeopleList(searchInput.value);
    } else {
      renderPeopleList(state.people);
    }
    
    // If targetPersonId is given, select that specific person
    if (targetPersonId) {
      selectPerson(targetPersonId);
    } else if (state.people.length > 0) {
      // Default: In loa tree default to Lóa, in sigurjon tree default to Sigurjón
      let defaultP;
      if (treeId === 'loa') {
        defaultP = state.people.find(p => p.id === 'I272771958737' || (p.name && p.name.includes('Ólafía'))) || state.people[0];
      } else {
        defaultP = state.people.find(p => p.id === 'I212097023483' || (p.name && p.name.includes('Sigurjón Axel'))) || state.people[0];
      }
      selectPerson(defaultP.id);
    }
  } catch (err) {
    console.error("Error loading tree:", err);
    showToast("Villa við að hlaða inn ættartré.");
  }
}

async function handleGedcomFileUpload() {
  const fileInput = document.getElementById('gedcom-file-input');
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;

  const file = fileInput.files[0];
  showToast(`Hlað inn ${file.name}...`);

  const formData = new FormData();
  formData.append('gedcom', file);

  try {
    const res = await fetch('/api/upload_gedcom', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error("Gat ekki hlaðið inn GEDCOM skrá.");
    const data = await res.json();
    showToast(data.message || "Ættartré flutt inn!");
    await loadTreesList();
    await loadTree(data.tree_id);
  } catch (err) {
    console.error("Error uploading GEDCOM:", err);
    showToast("Villa við innlestur GEDCOM skráar: " + err.message);
  }
}

function normalizeText(str) {
  if (str === null || str === undefined) return '';
  return String(str).toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/ð/g, 'd')
    .replace(/þ/g, 'th')
    .replace(/æ/g, 'ae')
    .replace(/ö/g, 'o');
}

function renderPeopleList(people) {
  const container = document.getElementById('people-list-container');
  if (!container) return;
  
  if (!people || people.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Engir einstaklingar fundust.</div>`;
    return;
  }
  
  container.innerHTML = people.map(p => {
    if (!p) return '';
    const displayName = p.name || 'Óþekkt nafn';
    const dates = [p.birth_year, p.death_year].filter(Boolean).join(' – ');
    const isSelected = state.selectedPersonId === p.id;
    return `
      <div class="person-item ${isSelected ? 'active' : ''}" onclick="selectPerson('${p.id}')">
        <div class="person-avatar-small">
          ${p.avatar_url ? `<img src="${p.avatar_url.startsWith('images/') ? './' + p.avatar_url : p.avatar_url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">` : '<i data-lucide="user"></i>'}
        </div>
        <div class="person-info">
          <div class="person-name">${displayName}</div>
          <div class="person-meta">${dates ? dates : 'Óþekkt ártöl'}</div>
        </div>
      </div>
    `;
  }).join('');
  
  try { if (window.lucide) lucide.createIcons(); } catch(e) {}
}

function filterPeopleList(query) {
  try {
    if (!query || !query.trim()) {
      renderPeopleList(state.people);
      return;
    }
    const queryTokens = normalizeText(query).split(/\s+/).filter(Boolean);
    
    const filtered = (state.people || []).filter(p => {
      if (!p) return false;
      const searchableFields = [
        p.name,
        p.given_names,
        p.surname,
        p.birth_date,
        p.birth_year,
        p.death_date,
        p.death_year,
        p.id
      ].filter(Boolean).map(normalizeText).join(' ');
      
      return queryTokens.every(token => searchableFields.includes(token));
    });
    renderPeopleList(filtered);
    updateDebugBar(`🔍 Leit: "${query}" → ${filtered.length} niðurstöður úr ${(state.people||[]).length} einstaklingum`);
  } catch (err) {
    console.error("Filter error:", err);
  }
}

async function selectPerson(personId) {
  // Snjallt trjáhopp (Cross-Tree Navigation):
  // Ef smellt er á Lóu í Sigurjóns tré -> Hoppum sjálfkrafa yfir í Lóu tré (þar sem öll hennar börn og foreldrar eru)!
  if (personId === 'I_ADD_LOA_I212097023483' && state.selectedTreeId !== 'loa') {
    state.selectedTreeId = 'loa';
    const treeSelect = document.getElementById('tree-select');
    if (treeSelect) treeSelect.value = 'loa';
    showToast("🌳 Skipti yfir í Lóu ættartré...");
    await loadTree('loa', 'I272771958737');
    return;
  }

  // Ef smellt er á Sigurjón í Lóu tré -> Hoppum sjálfkrafa yfir í Sigurjóns tré (þar sem öll hans börn og foreldrar eru)!
  if (personId === 'I_ADD_100' && state.selectedTreeId !== 'sigurjon') {
    state.selectedTreeId = 'sigurjon';
    const treeSelect = document.getElementById('tree-select');
    if (treeSelect) treeSelect.value = 'sigurjon';
    showToast("🌳 Skipti yfir í Sigurjóns ættartré...");
    await loadTree('sigurjon', 'I212097023483');
    return;
  }

  state.selectedPersonId = personId;
  
  // Close mobile sidebar drawer if open
  if (window.innerWidth <= 900) {
    toggleMobileSidebar(false);
  }

  // Highlight active item in sidebar list without blowing away search filter!
  const container = document.getElementById('people-list-container');
  if (container) {
    const items = container.querySelectorAll('.person-item');
    items.forEach(item => {
      const onclickAttr = item.getAttribute('onclick') || '';
      if (onclickAttr.includes(`'${personId}'`)) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }
  
  const emptyView = document.getElementById('empty-state-view');
  const workspaceView = document.getElementById('person-workspace-view');
  if (emptyView) emptyView.style.display = 'none';
  if (workspaceView) workspaceView.style.display = 'grid';
  
  try {
    const res = await fetch(`/api/person?id=${personId}`);
    if (!res.ok) throw new Error("Gat ekki sótt persónu.");
    const details = await res.json();
    state.personDetails = details;
    state.selectedPerson = details.person || null;
    state.selectedPersonId = personId;
    renderPersonProfile(details);
  } catch (err) {
    console.error("Error fetching person profile:", err);
    showToast("Villa við að hlaða persónu.");
  }
}

function renderPersonProfile(details) {
  const p = details.person || {};
  const sources = details.sources || [];
  const suggestions = details.suggestions || [];
  const family = details.family || { father: null, mother: null, spouse: [], children: [], siblings: [] };
  
  // Header Info
  const nameEl = document.getElementById('p-full-name');
  if (nameEl) nameEl.textContent = p.name || 'Óþekkt nafn';
  
  const datesEl = document.getElementById('p-life-dates');
  if (datesEl) {
    datesEl.textContent = [
      p.birth_date || p.birth_year ? `f. ${p.birth_date || p.birth_year}` : '',
      p.death_date || p.death_year ? `d. ${p.death_date || p.death_year}` : ''
    ].filter(Boolean).join(' — ');
  }

  // Profile Confidence & Identity Verification Badge
  const confBadge = document.getElementById('p-confidence-badge');
  if (confBadge) {
    const verifiedSourcesCount = sources.length;
    const hasNotes = !!(p.notes && p.notes.length > 50);
    
    if (verifiedSourcesCount >= 2 || (hasNotes && verifiedSourcesCount >= 1)) {
      confBadge.className = 'badge badge-success';
      confBadge.innerHTML = `<i data-lucide="shield-check" style="width:12px;height:12px;"></i> <span>Hátt áreiðanleikastig (${verifiedSourcesCount} staðfestar heimildir)</span>`;
    } else if (hasNotes || (family.father || family.mother || (family.spouse && family.spouse.length > 0))) {
      confBadge.className = 'badge badge-warning';
      confBadge.innerHTML = `<i data-lucide="check-circle" style="width:12px;height:12px;"></i> <span>Staðfest ættartré (${verifiedSourcesCount} vefheimildir)</span>`;
    } else {
      confBadge.className = 'badge badge-secondary';
      confBadge.innerHTML = `<i data-lucide="help-circle" style="width:12px;height:12px;"></i> <span>Óyfirfarin færtla</span>`;
    }
  }
  
  // Descendant Count (Íslendingabók)
  const descRow = document.getElementById('p-descendant-count-row');
  const descVal = document.getElementById('p-descendant-count-val');
  if (descRow && descVal) {
    if (p.descendant_count) {
      descVal.innerHTML = `🌟 <strong>${p.descendant_count}</strong>`;
      descRow.style.display = 'flex';
    } else {
      descRow.style.display = 'none';
    }
  }

  // Basic Details
  const birthInfo = document.getElementById('p-birth-info');
  if (birthInfo) birthInfo.textContent = p.birth_date || p.birth_year || 'Óþekkt';

  const deathInfo = document.getElementById('p-death-info');
  if (deathInfo) deathInfo.textContent = p.death_date || p.death_year || 'Lifandi / Óþekkt';

  // Father
  const fatherEl = document.getElementById('p-father-info');
  if (fatherEl) {
    if (family.father) {
      fatherEl.innerHTML = `<span class="relation-value clickable" onclick="selectPerson('${family.father.id}')" style="color:var(--accent-gold);cursor:pointer;">${family.father.name}</span>`;
    } else {
      fatherEl.textContent = 'Óþekktur';
    }
  }

  // Mother
  const motherEl = document.getElementById('p-mother-info');
  if (motherEl) {
    if (family.mother) {
      motherEl.innerHTML = `<span class="relation-value clickable" onclick="selectPerson('${family.mother.id}')" style="color:var(--accent-gold);cursor:pointer;">${family.mother.name}</span>`;
    } else {
      motherEl.textContent = 'Óþekkt';
    }
  }

  // Spouse(s)
  const spouseEl = document.getElementById('p-spouse-info');
  if (spouseEl) {
    if (family.spouse && family.spouse.length > 0) {
      const unique = [...new Map(family.spouse.map(s => [s.id, s])).values()];
      spouseEl.innerHTML = unique.map(s => `<span class="relation-value clickable" onclick="selectPerson('${s.id}')" style="color:var(--accent-gold);cursor:pointer;display:block;">${s.name}</span>`).join('');
    } else {
      spouseEl.textContent = 'Enginn skráður';
    }
  }

  // Children
  const childrenEl = document.getElementById('p-children-list');
  if (childrenEl) {
    if (family.children && family.children.length > 0) {
      const unique = [...new Map(family.children.map(c => [c.id, c])).values()];
      childrenEl.innerHTML = unique.map(c => `
        <span class="relation-value clickable" onclick="selectPerson('${c.id}')" style="display:block;font-size:0.85rem;color:var(--accent-gold);margin-bottom:0.2rem;cursor:pointer;">
          ${c.name}${c.birth_year ? ' (' + c.birth_year + ')' : ''}
        </span>
      `).join('');
    } else {
      childrenEl.innerHTML = '<span style="color:var(--text-muted);font-size:0.8rem;">Engin börn skráð</span>';
    }
  }

  // Research Notes Summary / Biography
  const notesEl = document.getElementById('p-research-notes');
  if (notesEl) {
    if (p.notes) {
      let formattedHtml = p.notes
        .replace(/^# (.*$)/gim, '<div style="font-size:1.05rem;font-weight:700;color:var(--accent-gold);margin-bottom:0.4rem;">$1</div>')
        .replace(/^## (.*$)/gim, '<div style="font-size:0.92rem;font-weight:600;color:#fff;margin-top:0.6rem;margin-bottom:0.25rem;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:2px;">$1</div>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/^- (.*$)/gim, '<div style="padding-left:0.8rem;margin-bottom:0.2rem;position:relative;"><span style="position:absolute;left:0;color:var(--accent-gold);">•</span>$1</div>')
        .replace(/\n\n/gim, '<div style="height:0.4rem;"></div>');
      notesEl.innerHTML = formattedHtml;
    } else {
      notesEl.textContent = `Ekki er búið að skrá rannsóknarnótur fyrir ${p.name}. Ýttu á 'Keyra Google AI leit' til að afla upplýsinga sjálfvirkt.`;
    }
  }

  // Also populate Tab 2: Biography & Format
  const formattedBioTextarea = document.getElementById('formatted-bio-text');
  if (formattedBioTextarea && p.notes) {
    formattedBioTextarea.value = p.notes;
  }
  
  // Avatar
  const avatarImg = document.getElementById('p-avatar-img');
  const avatarIcon = document.getElementById('p-avatar-icon');
  if (avatarImg && avatarIcon) {
    const btnRemove = document.getElementById('btn-remove-avatar');
    if (p.avatar_url) {
      avatarImg.src = p.avatar_url.startsWith('images/') ? `./${p.avatar_url}` : p.avatar_url;
      avatarImg.style.display = 'block';
      avatarIcon.style.display = 'none';
      avatarImg.onerror = () => { avatarImg.style.display='none'; avatarIcon.style.display='block'; };
      if (p.avatar_verified) {
        avatarImg.title = "✓ Staðfest prófílmynd (Læst)";
      }
      if (btnRemove) btnRemove.style.display = 'inline-flex';
    } else {
      avatarImg.style.display = 'none';
      avatarIcon.style.display = 'block';
      if (btnRemove) btnRemove.style.display = 'none';
    }
  }

  // Quick Links
  const encodedName = encodeURIComponent(p.name || '');
  
  const linkTimarit = document.getElementById('link-timarit');
  if (linkTimarit) linkTimarit.href = `https://timarit.is/search?q=${encodedName}`;
  
  const linkMbl = document.getElementById('link-mbl');
  if (linkMbl) linkMbl.href = `https://www.mbl.is/greinasafn/leit/?q=${encodedName}`;

  // Confirmed Sources Gallery
  renderConfirmedSources(sources);
  
  // AI Suggestions Section
  renderAISuggestions(suggestions, p.id);
  
  // Render Interactive Tree immediately and reliably
  try {
    renderInteractiveTree();
  } catch(err) {
    console.error("renderInteractiveTree call error:", err);
  }
  
  try { if (window.lucide) lucide.createIcons(); } catch(e) {}
}

function renderConfirmedSources(sources) {
  const gallery = document.getElementById('p-sources-gallery');
  if (!gallery) return;
  
  if (!sources || sources.length === 0) {
    gallery.innerHTML = `<div style="font-size:0.85rem;color:var(--text-muted);padding:1rem;text-align:center;border:1px dashed var(--border-color);border-radius:6px;">Engar staðfestar heimildir ennþá.</div>`;
    return;
  }

  gallery.innerHTML = sources.map(s => {
    const hasImage = s.image_url || s.local_path;
    const imgSrc = s.local_path
      ? (s.local_path.startsWith('images/') ? `./${encodeURIComponent(s.local_path)}` : s.local_path)
      : (s.image_url
        ? (s.image_url.startsWith('images/') ? `./${encodeURIComponent(s.image_url)}` : s.image_url)
        : null);
    
    const domain = s.link ? (() => { try { return new URL(s.link).hostname.replace('www.',''); } catch(e) { return ''; } })() : '';
    const snippet = s.snippet ? s.snippet.substring(0, 120) + (s.snippet.length > 120 ? '…' : '') : '';

    return `
      <div style="background:rgba(255,255,255,0.03);padding:0.85rem;border-radius:8px;border:1px solid var(--border-color);display:flex;gap:0.75rem;align-items:flex-start;position:relative;">
        ${imgSrc ? `
          <div style="position:relative;flex-shrink:0;">
            <img src="${imgSrc}" style="width:64px;height:64px;object-fit:cover;border-radius:6px;border:1px solid var(--border-color);cursor:pointer;" 
                 onclick="setProfileImage('${state.selectedPersonId}', '${s.local_path || s.image_url || ''}', this)"
                 title="Smella til að setja sem prófílmynd">
            <div style="position:absolute;bottom:2px;right:2px;background:rgba(0,0,0,0.7);border-radius:3px;padding:1px 3px;font-size:9px;color:#fff;">📷</div>
          </div>
        ` : `<i data-lucide="book-open" style="width:24px;height:24px;color:var(--accent-gold);flex-shrink:0;margin-top:2px;"></i>`}
        <div style="flex-grow:1;min-width:0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.2rem;">
            <div style="font-weight:600;font-size:0.88rem;color:var(--accent-gold);">${s.title}</div>
            <span class="badge badge-success" style="font-size:0.62rem;padding:1px 5px;">✓ Staðfest</span>
          </div>
          ${snippet ? `<div style="font-size:0.78rem;color:var(--text-secondary);margin-bottom:0.3rem;line-height:1.4;">${snippet}</div>` : ''}
          ${domain ? `<div style="font-size:0.72rem;color:var(--text-muted);">🔗 ${domain}</div>` : ''}
          ${s.link ? `<a href="${s.link}" target="_blank" style="font-size:0.72rem;color:var(--accent-gold);margin-top:0.25rem;display:inline-flex;align-items:center;gap:4px;">Opna heimild <i data-lucide="external-link" style="width:10px;height:10px;"></i></a>` : ''}
        </div>
        <button onclick="deleteSource(${s.id}, '${state.selectedPersonId}')" 
                title="Eyða heimild"
                style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:2px;flex-shrink:0;opacity:0.6;transition:opacity 0.2s;"
                onmouseover="this.style.opacity='1';this.style.color='#e53e3e'"
                onmouseout="this.style.opacity='0.6';this.style.color='var(--text-muted)'">
          <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
        </button>
      </div>
    `;
  }).join('');
  
  try { if (window.lucide) lucide.createIcons(); } catch(e) {}
}

window.deleteSource = async function(sourceId, personId) {
  if (!confirm('Eyða þessari heimild?')) return;
  try {
    const res = await fetch(`/api/delete_source?source_id=${sourceId}&person_id=${personId}`, { method: 'POST' });
    if (!res.ok) throw new Error('Villa');
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast('Heimild eytt!');
  } catch(e) {
    showToast('Villa við eyðingu: ' + e.message);
  }
};

window.setProfileImage = async function(personId, imagePath, imgEl) {
  if (!imagePath) return;
  try {
    const res = await fetch(`/api/set_profile_image?person_id=${personId}&image_path=${encodeURIComponent(imagePath)}`, { method: 'POST' });
    if (!res.ok) throw new Error('Villa');
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast('Prófílmynd uppfærð!');
  } catch(e) {
    showToast('Villa: ' + e.message);
  }
};

window.removeProfileAvatar = async function() {
  if (!state.selectedPersonId) return;
  if (!confirm('Viltu fjarlægja prófílmyndina af þessum einstaklingi?')) return;
  try {
    const res = await fetch(`/api/set_profile_image?person_id=${state.selectedPersonId}&image_path=`, { method: 'POST' });
    if (!res.ok) throw new Error('Villa');
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast('Prófílmynd fjarlægð!');
  } catch(e) {
    showToast('Villa: ' + e.message);
  }
};

function renderAISuggestions(suggestions, personId) {
  const container = document.getElementById('web-suggestions-section');
  const gallery = document.getElementById('p-suggestions-gallery');
  const countBadge = document.getElementById('suggestions-count');
  if (!container || !gallery || !countBadge) return;
  
  const allSugs = suggestions || [];
  const activeSugs = allSugs.filter(s => s.status === 'pending');
  const rejectedSugs = allSugs.filter(s => s.status === 'rejected');
  
  if (activeSugs.length === 0 && rejectedSugs.length === 0) {
    container.style.display = 'none';
    return;
  }
  container.style.display = 'block';
  
  countBadge.textContent = activeSugs.length;

  let html = '';
  
  if (activeSugs.length === 0 && rejectedSugs.length === 0) {
    html = `<div style="font-size: 0.85rem; color: var(--text-muted); padding: 1rem; text-align: center; border: 1px dashed var(--border-color); border-radius: 6px;">Engar uppástungur í boði. Ýttu á 'Keyra Google AI leit' til að leita á vefnum.</div>`;
  } else {
    html += activeSugs.map(s => renderSingleSuggestionCard(s, false)).join('');

    if (rejectedSugs.length > 0) {
      html += `
        <div style="margin-top: 1rem; border-top: 1px dashed var(--border-color); padding-top: 0.75rem; text-align: center;">
          <button class="btn btn-secondary" style="font-size: 0.75rem;" onclick="toggleShowRejected()">
            ${state.showRejected ? 'Fela hafnaðar uppástungur' : `Sýna hafnaðar uppástungur (${rejectedSugs.length})`}
          </button>
        </div>
      `;
      if (state.showRejected) {
        html += `<div style="margin-top: 0.75rem; display: flex; flex-direction: column; gap: 0.75rem;">`;
        html += rejectedSugs.map(s => renderSingleSuggestionCard(s, true)).join('');
        html += `</div>`;
      }
    }
  }

  gallery.innerHTML = html;
}

function renderSingleSuggestionCard(sug, isRejected) {
  const imgPath = sug.local_path || sug.image_url;
  const proxyImg = imgPath ? `./${encodeURIComponent(imgPath)}` : null;

  return `
    <div style="background: rgba(13,15,18,0.6); padding: 1rem; border-radius: 8px; border: 1px solid ${isRejected ? 'rgba(255,255,255,0.08)' : 'rgba(184,134,11,0.25)'}; position: relative;">
      <div style="display: flex; gap: 0.75rem; align-items: flex-start;">
        ${proxyImg ? `
          <div style="width: 80px; height: 80px; flex-shrink: 0; background: #000; border-radius: 6px; overflow: hidden; border: 1px solid var(--border-color);">
            <img src="${proxyImg}" style="width: 100%; height: 100%; object-fit: cover;">
          </div>
        ` : ''}
        <div style="flex-grow: 1;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.72rem; color: #ffb86c; font-weight: 700; text-transform: uppercase;">
              ${sug.type === 'image' ? '💡 Óstaðfest myndatillaga (Ágiskun)' : (sug.source || 'AI LEIT')}
            </span>
            <span class="badge badge-secondary" style="font-size: 0.65rem;">${sug.confidence}% öryggi</span>
          </div>
          <div style="font-weight: 600; font-size: 0.92rem; color: #fff; margin-top: 0.2rem;">${sug.title}</div>
          <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.35rem; line-height: 1.5;">${sug.description}</div>
          ${sug.type === 'image' ? '<div style="font-size:0.72rem;color:#f1fa8c;margin-top:0.25rem;">⚠️ Þetta er óstaðfest uppástunga af vefnum. Hún verður ekki prófílmynd nema þú ýtir á „Staðfesta & Vista“.</div>' : ''}
          ${sug.url ? `
            <div style="margin-top: 0.35rem;">
              <a href="${sug.url}" target="_blank" style="font-size: 0.75rem; color: var(--accent-gold); display: inline-flex; align-items: center; gap: 4px; text-decoration: none;">
                🔗 Skoða vefsíðu / heimild <i data-lucide="external-link" style="width: 11px; height: 11px;"></i>
              </a>
            </div>
          ` : ''}
        </div>
      </div>
      
      <div style="margin-top: 0.75rem; display: flex; justify-content: flex-end; gap: 0.5rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.6rem;">
        ${isRejected ? `
          <button class="btn btn-secondary" style="font-size: 0.75rem;" onclick="confirmSuggestion(${sug.id})">Endurheimta</button>
        ` : `
          <button class="btn btn-secondary" style="font-size: 0.75rem; color: #ff6b6b; border-color: rgba(255,107,107,0.3);" onclick="rejectSuggestion(${sug.id})">Hafna</button>
          <button class="btn btn-primary" style="font-size: 0.75rem; background: var(--accent-gold); color: black;" onclick="confirmSuggestion(${sug.id})">Staðfesta & Vista</button>
        `}
      </div>
    </div>
  `;
}

window.toggleShowRejected = function() {
  state.showRejected = !state.showRejected;
  if (state.personDetails) {
    renderAISuggestions(state.personDetails.suggestions || [], state.selectedPersonId);
    lucide.createIcons();
  }
};

window.regenerateBio = async function() {
  if (!state.selectedPersonId) return;
  const btn = document.getElementById('btn-regen-bio');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Semur ævisögu...';
    try { lucide.createIcons(); } catch(e) {}
  }
  try {
    const res = await fetch(`/api/generate_bio?person_id=${state.selectedPersonId}`, { method: 'POST' });
    if (!res.ok) throw new Error('Gat ekki endurgert samantekt.');
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast('Lífshlaupssamantekt hefur verið endurgerð!');
  } catch(e) {
    console.error('Bio Regen Error:', e);
    showToast('Villa við að endurgera samantekt: ' + e.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="refresh-cw" style="width:12px;height:12px;"></i> Endurgera samantekt';
      try { lucide.createIcons(); } catch(e) {}
    }
  }
};

window.runAIResearch = async function() {
  if (!state.selectedPersonId || !state.personDetails) return;
  const p = state.personDetails.person;
  if (!p) return;

  const btn = document.getElementById('btn-run-ai-research');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Leitar með Google AI...';
    lucide.createIcons();
  }

  try {
    const res = await fetch(`/api/run_scraper?id=${p.id}&name=${encodeURIComponent(p.name)}&birth=${p.birth_year || ''}`);
    if (!res.ok) throw new Error("Villa við leit.");
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast("Google AI leit lokið og uppfært!");
  } catch (err) {
    console.error("AI Research Error:", err);
    showToast("Villa kom upp við AI leit: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="sparkles"></i> Keyra Google AI leit';
      lucide.createIcons();
    }
  }
};

window.confirmSuggestion = async function(sugId) {
  try {
    const res = await fetch(`/api/confirm_suggestion?id=${state.selectedPersonId}&sug_id=${sugId}`, { method: 'POST' });
    if (!res.ok) throw new Error("Gat ekki staðfest.");
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast("Uppástunga staðfest!");
  } catch (err) {
    console.error(err);
    showToast("Villa við að staðfesta.");
  }
};

window.rejectSuggestion = async function(sugId) {
  try {
    const res = await fetch(`/api/reject_suggestion?id=${state.selectedPersonId}&sug_id=${sugId}`, { method: 'POST' });
    if (!res.ok) throw new Error("Gat ekki hafnað.");
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast("Uppástungu hafnað.");
  } catch (err) {
    console.error(err);
    showToast("Villa við að hafna.");
  }
};

window.triggerAvatarUpload = function() {
  const input = document.getElementById('avatar-file-input');
  if (input) input.click();
};

window.handleAvatarUpload = async function() {
  const input = document.getElementById('avatar-file-input');
  if (!input || !input.files || input.files.length === 0) return;

  const formData = new FormData();
  formData.append('avatar', input.files[0]);

  try {
    const res = await fetch(`/api/upload_avatar?id=${state.selectedPersonId}`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error("Gat ekki hlaðið inn mynd.");
    const data = await res.json();
    state.personDetails = data.details;
    renderPersonProfile(data.details);
    showToast("Prófílmynd uppfærð!");
  } catch (err) {
    console.error(err);
    showToast("Villa við innkall prófílmyndar.");
  }
};

function openSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) modal.style.display = 'flex'; const activeTreeName = (state.currentTree === 'loa' ? 'Lóutrésins' : 'Sigurjónstrésins');
}

function closeSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) modal.style.display = 'none';
}

async function saveSettings() {
  const keyInput = document.getElementById('input-gemini-key');
  const key = keyInput ? keyInput.value.trim() : '';
  
  if (!key) {
    showToast("Vinsamlegast sláðu inn API lykil.");
    return;
  }

  try {
    const res = await fetch(`/api/save_settings?key=${encodeURIComponent(key)}`, { method: 'POST' });
    if (res.ok) {
      showToast("Stillingar vistaðar!");
      closeSettingsModal();
    }
  } catch (err) {
    console.error(err);
    showToast("Villa við að vista stillingar.");
  }
}



// ==========================================
// GLÆSILEGT GAGNVIRKT ÆTTARTRÉ (DESKTOP + MOBILE ENGINE)
// ==========================================

async function renderInteractiveTree() {
  const container = document.getElementById('interactive-tree-canvas');
  if (!container) return;
  
  const currentId = state.selectedPersonId;
  if (!currentId) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:3rem;">Engin persóna valin.</div>';
    return;
  }

  container.innerHTML = `
    <div style="text-align:center;padding:3rem;color:var(--accent-gold);">
      <i data-lucide="loader-2" class="spin" style="width:28px;height:28px;"></i>
      <div style="margin-top:0.5rem;font-size:0.85rem;">Teikna ættartré...</div>
    </div>
  `;
  try { if (window.lucide) lucide.createIcons(); } catch(e) {}

  try {
    const res = await fetch(`/api/person?id=${currentId}`);
    if (!res.ok) throw new Error("Gat ekki sótt gögn fyrir ættartré.");
    const data = await res.json();
    const p = data.person;
    const fam = data.family || {};

    let pGrandParents = { ff: null, fm: null, mf: null, mm: null };
    
    if (fam.father && fam.father.id) {
      try {
        const fRes = await fetch(`/api/person?id=${fam.father.id}`);
        if (fRes.ok) {
          const fData = await fRes.json();
          pGrandParents.ff = fData.family?.father || null;
          pGrandParents.fm = fData.family?.mother || null;
        }
      } catch(e){}
    }
    if (fam.mother && fam.mother.id) {
      try {
        const mRes = await fetch(`/api/person?id=${fam.mother.id}`);
        if (mRes.ok) {
          const mData = await mRes.json();
          pGrandParents.mf = mData.family?.father || null;
          pGrandParents.mm = mData.family?.mother || null;
        }
      } catch(e){}
    }

    function renderNode(person, role, isFocus = false) {
      if (!person) {
        return `
          <div style="width:138px;padding:0.45rem 0.5rem;border-radius:6px;border:1px dashed rgba(255,255,255,0.15);background:rgba(0,0,0,0.25);text-align:center;color:var(--text-muted);font-size:0.68rem;">
            <em>Óþekkt(ur) ${role}</em>
          </div>
        `;
      }
      const pName = person.name || 'Óþekkt nafn';
      const bYear = person.birth_year ? `f. ${person.birth_year}` : '';
      const dYear = person.death_year ? `d. ${person.death_year}` : '';
      const dates = [bYear, dYear].filter(Boolean).join(' – ');
      const avatarUrl = person.avatar_url ? (person.avatar_url.startsWith('images/') ? `./${person.avatar_url}` : person.avatar_url) : '';
      
      const borderColor = isFocus ? 'var(--accent-gold)' : 'rgba(255,255,255,0.15)';
      const bg = isFocus ? 'linear-gradient(135deg, rgba(184,134,11,0.25) 0%, rgba(20,24,30,0.95) 100%)' : 'rgba(20,24,30,0.85)';
      const boxShadow = isFocus ? '0 0 12px rgba(184,134,11,0.4), 0 3px 8px rgba(0,0,0,0.6)' : '0 2px 6px rgba(0,0,0,0.4)';

      return `
        <div onclick="selectPerson('${person.id}')" style="width:145px;padding:0.45rem 0.55rem;border-radius:8px;border:1.5px solid ${borderColor};background:${bg};box-shadow:${boxShadow};cursor:pointer;transition:all 0.15s ease;position:relative;" onmouseover="this.style.transform='translateY(-2px)';this.style.borderColor='var(--accent-gold)'" onmouseout="this.style.transform='none';this.style.borderColor='${borderColor}'">
          ${isFocus ? '<span style="position:absolute;top:-8px;left:50%;transform:translateX(-50%);background:var(--accent-gold);color:#000;font-size:0.58rem;font-weight:bold;padding:1px 6px;border-radius:8px;text-transform:uppercase;letter-spacing:0.3px;">Valin</span>' : ''}
          <div style="display:flex;align-items:center;gap:0.4rem;text-align:left;">
            <div style="width:30px;height:30px;min-width:30px;border-radius:50%;overflow:hidden;border:1px solid ${isFocus ? 'var(--accent-gold)' : 'rgba(255,255,255,0.2)'};background:rgba(0,0,0,0.4);flex-shrink:0;display:flex;align-items:center;justify-content:center;">
              ${avatarUrl ? `<img src="${avatarUrl}" style="width:100%;height:100%;object-fit:cover;">` : '<i data-lucide="user" style="width:14px;height:14px;color:var(--text-muted);"></i>'}
            </div>
            <div style="overflow:hidden;flex-grow:1;min-width:0;">
              <div style="font-weight:600;font-size:0.75rem;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${pName}">${pName}</div>
              <div style="font-size:0.65rem;color:var(--text-secondary);margin-top:1px;">${dates || role}</div>
            </div>
          </div>
        </div>
      `;
    }

    function renderMobileCard(person, role, isFocus = false) {
      if (!person) return '';
      const pName = person.name || 'Óþekkt';
      const bYear = person.birth_year ? `f. ${person.birth_year}` : '';
      const dYear = person.death_year ? `d. ${person.death_year}` : '';
      const dates = [bYear, dYear].filter(Boolean).join(' – ');
      const avatarUrl = person.avatar_url ? (person.avatar_url.startsWith('images/') ? `./${person.avatar_url}` : person.avatar_url) : '';

      return `
        <div class="mobile-tree-card ${isFocus ? 'focus' : ''}" onclick="selectPerson('${person.id}')">
          <div style="width:38px;height:38px;border-radius:50%;overflow:hidden;border:1.5px solid ${isFocus ? 'var(--accent-gold)' : 'rgba(255,255,255,0.2)'};background:rgba(0,0,0,0.4);flex-shrink:0;display:flex;align-items:center;justify-content:center;">
            ${avatarUrl ? `<img src="${avatarUrl}" style="width:100%;height:100%;object-fit:cover;">` : '<i data-lucide="user" style="width:18px;height:18px;color:var(--text-muted);"></i>'}
          </div>
          <div style="flex-grow:1;overflow:hidden;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="font-weight:600;font-size:0.88rem;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${pName}</span>
              ${role ? `<span style="font-size:0.68rem;color:var(--accent-gold);background:rgba(184,134,11,0.15);padding:1px 6px;border-radius:4px;">${role}</span>` : ''}
            </div>
            <div style="font-size:0.72rem;color:var(--text-secondary);margin-top:2px;">${dates}</div>
          </div>
          <i data-lucide="chevron-right" style="width:16px;height:16px;color:var(--accent-gold);flex-shrink:0;"></i>
        </div>
      `;
    }

    // 1. DESKTOP 2D GRAPH (Compact & Perfectly Fitting Vertical Flow)
    let desktopHtml = `
      <div class="tree-container-desktop" style="flex-direction:column;align-items:center;gap:0.8rem;width:100%;padding:0.5rem 0;">
        
        <!-- Afar og Ömmur -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:0.25rem;width:100%;">
          <div style="font-size:0.68rem;font-weight:bold;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">👵👴 Afar & Ömmur</div>
          <div style="display:flex;justify-content:space-around;width:100%;gap:0.6rem;">
            <div style="display:flex;gap:0.4rem;">
              ${renderNode(pGrandParents.ff, 'Föðurafi')}
              ${renderNode(pGrandParents.fm, 'Föðuramma')}
            </div>
            <div style="display:flex;gap:0.4rem;">
              ${renderNode(pGrandParents.mf, 'Móðurafi')}
              ${renderNode(pGrandParents.mm, 'Móðuramma')}
            </div>
          </div>
        </div>

        <div style="width:50%;height:1.5px;background:rgba(184,134,11,0.25);position:relative;">
          <div style="position:absolute;left:25%;top:-6px;bottom:-6px;width:1.5px;background:rgba(184,134,11,0.25);"></div>
          <div style="position:absolute;right:25%;top:-6px;bottom:-6px;width:1.5px;background:rgba(184,134,11,0.25);"></div>
        </div>

        <!-- Foreldrar -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:0.25rem;width:100%;">
          <div style="font-size:0.68rem;font-weight:bold;color:var(--accent-gold);text-transform:uppercase;letter-spacing:0.5px;">👨‍👩‍👦 Foreldrar</div>
          <div style="display:flex;justify-content:center;gap:1.5rem;">
            ${renderNode(fam.father, 'Faðir')}
            ${renderNode(fam.mother, 'Móðir')}
          </div>
        </div>

        <div style="width:1.5px;height:14px;background:var(--accent-gold);"></div>

        <!-- Valin persóna & Maki -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:0.3rem;">
          <div style="display:flex;align-items:center;gap:0.8rem;background:rgba(184,134,11,0.08);padding:0.5rem 0.8rem;border-radius:10px;border:1px solid rgba(184,134,11,0.25);">
            ${renderNode(p, 'Valin persóna', true)}
            ${(fam.spouse && fam.spouse.length > 0) ? `
              <div style="display:flex;align-items:center;gap:0.35rem;">
                <span style="font-size:1rem;" title="Maki">💍</span>
                <div style="display:flex;gap:0.4rem;">
                  ${fam.spouse.map(s => renderNode(s, 'Maki')).join('')}
                </div>
              </div>
            ` : ''}
          </div>
        </div>

        <!-- Systkini -->
        ${(fam.siblings && fam.siblings.length > 0) ? `
          <div style="display:flex;flex-direction:column;align-items:center;gap:0.25rem;width:100%;margin-top:-0.2rem;">
            <div style="font-size:0.68rem;font-weight:bold;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">👫 Systkini (${fam.siblings.length})</div>
            <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:0.4rem;max-width:850px;">
              ${fam.siblings.map(s => renderNode(s, 'Systkini')).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Börn -->
        ${(fam.children && fam.children.length > 0) ? `
          <div style="width:1.5px;height:14px;background:var(--accent-gold);"></div>
          <div style="display:flex;flex-direction:column;align-items:center;gap:0.25rem;width:100%;">
            <div style="font-size:0.68rem;font-weight:bold;color:var(--accent-gold);text-transform:uppercase;letter-spacing:0.5px;">👶 Börn & Afkomendur (${fam.children.length})</div>
            <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:0.5rem;max-width:850px;">
              ${fam.children.map(c => renderNode(c, 'Barn')).join('')}
            </div>
          </div>
        ` : '<div style="color:var(--text-muted);font-size:0.7rem;margin-top:0.25rem;">Engin börn skráð í þessari grein.</div>'}
      </div>
    `;

    // 2. MOBILE CARD FLOW (Responsive Vertical Flow for Phones)
    const grandList = [pGrandParents.ff, pGrandParents.fm, pGrandParents.mf, pGrandParents.mm].filter(Boolean);
    const parentList = [fam.father, fam.mother].filter(Boolean);

    let mobileHtml = `
      <div class="tree-container-mobile">
        
        <!-- Focus Person -->
        <div class="mobile-tree-section" style="border-color:var(--accent-gold);background:rgba(184,134,11,0.06);">
          <div class="mobile-tree-header"><i data-lucide="user-check" style="width:14px;height:14px;"></i> Valin persóna</div>
          <div class="mobile-tree-cards">
            ${renderMobileCard(p, 'Aðalpersóna', true)}
          </div>
        </div>

        <!-- Makar -->
        ${(fam.spouse && fam.spouse.length > 0) ? `
          <div class="mobile-tree-section">
            <div class="mobile-tree-header"><i data-lucide="heart" style="width:14px;height:14px;"></i> Maki (${fam.spouse.length})</div>
            <div class="mobile-tree-cards">
              ${fam.spouse.map(s => renderMobileCard(s, 'Maki')).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Foreldrar -->
        ${parentList.length > 0 ? `
          <div class="mobile-tree-section">
            <div class="mobile-tree-header"><i data-lucide="users" style="width:14px;height:14px;"></i> Foreldrar (${parentList.length})</div>
            <div class="mobile-tree-cards">
              ${parentList.map(par => renderMobileCard(par, par.id === fam.father?.id ? 'Faðir' : 'Móðir')).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Afar og Ömmur -->
        ${grandList.length > 0 ? `
          <div class="mobile-tree-section">
            <div class="mobile-tree-header"><i data-lucide="history" style="width:14px;height:14px;"></i> Afar & Ömmur (${grandList.length})</div>
            <div class="mobile-tree-cards">
              ${grandList.map(g => renderMobileCard(g, 'Afi/Amma')).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Systkini -->
        ${(fam.siblings && fam.siblings.length > 0) ? `
          <div class="mobile-tree-section">
            <div class="mobile-tree-header"><i data-lucide="user-plus" style="width:14px;height:14px;"></i> Systkini (${fam.siblings.length})</div>
            <div class="mobile-tree-cards">
              ${fam.siblings.map(s => renderMobileCard(s, 'Systkini')).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Börn & Afkomendur -->
        ${(fam.children && fam.children.length > 0) ? `
          <div class="mobile-tree-section">
            <div class="mobile-tree-header"><i data-lucide="baby" style="width:14px;height:14px;"></i> Börn & Afkomendur (${fam.children.length})</div>
            <div class="mobile-tree-cards">
              ${fam.children.map(c => renderMobileCard(c, 'Barn')).join('')}
            </div>
          </div>
        ` : ''}

      </div>
    `;

    container.innerHTML = desktopHtml + mobileHtml;
    try { if (window.lucide) lucide.createIcons(); } catch(e) {}

  } catch(err) {
    console.error("Tree render error:", err);
    container.innerHTML = `<div style="color:#ff6b6b;padding:2rem;text-align:center;">Villa við að teikna ættartré: ${err.message}</div>`;
  }
}


// ==========================================
// STÆKKUN OG MINNKUN Á PANELUM (PANEL TOGGLE)
// ==========================================

function toggleSidebarCollapse() {
  const sidebar = document.getElementById('app-sidebar');
  const btn = document.getElementById('btn-toggle-sidebar');
  const icon = document.getElementById('sidebar-toggle-icon');
  const text = document.getElementById('sidebar-toggle-text');
  
  if (!sidebar) return;
  const isCollapsed = sidebar.classList.toggle('collapsed');
  
  if (text) text.textContent = isCollapsed ? 'Sýna stiku' : 'Fela stiku';
  if (icon) {
    icon.setAttribute('data-lucide', isCollapsed ? 'panel-left-open' : 'panel-left-close');
    try { if (window.lucide) lucide.createIcons(); } catch(e){}
  }
}
window.toggleSidebarCollapse = toggleSidebarCollapse;

function toggleMaximizeTree() {
  const grid = document.getElementById('person-workspace-view');
  const btn = document.getElementById('btn-maximize-tree');
  const icon = document.getElementById('maximize-tree-icon');
  const text = document.getElementById('maximize-tree-text');
  
  if (!grid) return;
  const isMaximized = grid.classList.toggle('maximize-tree');
  
  if (text) text.textContent = isMaximized ? 'Sýna prófíl' : 'Stækka tré (Fullskjár)';
  if (icon) {
    icon.setAttribute('data-lucide', isMaximized ? 'minimize-2' : 'maximize-2');
    try { if (window.lucide) lucide.createIcons(); } catch(e){}
  }
}
window.toggleMaximizeTree = toggleMaximizeTree;


async function uploadPhoneScreenshot(input) {
  if (!input || !input.files || input.files.length === 0) return;
  const files = Array.from(input.files);
  const currentTree = state.currentTree || 'sigurjon';
  const treeLabel = currentTree === 'loa' ? 'Lóutré' : 'Sigurjónstré';
  
  showToast(`Sendi ${files.length} ábendingu/skjáskot fyrir ${treeLabel}...`);

  for (let i = 0; i < files.length; i++) {
    const formData = new FormData();
    formData.append('screenshot', files[i]);
    formData.append('tree_id', currentTree);

    try {
      const res = await fetch('/api/upload_screenshot', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error('Gat ekki sent skjáskot');
    } catch (err) {
      showToast('Villa við að senda: ' + err.message);
      return;
    }
  }
  showToast(`💡 ${files.length} ábending(ar)/skjáskot send(ar) fyrir ${treeLabel}!`);
  input.value = '';
}
window.uploadPhoneScreenshot = uploadPhoneScreenshot;


window.openNotableArticlesModal = async function() {
  const modal = document.getElementById('modal-notable-articles');
  const listEl = document.getElementById('notable-articles-list');
  if (!modal || !listEl) return;
  
  const currentTree = getActiveTreeId();
  const activeTreeName = (currentTree === 'loa' ? 'Lóutré' : 'Sigurjónstré');
  modal.style.display = 'flex';
  listEl.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Sæki greinar fyrir ${activeTreeName}...</div>`;
  
  try {
    const res = await fetch(`/api/notable_articles?tree_id=${currentTree}`);
    const data = await res.json();
    const articles = data.articles || [];
    
    if (articles.length === 0) {
      listEl.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-muted);">Engar sögulegar greinar skráðar í ${activeTreeName} ennþá.</div>`;
      return;
    }
    
    listEl.innerHTML = articles.map(a => {
      const datesStr = `(f. ${a.birth_year || '?'}${a.death_year ? ` - d. ${a.death_year}` : ''})`;
      return `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; transition: border-color 0.2s;" onmouseover="this.style.borderColor='var(--accent-gold)'" onmouseout="this.style.borderColor='var(--border-color)'">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.4rem;">
            <div>
              <span style="font-weight: 700; font-size: 1rem; color: #fff; cursor: pointer;" onclick="closeNotableArticlesModal(); selectPerson('${a.person_id}')" title="Opna spjald einstaklings">
                👤 ${a.name} <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">${datesStr}</span>
              </span>
              <div style="font-weight: 600; font-size: 0.88rem; color: var(--accent-gold); margin-top: 0.2rem;">
                📖 ${a.title}
              </div>
            </div>
            ${a.link ? `<a href="${a.link}" target="_blank" class="btn btn-secondary" style="font-size: 0.72rem; padding: 0.2rem 0.5rem; display: inline-flex; align-items: center; gap: 4px;">Opna á Tímarit.is <i data-lucide="external-link" style="width: 12px; height: 12px;"></i></a>` : ''}
          </div>
          <div style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.5; margin-top: 0.4rem; background: rgba(0,0,0,0.2); padding: 0.6rem; border-radius: 6px;">
            „${a.snippet}“
          </div>
        </div>
      `;
    }).join('');
    
    try { if (window.lucide) lucide.createIcons(); } catch(e) {}
  } catch(err) {
    listEl.innerHTML = `<div style="color:#e53e3e; padding:1rem; text-align:center;">Villa við að sækja greinar: ${err.message}</div>`;
  }
};

window.closeNotableArticlesModal = function() {
  const modal = document.getElementById('modal-notable-articles');
  if (modal) modal.style.display = 'none';
};


window.openTreeStatsModal = async function() {
  const modal = document.getElementById('modal-tree-stats');
  const bodyEl = document.getElementById('tree-stats-body');
  if (!modal || !bodyEl) return;
  
  const currentTree = getActiveTreeId();
  const activeTreeName = (currentTree === 'loa' ? 'Lóutrésins (Ólafía)' : 'Sigurjónstrésins (Sigurjón)');
  modal.style.display = 'flex';
  bodyEl.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Reikna tölfræði fyrir ${activeTreeName}...</div>`;
  
  try {
    const res = await fetch(`/api/tree_stats?tree_id=${currentTree}`);
    const d = await res.json();
    
    bodyEl.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; text-align: center;">
          <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Heildarfjöldi (${currentTree === 'loa' ? 'Lóutré' : 'Sigurjónstré'})</div>
          <div style="font-size: 1.6rem; font-weight: 700; color: var(--accent-gold); margin-top: 0.2rem;">${d.total_people}</div>
          <div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 0.2rem;">👨 ${d.males} karlar | 👩 ${d.females} konur</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; text-align: center;">
          <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Tímaspann ættar</div>
          <div style="font-size: 1.6rem; font-weight: 700; color: #fff; margin-top: 0.2rem;">${d.span_years} ár</div>
          <div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 0.2rem;">Árin ${d.earliest_birth} – ${d.latest_birth}</div>
        </div>
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; text-align: center;">
          <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Meðalaldur (látinna)</div>
          <div style="font-size: 1.6rem; font-weight: 700; color: #2ecc71; margin-top: 0.2rem;">${d.avg_lifespan} ár</div>
          <div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 0.2rem;">Yfir allar aldir</div>
        </div>
      </div>

      <div class="stats-grid-2col" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <!-- Langlífasta fólkið -->
        <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem;">
          <h4 style="color: var(--accent-gold); font-size: 0.95rem; margin-top: 0; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 6px;">
            🏆 Langlífustu forfeðurnir
          </h4>
          <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            ${(d.oldest_people || []).map((p, idx) => `
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.84rem; border-bottom: 1px dashed rgba(255,255,255,0.05); padding-bottom: 0.3rem;">
                <span>${idx+1}. <strong>${p.name}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">(${p.birth}-${p.death})</span></span>
                <span class="badge badge-success" style="font-size:0.75rem;">${p.age} ára</span>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Stærstu barnafjölskyldurnar -->
        <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem;">
          <h4 style="color: var(--accent-gold); font-size: 0.95rem; margin-top: 0; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 6px;">
            👶 Stærstu fjölskyldurnar (Flest börn)
          </h4>
          <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            ${(d.biggest_families || d.large_families || []).map((f, idx) => `
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.84rem; border-bottom: 1px dashed rgba(255,255,255,0.05); padding-bottom: 0.3rem;">
                <span>${idx+1}. <strong>${(f.parent_name || f.name)}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">${f.spouse_name ? `& ${f.spouse_name}` : ''}</span></span>
                <span class="badge badge-primary" style="font-size:0.75rem;">${f.child_count} börn</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>

      <!-- Afmælisdagar og dánardagar -->
      <div class="stats-grid-2col" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
        <!-- Afmælisdagar -->
        <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem;">
          <h4 style="color: var(--accent-gold); font-size: 0.95rem; margin-top: 0; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 6px;">
            🎂 Vinsælustu afmælisdagar
          </h4>
          <div style="display: flex; flex-direction: column; gap: 0.4rem;">
            ${(d.top_birth_days || []).map((b, idx) => `
              <div style="display: flex; justify-content: space-between; font-size: 0.84rem; border-bottom: 1px dashed rgba(255,255,255,0.05); padding-bottom: 0.2rem;">
                <span>${idx+1}. <strong>${(b.date || (Array.isArray(b) ? b[0] : ''))}</strong></span>
                <span style="color: var(--accent-gold);">${(b.count || (Array.isArray(b) ? b[1] : ''))} fæðingar</span>
              </div>
            `).join('')}
          </div>
          <div style="margin-top: 0.8rem; padding-top: 0.6rem; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.78rem; color: var(--text-secondary);">
            <strong>☀️ Vinsælustu mánuðir:</strong> ${(d.top_birth_months || []).slice(0, 3).map(m => `${(m.month || (Array.isArray(m) ? m[0] : ''))} (${(m.count || (Array.isArray(m) ? m[1] : ''))})`).join(' • ')}
          </div>
        </div>

        <!-- Dánardagar -->
        <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem;">
          <h4 style="color: var(--accent-gold); font-size: 0.95rem; margin-top: 0; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 6px;">
            🕊️ Vinsælustu dánardagar
          </h4>
          <div style="display: flex; flex-direction: column; gap: 0.4rem;">
            ${(d.top_death_days || []).map((b, idx) => `
              <div style="display: flex; justify-content: space-between; font-size: 0.84rem; border-bottom: 1px dashed rgba(255,255,255,0.05); padding-bottom: 0.2rem;">
                <span>${idx+1}. <strong>${(b.date || (Array.isArray(b) ? b[0] : ''))}</strong></span>
                <span style="color: var(--accent-gold);">${(b.count || (Array.isArray(b) ? b[1] : ''))} andlát</span>
              </div>
            `).join('')}
          </div>
          <div style="margin-top: 0.8rem; padding-top: 0.6rem; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.78rem; color: var(--text-secondary);">
            <strong>🍂 Vinsælustu mánuðir:</strong> ${(d.top_death_months || []).slice(0, 3).map(m => `${(m.month || (Array.isArray(m) ? m[0] : ''))} (${(m.count || (Array.isArray(m) ? m[1] : ''))})`).join(' • ')}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    bodyEl.innerHTML = `<div style="color: #e53e3e; padding: 1rem; text-align: center;">Villa við að reikna tölfræði: ${err.message}</div>`;
  }
};

window.closeTreeStatsModal = function() {
  const modal = document.getElementById('modal-tree-stats');
  if (modal) modal.style.display = 'none';
};


function getActiveTreeId() {
  const sel = document.getElementById('tree-select');
  if (sel && sel.value) return sel.value;
  return state.selectedTreeId || 'sigurjon';
}
window.getActiveTreeId = getActiveTreeId;

window.openFeedbackModal = function() {
  const modal = document.getElementById('modal-feedback');
  const treeLabel = document.getElementById('feedback-active-tree-label');
  const filesInput = document.getElementById('feedback-files');
  const countEl = document.getElementById('feedback-file-count');
  const textInput = document.getElementById('feedback-text');
  
  if (!modal) return;
  const currentTree = getActiveTreeId();
  if (treeLabel) treeLabel.textContent = currentTree === 'loa' ? '🌳 Lóa ættartré (Ólafía Rósbjörg)' : '🌳 Sigurjón ættartré (Sigurjón Axel)';
  if (textInput) textInput.value = '';
  if (filesInput) {
    filesInput.value = '';
    filesInput.onchange = function() {
      if (countEl) countEl.textContent = `${this.files.length} skjáskot valin`;
    };
  }
  if (countEl) countEl.textContent = 'Engin skrá valin';
  modal.style.display = 'flex';
};

window.closeFeedbackModal = function() {
  const modal = document.getElementById('modal-feedback');
  if (modal) modal.style.display = 'none';
};

window.submitFeedbackForm = async function() {
  const textInput = document.getElementById('feedback-text');
  const filesInput = document.getElementById('feedback-files');
  const note = textInput ? textInput.value.trim() : '';
  const files = filesInput && filesInput.files ? Array.from(filesInput.files) : [];
  const currentTree = getActiveTreeId();
  const treeLabel = currentTree === 'loa' ? 'Lóutré' : 'Sigurjónstré';

  if (!note && files.length === 0) {
    showToast('Vinsamlegast skrifaðu texta eða veldu skjáskot.');
    return;
  }

  showToast(`Sendi ábendingu fyrir ${treeLabel}...`);
  const submitBtn = document.getElementById('btn-submit-feedback');
  if (submitBtn) submitBtn.disabled = true;

  try {
    if (files.length > 0) {
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('screenshot', files[i]);
        formData.append('tree_id', currentTree);
        if (i === 0 && note) formData.append('user_note', note);
        await fetch('/api/upload_screenshot', { method: 'POST', body: formData });
      }
    } else if (note) {
      const formData = new FormData();
      formData.append('user_note', note);
      formData.append('tree_id', currentTree);
      await fetch('/api/upload_screenshot', { method: 'POST', body: formData });
    }

    showToast(`💡 Ábending send fyrir ${treeLabel}!`);
    closeFeedbackModal();
  } catch (err) {
    showToast('Villa við að senda: ' + err.message);
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
};


// ========================================================
// ÚTGÁFUSTJÓRNUN (VERSIONING & ROLLBACK / SNAPSHOTS)
// ========================================================

window.openPersonHistoryModal = async function() {
  const modal = document.getElementById('modal-person-history');
  const listEl = document.getElementById('person-history-list');
  const titleEl = document.getElementById('history-modal-title');
  if (!modal || !listEl) return;

  const currentPerson = state.selectedPerson || state.personDetails?.person || (state.people && state.selectedPersonId ? state.people.find(p => p.id === state.selectedPersonId) : null);
  if (!currentPerson) {
    showToast('Veldu fyrst einstakling.');
    return;
  }

  modal.style.display = 'flex';
  if (titleEl) titleEl.textContent = `Breytingasaga: ${currentPerson.name}`;
  listEl.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Sæki breytingasögu...</div>';

  try {
    const res = await fetch(`/api/person_history?person_id=${encodeURIComponent(currentPerson.id)}&tree_id=${encodeURIComponent(getActiveTreeId())}`);
    const data = await res.json();
    const history = data.history || [];

    if (history.length === 0) {
      listEl.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Engin breytingasaga skráð enn fyrir þennan einstakling.</div>';
      return;
    }

    listEl.innerHTML = history.map((h, idx) => {
      const snap = JSON.parse(h.snapshot_data || '{}');
      const prev = (idx + 1 < history.length) ? JSON.parse(history[idx + 1].snapshot_data || '{}') : null;
      const isLatest = (idx === 0);

      // Reikna hvað er nýtt eða breytt miðað við fyrri útgáfu (Diff)
      let diffItems = [];
      if (prev) {
        if (snap.name !== prev.name) diffItems.push(`📝 <strong>Nafn leiðrétt:</strong> <span style="text-decoration:line-through;color:#ff8888;">${prev.name || 'tómt'}</span> ➔ <span style="color:#a8ffb2;">${snap.name}</span>`);
        if (snap.birth_date !== prev.birth_date) diffItems.push(`🎂 <strong>Fæðing:</strong> ${snap.birth_date || 'óþekkt'}`);
        if (snap.birth_place !== prev.birth_place && snap.birth_place) diffItems.push(`📍 <strong>Fæðingarstaður:</strong> ${snap.birth_place}`);
        if (snap.death_date !== prev.death_date && snap.death_date) diffItems.push(`🕊️ <strong>Andlát:</strong> ${snap.death_date}`);
        if (snap.ib_sources !== prev.ib_sources && snap.ib_sources) diffItems.push(`🏛️ <strong>Íslendingabókarheimildir:</strong> ${snap.ib_sources}`);
        if (snap.notes !== prev.notes) {
          const notesLenDiff = (snap.notes || '').length - (prev.notes || '').length;
          diffItems.push(`📖 <strong>Lífshlaup & Samantekt uppfærð</strong> (${notesLenDiff >= 0 ? '+' : ''}${notesLenDiff} stafir)`);
        }
      }

      // Full line-by-line diff of notes if they changed
      let notesDiffHtml = '';
      if (prev && snap.notes !== prev.notes) {
        const linesPrev = (prev.notes || '').split('\n');
        const linesCurr = (snap.notes || '').split('\n');
        const addedLines = linesCurr.filter(l => l.trim() && !linesPrev.includes(l));
        const removedLines = linesPrev.filter(l => l.trim() && !linesCurr.includes(l));

        notesDiffHtml = `
          <div style="margin-top: 0.4rem; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 0.6rem; font-family: monospace; font-size: 0.75rem; max-height: 180px; overflow-y: auto;">
            <div style="font-weight: 700; color: var(--text-muted); margin-bottom: 0.3rem; font-family: sans-serif;">🔍 Textabreytingar (Diff):</div>
            ${removedLines.slice(0, 5).map(l => `<div style="color: #ff8888; background: rgba(255,0,0,0.1); padding: 1px 4px; margin-bottom: 2px;">- ${l}</div>`).join('')}
            ${addedLines.slice(0, 8).map(l => `<div style="color: #a8ffb2; background: rgba(0,255,0,0.1); padding: 1px 4px; margin-bottom: 2px;">+ ${l}</div>`).join('')}
            ${(addedLines.length > 8 || removedLines.length > 5) ? `<div style="color: var(--text-muted); padding: 2px;">... og fleiri línur</div>` : ''}
          </div>
        `;
      }

      return `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid ${isLatest ? 'var(--accent-gold)' : 'var(--border-color)'}; border-radius: 8px; padding: 1rem 1.2rem; display: flex; flex-direction: column; gap: 0.5rem;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; font-size: 1rem; color: ${isLatest ? 'var(--accent-gold)' : '#fff'}; display: flex; align-items: center; gap: 6px;">
              🏷️ Útgáfa ${h.version_num} ${isLatest ? '<span class="badge badge-success" style="font-size:0.68rem;">Núverandi</span>' : ''}
            </span>
            <span style="font-size: 0.76rem; color: var(--text-muted);">${h.changed_at}</span>
          </div>
          
          <div style="font-size: 0.86rem; color: #eee;">
            <strong>Aðgerð:</strong> ${h.change_summary || h.change_type}
          </div>

          ${diffItems.length > 0 ? `
            <div style="font-size: 0.82rem; color: var(--accent-gold); background: rgba(184,134,11,0.08); border-left: 3px solid var(--accent-gold); padding: 0.6rem 0.8rem; border-radius: 0 6px 6px 0; display: flex; flex-direction: column; gap: 0.35rem;">
              <div style="font-weight: 700; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.5px;">✨ Hvað breyttist frá Útgáfu ${h.version_num - 1}:</div>
              ${diffItems.map(d => `<div>${d}</div>`).join('')}
            </div>
            ${notesDiffHtml}
          ` : (prev ? `<div style="font-size: 0.78rem; color: var(--text-muted); font-style: italic; background: rgba(255,255,255,0.02); padding: 0.4rem 0.6rem; border-radius: 4px;">Engin gögn breyttust frá v1 (Staðfesting & jöfnun á spjaldi).</div>` : '')}

          <div style="font-size: 0.78rem; color: var(--text-secondary); background: rgba(0,0,0,0.25); padding: 0.6rem; border-radius: 6px; margin-top: 0.2rem;">
            <div><strong>Nafn:</strong> ${snap.name || '-'} (${snap.birth_year || '?'}-${snap.death_year || '?'})</div>
            ${snap.birth_place ? `<div><strong>Fæðingarstaður:</strong> ${snap.birth_place}</div>` : ''}
            ${snap.ib_sources ? `<div><strong>Heimildir:</strong> ${snap.ib_sources}</div>` : ''}
          </div>

          ${!isLatest ? `
            <div style="display: flex; justify-content: flex-end; margin-top: 0.4rem;">
              <button class="btn btn-secondary" onclick="rollbackPersonVersion(${h.id})" style="font-size: 0.76rem; padding: 0.25rem 0.7rem; color: var(--accent-gold); border-color: rgba(184,134,11,0.3); display: flex; align-items: center; gap: 5px;">
                ↩️ Endurheimta þessa útgáfu (${h.version_num})
              </button>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');

    try { if (window.lucide) lucide.createIcons(); } catch(e) {}
  } catch(err) {
    listEl.innerHTML = `<div style="color: #e53e3e; padding: 1rem; text-align: center;">Villa við að sækja sögu: ${err.message}</div>`;
  }
};

window.closePersonHistoryModal = function() {
  const modal = document.getElementById('modal-person-history');
  if (modal) modal.style.display = 'none';
};

window.rollbackPersonVersion = async function(historyId) {
  if (!confirm('Ertu viss um að vilja endurheimta þessa eldri útgáfu?')) return;
  showToast('Endurheimti útgáfu...');
  try {
    const res = await fetch(`/api/rollback_person?history_id=${historyId}`, { method: 'POST' });
    const d = await res.json();
    if (d.status === 'ok') {
      showToast('✓ Útgáfa endurheimt!');
      closePersonHistoryModal();
      if (d.details) {
        state.selectedPerson = d.details.person;
        renderPersonDetails(d.details);
      }
    } else {
      showToast('Villa: ' + (d.message || 'Gat ekki endurheimt'));
    }
  } catch(err) {
    showToast('Villa: ' + err.message);
  }
};

window.openTreeSnapshotsModal = async function() {
  const modal = document.getElementById('modal-tree-snapshots');
  const listEl = document.getElementById('tree-snapshots-list');
  if (!modal || !listEl) return;

  const currentTree = getActiveTreeId();
  modal.style.display = 'flex';
  listEl.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Sæki útgáfur trés...</div>';

  try {
    const res = await fetch(`/api/tree_snapshots?tree_id=${encodeURIComponent(currentTree)}`);
    const data = await res.json();
    const snaps = data.snapshots || [];

    if (snaps.length === 0) {
      listEl.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Engar útgáfur (snapshots) vistaðar enn.</div>';
      return;
    }

    listEl.innerHTML = snaps.map((s, idx) => `
      <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.9rem 1.1rem; display: flex; flex-direction: column; gap: 0.4rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700; font-size: 1rem; color: var(--accent-gold); display: flex; align-items: center; gap: 6px;">
            🏷️ ${s.tag}
          </span>
          <span style="font-size: 0.76rem; color: var(--text-muted);">${s.created_at}</span>
        </div>
        <div style="font-size: 0.85rem; color: #eee; margin-top: 0.2rem;">
          ${s.description || 'Engin lýsing'}
        </div>
        <div style="font-size: 0.76rem; color: var(--text-secondary); display: flex; gap: 1rem; margin-top: 0.2rem;">
          <span>👥 ${s.total_people} einstaklingar</span>
          <span>📜 ${s.total_sources} staðfestar heimildir</span>
        </div>
      </div>
    `).join('');

    try { if (window.lucide) lucide.createIcons(); } catch(e) {}
  } catch(err) {
    listEl.innerHTML = `<div style="color: #e53e3e; padding: 1rem; text-align: center;">Villa við að sækja útgáfur: ${err.message}</div>`;
  }
};

window.closeTreeSnapshotsModal = function() {
  const modal = document.getElementById('modal-tree-snapshots');
  if (modal) modal.style.display = 'none';
};

window.createNewTreeSnapshot = async function() {
  const tagInput = document.getElementById('new-snapshot-tag');
  const descInput = document.getElementById('new-snapshot-desc');
  const tag = tagInput ? tagInput.value.trim() : '';
  const desc = descInput ? descInput.value.trim() : '';
  const currentTree = getActiveTreeId();

  if (!tag) {
    showToast('Sláðu inn heiti útgáfu (t.d. v2.1-loka)');
    return;
  }

  showToast('Vista heildarútgáfu af trénu...');
  try {
    const res = await fetch(`/api/create_snapshot?tree_id=${encodeURIComponent(currentTree)}&tag=${encodeURIComponent(tag)}&description=${encodeURIComponent(desc)}`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast(`✓ Útgáfa ${tag} vistuð!`);
      if (tagInput) tagInput.value = '';
      if (descInput) descInput.value = '';
      openTreeSnapshotsModal();
    } else {
      showToast('Villa: ' + data.message);
    }
  } catch(err) {
    showToast('Villa: ' + err.message);
  }
};
