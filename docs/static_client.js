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

      if (path.endsWith('/api/notable_articles')) {
        const treeId = u.searchParams.get('tree_id') || 'loa';
        const treePeople = (data.people || []).filter(p => p.tree_id === treeId);
        const personMap = new Map(treePeople.map(p => [p.id, p]));
        
        const articles = [];
        (data.sources || []).forEach(s => {
          const p = personMap.get(s.person_id);
          if (p) {
            const title = s.title || '';
            if (title.includes('Tímarit') || title.includes('Mbl') || title.includes('DV') || title.includes('Samvinnan') || title.includes('Réttur') || title.includes('Sjómannadagsblaðið') || title.includes('Fréttablaðið') || s.link) {
              articles.push({
                id: s.id,
                person_id: s.person_id,
                name: p.name,
                birth_year: p.birth_year,
                death_year: p.death_year,
                title: s.title,
                snippet: s.snippet,
                link: s.link,
                image_url: s.image_url
              });
            }
          }
        });
        articles.sort((a, b) => ((parseInt(a.birth_year) || 9999) - (parseInt(b.birth_year) || 9999)) || (a.id - b.id));
        return new Response(JSON.stringify({ status: 'ok', articles }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (path.endsWith('/api/tree_stats')) {
        const treeId = u.searchParams.get('tree_id') || 'loa';
        const people = (data.people || []).filter(p => p.tree_id === treeId);
        const total_people = people.length;
        const males = people.filter(p => p.sex === 'M').length;
        const females = people.filter(p => p.sex === 'F').length;
        
        const birth_years = people.map(p => parseInt(p.birth_year)).filter(y => !isNaN(y) && y > 1000 && y < 2030);
        const earliest_birth = birth_years.length ? Math.min(...birth_years) : 0;
        const latest_birth = birth_years.length ? Math.max(...birth_years) : 0;
        
        const lifespans = [];
        people.forEach(p => {
          const by = parseInt(p.birth_year);
          const dy = parseInt(p.death_year);
          if (!isNaN(by) && !isNaN(dy) && dy >= by && (dy - by) <= 115) {
            lifespans.push({ name: p.name, birth: by, death: dy, age: dy - by });
          }
        });
        lifespans.sort((a, b) => b.age - a.age);
        const avg_lifespan = lifespans.length ? +(lifespans.reduce((s, x) => s + x.age, 0) / lifespans.length).toFixed(1) : 0;
        
        // Large families
        const childCountMap = new Map();
        (data.relations || []).forEach(r => {
          if (r.tree_id === treeId && r.relation_type === 'child') {
            childCountMap.set(r.person_id, (childCountMap.get(r.person_id) || 0) + 1);
          }
        });
        const personMap = new Map(people.map(p => [p.id, p]));
        const biggest_families = Array.from(childCountMap.entries())
          .map(([pid, cnt]) => {
            const p = personMap.get(pid);
            return p ? { parent_name: p.name, child_count: cnt } : null;
          })
          .filter(Boolean)
          .sort((a, b) => b.child_count - a.child_count)
          .slice(0, 5);

        // Name counts
        const mNames = {};
        const fNames = {};
        people.forEach(p => {
          const fn = (p.name || '').trim().split(' ')[0];
          if (fn) {
            if (p.sex === 'M') mNames[fn] = (mNames[fn] || 0) + 1;
            else if (p.sex === 'F') fNames[fn] = (fNames[fn] || 0) + 1;
          }
        });
        const top_male_names = Object.entries(mNames).sort((a, b) => b[1] - a[1]).slice(0, 5);
        const top_female_names = Object.entries(fNames).sort((a, b) => b[1] - a[1]).slice(0, 5);

        // Dates
        const MONTHS = {
          'jan': 'Janúar', 'feb': 'Febrúar', 'mar': 'Mars', 'apr': 'Apríl', 'maí': 'Maí', 'jún': 'Júní',
          'júl': 'Júlí', 'ágú': 'Ágúst', 'sep': 'September', 'okt': 'Október', 'nóv': 'Nóvember', 'des': 'Desember'
        };
        const birth_days = {};
        const death_days = {};
        const birth_months = {};
        const death_months = {};

        people.forEach(p => {
          const bd = (p.birth_date || '').toLowerCase();
          const dd = (p.death_date || '').toLowerCase();
          
          for (const [prefix, mName] of Object.entries(MONTHS)) {
            if (bd.includes(prefix)) {
              birth_months[mName] = (birth_months[mName] || 0) + 1;
              const match = bd.match(/(\d{1,2})\.?\s+/);
              if (match) {
                const dayKey = `${parseInt(match[1])}. ${mName}`;
                birth_days[dayKey] = (birth_days[dayKey] || 0) + 1;
              }
              break;
            }
          }
          for (const [prefix, mName] of Object.entries(MONTHS)) {
            if (dd.includes(prefix)) {
              death_months[mName] = (death_months[mName] || 0) + 1;
              const match = dd.match(/(\d{1,2})\.?\s+/);
              if (match) {
                const dayKey = `${parseInt(match[1])}. ${mName}`;
                death_days[dayKey] = (death_days[dayKey] || 0) + 1;
              }
              break;
            }
          }
        });

        const top_birth_days = Object.entries(birth_days).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([date, count]) => ({ date, count }));
        const top_death_days = Object.entries(death_days).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([date, count]) => ({ date, count }));
        const top_birth_months = Object.entries(birth_months).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([month, count]) => ({ month, count }));
        const top_death_months = Object.entries(death_months).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([month, count]) => ({ month, count }));

        return new Response(JSON.stringify({
          status: 'ok',
          total_people,
          males,
          females,
          earliest_birth,
          latest_birth,
          span_years: latest_birth - earliest_birth,
          avg_lifespan,
          oldest_people: lifespans.slice(0, 5),
          top_male_names,
          top_female_names,
          biggest_families,
          top_birth_months,
          top_death_months,
          top_birth_days,
          top_death_days
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (path.endsWith('/api/create_snapshot')) {
        const treeId = u.searchParams.get('tree_id') || 'loa';
        const tag = u.searchParams.get('tag') || 'snapshot';
        const desc = u.searchParams.get('description') || '';
        const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
        const newSnap = {
          id: Date.now(),
          tree_id: treeId,
          snapshot_tag: tag,
          description: desc,
          created_at: now
        };
        data.tree_snapshots = data.tree_snapshots || [];
        data.tree_snapshots.unshift(newSnap);
        return new Response(JSON.stringify({ status: 'ok', snapshot: newSnap }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (path.endsWith('/api/upload_screenshot')) {
        return new Response(JSON.stringify({ status: 'ok', message: 'Ábending skráð' }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (path.endsWith('/api/proxy_image')) {
        const imgUrl = u.searchParams.get('url') || '';
        return new Response(null, { status: 302, headers: { 'Location': imgUrl } });
      }
    }
  }
  
  return origFetch.apply(this, arguments);
};
