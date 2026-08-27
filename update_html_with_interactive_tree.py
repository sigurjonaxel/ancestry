with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add visual Family Tree tab to the workspace tab-bar
tab_search = '<div class="tab-bar">'
tab_replacement = '''<div class="tab-bar">
              <div class="tab active" data-tab="tab-pedigree">
                <i data-lucide="network" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 0.25rem; color: var(--accent-gold);"></i>
                🌳 Gagnvirkt Ættartré
              </div>'''

if 'data-tab="tab-pedigree"' not in html:
    html = html.replace('<div class="tab-bar">\n              <div class="tab active" data-tab="tab-ocr">', tab_replacement + '\n              <div class="tab" data-tab="tab-ocr">')

# 2. Add Tab Content for Interactive Tree (Pedigree & Descendants Canvas/Graph)
tree_content = '''
            <!-- Tab: Interactive Family Tree Navigator -->
            <div class="tab-content" id="tab-pedigree" style="display: block;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem; background: rgba(184,134,11,0.08); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid rgba(184,134,11,0.2);">
                <div>
                  <h3 style="font-size: 1.05rem; color: var(--accent-gold); margin: 0; display: flex; align-items: center; gap: 0.4rem;">
                    <i data-lucide="git-fork" style="width: 16px; height: 16px;"></i>
                    <span id="tree-nav-title">Gagnvirkt Ættartré & Afkomendur</span>
                  </h3>
                  <p style="font-size: 0.78rem; color: var(--text-muted); margin: 0.2rem 0 0 0;">
                    Smelltu á hvaða spjald sem er til að flakka um tréð, skoða forfeður, afkomendur og maka.
                  </p>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                  <button class="btn btn-secondary" onclick="renderInteractiveTree()" style="font-size: 0.75rem; padding: 0.35rem 0.7rem; display: inline-flex; align-items: center; gap: 4px;">
                    <i data-lucide="rotate-ccw" style="width: 12px; height: 12px;"></i> Miðja á valdan
                  </button>
                </div>
              </div>

              <!-- Interactive Visual Tree Container -->
              <div id="interactive-tree-canvas" style="background: radial-gradient(circle at 50% 50%, rgba(30,35,45,0.6) 0%, rgba(13,15,18,0.95) 100%); border: 1px solid var(--border-color); border-radius: 10px; padding: 1.5rem; min-height: 520px; overflow-x: auto; overflow-y: auto;">
                <div style="text-align: center; color: var(--text-muted); padding: 4rem 0;">
                  <i data-lucide="loader-2" class="spin" style="width: 32px; height: 32px; color: var(--accent-gold);"></i>
                  <div style="margin-top: 0.5rem;">Hleð inn ættartré...</div>
                </div>
              </div>
            </div>
'''

if 'id="tab-pedigree"' not in html:
    # Insert before tab-ocr
    html = html.replace('<!-- Tab 1: OCR -->\n            <div class="tab-content" id="tab-ocr">', tree_content + '\n            <!-- Tab 1: OCR -->\n            <div class="tab-content" id="tab-ocr" style="display: none;">')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✓ index.html uppfært með Gagnvirku Ættartré (Interactive Family Tree Navigator)!")
