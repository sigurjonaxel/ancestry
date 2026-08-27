# 1. Update index.css with collapsible sidebar & fullscreen workspace classes
with open("index.css", "r", encoding="utf-8") as f:
    css = f.read()

collapsible_css = '''
/* Collapsible & Resizable Panels */
.sidebar.collapsed {
  width: 0px !important;
  min-width: 0px !important;
  padding: 0 !important;
  overflow: hidden !important;
  border-right: none !important;
  opacity: 0;
  pointer-events: none;
}

.workspace-grid.maximize-tree {
  grid-template-columns: 1fr !important;
}

.workspace-grid.maximize-tree #person-details-card {
  display: none !important;
}

.workspace-grid.maximize-profile {
  grid-template-columns: 1fr !important;
}

.workspace-grid.maximize-profile > div:last-child {
  display: none !important;
}

.panel-toggle-btn {
  background: rgba(184,134,11,0.12);
  border: 1px solid rgba(184,134,11,0.3);
  color: var(--accent-gold);
  border-radius: 6px;
  padding: 0.35rem 0.6rem;
  font-size: 0.75rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.2s ease;
}

.panel-toggle-btn:hover {
  background: var(--accent-gold);
  color: #000;
  border-color: var(--accent-gold);
}
'''

if ".sidebar.collapsed" not in css:
    css += "\n" + collapsible_css
    with open("index.css", "w", encoding="utf-8") as f:
        f.write(css)

# 2. Add Toggle Buttons into the Header and Tabs in index.html
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Add Collapse Sidebar toggle in header
header_patch = '''      <div class="brand">
        <button class="panel-toggle-btn" id="btn-toggle-sidebar" title="Fela / Sýna vinstri hliðarstiku (Einstaklingalista)" onclick="toggleSidebarCollapse()">
          <i data-lucide="panel-left-close" id="sidebar-toggle-icon" style="width: 16px; height: 16px;"></i>
          <span id="sidebar-toggle-text">Fela stiku</span>
        </button>'''

if 'id="btn-toggle-sidebar"' not in html:
    html = html.replace('<div class="brand">', header_patch)

# Add Layout controls inside the interactive tree toolbar
tree_controls = '''                <div style="display: flex; gap: 0.5rem; align-items: center;">
                  <button class="panel-toggle-btn" id="btn-maximize-tree" onclick="toggleMaximizeTree()" title="Stækka ættartré yfir allan skjáinn">
                    <i data-lucide="maximize-2" id="maximize-tree-icon" style="width: 13px; height: 13px;"></i>
                    <span id="maximize-tree-text">Stækka tré (Fullskjár)</span>
                  </button>
                  <button class="btn btn-secondary" onclick="renderInteractiveTree()" style="font-size: 0.75rem; padding: 0.35rem 0.7rem; display: inline-flex; align-items: center; gap: 4px;">
                    <i data-lucide="rotate-ccw" style="width: 12px; height: 12px;"></i> Miðja
                  </button>
                </div>'''

if 'id="btn-maximize-tree"' not in html:
    html = html.replace('<button class="btn btn-secondary" onclick="renderInteractiveTree()" style="font-size: 0.75rem; padding: 0.35rem 0.7rem; display: inline-flex; align-items: center; gap: 4px;">\n                    <i data-lucide="rotate-ccw" style="width: 12px; height: 12px;"></i> Miðja á valdan\n                  </button>', tree_controls)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

# 3. Add JS functions in app.js
with open("app.js", "r", encoding="utf-8") as f:
    js = f.read()

panel_js = '''
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
'''

if "function toggleSidebarCollapse" not in js:
    js += "\n" + panel_js
    with open("app.js", "w", encoding="utf-8") as f:
        f.write(js)

print("✓ Stækkun og minnkun á panelum (Collapse Sidebar & Maximize Tree) komin í gagnið!")
