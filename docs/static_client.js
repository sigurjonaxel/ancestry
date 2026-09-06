// Standalone GitHub Pages Client Adapter
// Intercepts /api/ calls and serves directly from static_data.json in memory!

let STATIC_DATA = null;
let staticDataPromise = null;

function getStaticData() {
  if (!staticDataPromise) {
    staticDataPromise = fetch('static_data.json?v=' + Date.now(), { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        STATIC_DATA = data;
        console.log('📦 Static Database Loaded:', STATIC_DATA.people.length, 'people');
        return data;
      })
      .catch(e => {
        console.warn('Could not load static_data.json:', e);
        return null;
      });
  }
  return staticDataPromise;
}

// Preload immediately
getStaticData();

// Monkey-patch window.fetch to provide offline/GitHub Pages backend simulation
const origFetch = window.fetch;
window.fetch = async function(resource, init) {
  const url = typeof resource === 'string' ? resource : (resource && resource.url ? resource.url : '');
  
  if (url && (url.startsWith('/api/') || url.includes('/api/'))) {
    const data = STATIC_DATA || await getStaticData();
    if (data) {
      const u = new URL(url, window.location.href);
      const path = u.pathname;
      
      if (path.endsWith('/api/trees')) {
        return new Response(JSON.stringify(data.trees), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      
      if (path.endsWith('/api/tree')) {
        const treeId = u.searchParams.get('id') || 'sigurjon';
        const people = data.people.filter(p => p.tree_id === treeId);
        return new Response(JSON.stringify({ tree_id: treeId, people }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      
      if (path.endsWith('/api/person')) {
        const personId = u.searchParams.get('id');
        const person = data.people.find(p => p.id === personId);
        if (!person) {
          return new Response(JSON.stringify({ error: 'Not found' }), { status: 404 });
        }
        
        const personRels = data.relations.filter(r => r.person_id === personId);
        const fatherRel = personRels.find(r => r.relation_type === 'father');
        const motherRel = personRels.find(r => r.relation_type === 'mother');
        const spouseRels = personRels.filter(r => r.relation_type === 'spouse');
        const childRels = personRels.filter(r => r.relation_type === 'child');
        
        const father = fatherRel ? data.people.find(p => p.id === fatherRel.related_id) : null;
        const mother = motherRel ? data.people.find(p => p.id === motherRel.related_id) : null;
        const spouse = spouseRels.map(r => data.people.find(p => p.id === r.related_id)).filter(Boolean);
        const children = childRels.map(r => data.people.find(p => p.id === r.related_id)).filter(Boolean);
        
        const sources = data.sources.filter(s => s.person_id === personId);
        const suggestions = (data.suggestions || []).filter(s => s.person_id === personId);
        
        return new Response(JSON.stringify({
          person,
          family: { father, mother, spouse, children },
          sources,
          suggestions
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (path.endsWith('/api/person_history')) {
        const personId = (u.searchParams.get('person_id') || '').replace(/@/g, '');
        const history = (data.person_history || []).filter(h => h.person_id === personId || h.person_id === `@${personId}@`);
        history.sort((a, b) => (b.version_num || 0) - (a.version_num || 0));
        return new Response(JSON.stringify({ status: 'ok', history }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (path.endsWith('/api/tree_snapshots')) {
        const treeId = u.searchParams.get('tree_id') || 'loa';
        const snapshots = (data.tree_snapshots || []).filter(sn => sn.tree_id === treeId);
        return new Response(JSON.stringify({ status: 'ok', snapshots }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (path.endsWith('/api/proxy_image')) {
        const imgUrl = u.searchParams.get('url') || '';
        return new Response(null, { status: 302, headers: { 'Location': imgUrl } });
      }
    }
  }
  
  return origFetch.apply(this, arguments);
};
