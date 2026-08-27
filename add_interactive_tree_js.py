with open("app.js", "r", encoding="utf-8") as f:
    js = f.read()

tree_renderer_code = '''
// ==========================================
// GLÆSILEGT GAGNVIRKT ÆTTARTRÉ (FAMILY TREE MODULE)
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

    // Sækja líka afa og ömmur ef foreldrar eru til
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
          <div style="width:170px;padding:0.75rem;border-radius:8px;border:1px dashed rgba(255,255,255,0.15);background:rgba(0,0,0,0.2);text-align:center;color:var(--text-muted);font-size:0.75rem;">
            <em>Óþekkt(ur) ${role}</em>
          </div>
        `;
      }
      const pName = person.name || 'Óþekkt nafn';
      const bYear = person.birth_year ? `f. ${person.birth_year}` : '';
      const dYear = person.death_year ? `d. ${person.death_year}` : '';
      const dates = [bYear, dYear].filter(Boolean).join(' – ');
      const avatarUrl = person.avatar_url ? (person.avatar_url.startsWith('images/') ? `/api/proxy_image?url=${encodeURIComponent(person.avatar_url)}` : person.avatar_url) : '';
      
      const borderColor = isFocus ? 'var(--accent-gold)' : 'rgba(255,255,255,0.15)';
      const bg = isFocus ? 'linear-gradient(135deg, rgba(184,134,11,0.25) 0%, rgba(20,24,30,0.95) 100%)' : 'rgba(20,24,30,0.85)';
      const boxShadow = isFocus ? '0 0 16px rgba(184,134,11,0.4), 0 4px 12px rgba(0,0,0,0.6)' : '0 4px 10px rgba(0,0,0,0.4)';

      return `
        <div onclick="selectPerson('${person.id}')" style="width:190px;padding:0.75rem;border-radius:10px;border:2px solid ${borderColor};background:${bg};box-shadow:${boxShadow};cursor:pointer;transition:all 0.2s ease;text-align:center;position:relative;" onmouseover="this.style.transform='translateY(-3px)';this.style.borderColor='var(--accent-gold)'" onmouseout="this.style.transform='none';this.style.borderColor='${borderColor}'">
          ${isFocus ? '<span style="position:absolute;top:-9px;left:50%;transform:translateX(-50%);background:var(--accent-gold);color:#000;font-size:0.65rem;font-weight:bold;padding:1px 8px;border-radius:10px;text-transform:uppercase;letter-spacing:0.5px;">Valin persóna</span>' : ''}
          <div style="display:flex;align-items:center;gap:0.5rem;text-align:left;">
            <div style="width:42px;height:42px;border-radius:50%;overflow:hidden;border:1.5px solid ${isFocus ? 'var(--accent-gold)' : 'rgba(255,255,255,0.2)'};background:rgba(0,0,0,0.4);flex-shrink:0;display:flex;align-items:center;justify-content:center;">
              ${avatarUrl ? `<img src="${avatarUrl}" style="width:100%;height:100%;object-fit:cover;">` : '<i data-lucide="user" style="width:20px;height:20px;color:var(--text-muted);"></i>'}
            </div>
            <div style="overflow:hidden;flex-grow:1;">
              <div style="font-weight:600;font-size:0.85rem;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${pName}">${pName}</div>
              <div style="font-size:0.72rem;color:var(--text-secondary);margin-top:2px;">${dates || role}</div>
            </div>
          </div>
        </div>
      `;
    }

    // Byggja HTML fyrir ættartréð
    let treeHtml = `
      <div style="display:flex;flex-direction:column;align-items:center;gap:2rem;min-width:760px;padding:1rem 0;">
        
        <!-- 1. Afar og Ömmur (Grandparents Level) -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:0.4rem;width:100%;">
          <div style="font-size:0.75rem;font-weight:bold;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;">👵👴 Afar & Ömmur</div>
          <div style="display:flex;justify-content:space-around;width:100%;gap:1rem;">
            <div style="display:flex;gap:0.6rem;">
              ${renderNode(pGrandParents.ff, 'Föðurafi')}
              ${renderNode(pGrandParents.fm, 'Föðuramma')}
            </div>
            <div style="display:flex;gap:0.6rem;">
              ${renderNode(pGrandParents.mf, 'Móðurafi')}
              ${renderNode(pGrandParents.mm, 'Móðuramma')}
            </div>
          </div>
        </div>

        <!-- Tengilínur niður í foreldra -->
        <div style="width:60%;height:2px;background:rgba(184,134,11,0.25);position:relative;">
          <div style="position:absolute;left:25%;top:-10px;bottom:-10px;width:2px;background:rgba(184,134,11,0.25);"></div>
          <div style="position:absolute;right:25%;top:-10px;bottom:-10px;width:2px;background:rgba(184,134,11,0.25);"></div>
        </div>

        <!-- 2. Foreldrar (Parents Level) -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:0.4rem;width:100%;">
          <div style="font-size:0.75rem;font-weight:bold;color:var(--accent-gold);text-transform:uppercase;letter-spacing:1px;">👨‍👩‍👦 Foreldrar</div>
          <div style="display:flex;justify-content:center;gap:3rem;">
            ${renderNode(fam.father, 'Faðir')}
            ${renderNode(fam.mother, 'Móðir')}
          </div>
        </div>

        <!-- Tengilína niður í valda persónu -->
        <div style="width:2px;height:24px;background:var(--accent-gold);"></div>

        <!-- 3. Valin persóna og Maki (Focus & Spouses Level) -->
        <div style="display:flex;flex-direction:column;align-items:center;gap:0.6rem;">
          <div style="display:flex;align-items:center;gap:1.2rem;background:rgba(184,134,11,0.06);padding:1rem 1.5rem;border-radius:14px;border:1px solid rgba(184,134,11,0.25);">
            ${renderNode(p, 'Valin persóna', true)}
            ${(fam.spouse && fam.spouse.length > 0) ? `
              <div style="display:flex;align-items:center;gap:0.5rem;">
                <span style="font-size:1.2rem;" title="Maki">💍</span>
                <div style="display:flex;gap:0.6rem;">
                  ${fam.spouse.map(s => renderNode(s, 'Maki')).join('')}
                </div>
              </div>
            ` : ''}
          </div>
        </div>

        <!-- 4. Systkini (Siblings) ef til eru -->
        ${(fam.siblings && fam.siblings.length > 0) ? `
          <div style="display:flex;flex-direction:column;align-items:center;gap:0.4rem;width:100%;margin-top:-0.5rem;">
            <div style="font-size:0.75rem;font-weight:bold;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;">👫 Systkini (${fam.siblings.length})</div>
            <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:0.6rem;max-width:850px;">
              ${fam.siblings.map(s => renderNode(s, 'Systkini')).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Tengilína niður í börn -->
        ${(fam.children && fam.children.length > 0) ? `
          <div style="width:2px;height:24px;background:var(--accent-gold);"></div>
          
          <!-- 5. Börn (Children Level) -->
          <div style="display:flex;flex-direction:column;align-items:center;gap:0.4rem;width:100%;">
            <div style="font-size:0.75rem;font-weight:bold;color:var(--accent-gold);text-transform:uppercase;letter-spacing:1px;">👶 Börn & Afkomendur (${fam.children.length})</div>
            <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:0.8rem;max-width:850px;">
              ${fam.children.map(c => renderNode(c, 'Barn')).join('')}
            </div>
          </div>
        ` : '<div style="color:var(--text-muted);font-size:0.75rem;margin-top:0.5rem;">Engin börn skráð í þessari grein.</div>'}

      </div>
    `;

    container.innerHTML = treeHtml;
    try { if (window.lucide) lucide.createIcons(); } catch(e) {}

  } catch(err) {
    console.error("Tree render error:", err);
    container.innerHTML = `<div style="color:#ff6b6b;padding:2rem;text-align:center;">Villa við að teikna ættartré: ${err.message}</div>`;
  }
}

// Hook renderInteractiveTree into renderPersonProfile
const origRenderPersonProfile = renderPersonProfile;
renderPersonProfile = function(details) {
  origRenderPersonProfile(details);
  renderInteractiveTree();
};
'''

if "function renderInteractiveTree" not in js:
    js += "\n" + tree_renderer_code
    with open("app.js", "w", encoding="utf-8") as f:
        f.write(js)
    print("✓ app.js uppfært með fullkominni gagnvirkri ættartrés- og afkomendateiknivél!")
else:
    print("renderInteractiveTree er þegar til í app.js")
