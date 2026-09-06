// Standalone GitHub Pages Client Adapter
// Intercepts /api/ calls and serves directly from static_data.json in memory!

let STATIC_DATA = null;

async function initStaticDatabase() {
  try {
    const res = await fetch('static_data.json');
    if (res.ok) {
      STATIC_DATA = await res.json();
      console.log('📦 Static Database Loaded:', STATIC_DATA.people.length, 'people');
    }
  } catch (e) {
    console.warn('Could not load static_data.json:', e);
  }
}

// Monkey-patch window.fetch to provide offline/GitHub Pages backend simulation
const origFetch = window.fetch;
window.fetch = async function(resource, init) {
  const url = typeof resource === 'string' ? resource : resource.url;
  
  if (STATIC_DATA && url.startsWith('/api/')) {
    const u = new URL(url, window.location.href);
    const path = u.pathname;
    
    if (path === '/api/trees') {
      return new Response(JSON.stringify(STATIC_DATA.trees), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    
    if (path === '/api/tree') {
      const treeId = u.searchParams.get('id') || 'sigurjon';
      const people = STATIC_DATA.people.filter(p => p.tree_id === treeId);
      return new Response(JSON.stringify({ tree_id: treeId, people }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    
    if (path === '/api/person') {
      const personId = u.searchParams.get('id');
      const person = STATIC_DATA.people.find(p => p.id === personId);
      if (!person) {
        return new Response(JSON.stringify({ error: 'Not found' }), { status: 404 });
      }
      
      const personRels = STATIC_DATA.relations.filter(r => r.person_id === personId);
      const fatherRel = personRels.find(r => r.relation_type === 'father');
      const motherRel = personRels.find(r => r.relation_type === 'mother');
      const spouseRels = personRels.filter(r => r.relation_type === 'spouse');
      const childRels = personRels.filter(r => r.relation_type === 'child');
      
      const father = fatherRel ? STATIC_DATA.people.find(p => p.id === fatherRel.related_id) : null;
      const mother = motherRel ? STATIC_DATA.people.find(p => p.id === motherRel.related_id) : null;
      const spouse = spouseRels.map(r => STATIC_DATA.people.find(p => p.id === r.related_id)).filter(Boolean);
      const children = childRels.map(r => STATIC_DATA.people.find(p => p.id === r.related_id)).filter(Boolean);
      
      const sources = STATIC_DATA.sources.filter(s => s.person_id === personId);
      const suggestions = (STATIC_DATA.suggestions || []).filter(s => s.person_id === personId);
      
      return new Response(JSON.stringify({
        person,
        family: { father, mother, spouse, children },
        sources,
        suggestions
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }

    if (path === '/api/proxy_image') {
      const imgUrl = u.searchParams.get('url') || '';
      return new Response(null, { status: 302, headers: { 'Location': imgUrl } });
    }
  }
  
  return origFetch.apply(this, arguments);
};

// Auto-initialize when loaded
initStaticDatabase();
