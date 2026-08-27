import re

# Let's inspect app.js and ensure renderInteractiveTree is cleanly called without any infinite promise/async crash

with open("app.js", "r", encoding="utf-8") as f:
    js = f.read()

# Check if there is an infinite wrapper on renderPersonProfile
# We will directly call renderInteractiveTree() inside renderPersonProfile, without monkey-patching!

clean_render_call = '''  // Confirmed Sources Gallery
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
}'''

js = js.replace('''  // Confirmed Sources Gallery
  renderConfirmedSources(sources);
  
  // AI Suggestions Section
  renderAISuggestions(suggestions, p.id);
  
  lucide.createIcons();
}''', clean_render_call)

# Remove any old monkey-patching at the bottom
js = re.sub(r'const origRenderPersonProfile = renderPersonProfile;[\s\S]*?renderInteractiveTree\(\);[\s\S]*?};', '', js)

with open("app.js", "w", encoding="utf-8") as f:
    f.write(js)

print("✓ Lagfærði kallið í renderInteractiveTree svo það festist aldrei í bið!")
