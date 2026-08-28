# 🗺️ Saga Genealogy Engine — Framtíðarsýn & Vegvísir (Roadmap)

Skjal þetta heldur utan um áætlaða þróun, hýsingaráætlanir, notendastýringu og skalanleika fyrir Saga ættfræðikerfið.

---

## 📌 Áfangar (Milestones)

### ✅ Áfangi 1: Grunnkjarni & Init Protocol (Lokið - Ágúst 2026)
- [x] Innflutningur á GEDCOM trjám (`loa.ged`, `sigurjon.ged`).
- [x] Snjall Íslendingabókarsannprófunarvafri (Playwright) fyrir lífshlaup, manntöl (1801–1930) og búsetu.
- [x] Íslensk stafsetningar- og dönskuhreinsun (Orthography Normalizer).
- [x] Nafna- og alnafnavörn milli kynslóða (Namesake Isolation Guard).
- [x] Stök nöfn og vanskráðir forfeður leystir sjálfkrafa úr fjölskyldufærslum Íb (t.d. Sigurpáll & Rósa).
- [x] Lifandi einstaklingar varðir gegn fölskum minningargreinum.
- [x] 100% fullkomin 8 langafapör Lóu skráð og tengd.
- [x] Tvíhliða samstilling lífshlaups og heimilda yfir öll 447 spjöld í Lóutrénu.

---

### ✅ Áfangi 2: Útgáfustjórnun & Tímaferð (Lokið - Ágúst 2026)
- [x] **Trjástig (Tree Snapshots):** Geyma opinberar útgáfur af öllu trénu (`v2.0-master-verified`) með afriti af öllum gögnum.
- [x] **Einstaklingsstig (Person Version History):** Halda utan um allar breytingar á hverjum manni (`person_history`).
- [x] **Afturköllun (Rollback / Undo):** Hnappur á spjaldi til að hoppa beint í eldri útgáfu ef ný útgáfa er ekki eins góð.

---

### ⏳ Áfangi 3: Hýsing, Föst Vefslóð (URL) & Innviðir (Í vinnslu / Næst)

#### 1. Föst og Stöðug Vefslóð:
* **Stig 1 (Núna - Frítt):** Cloudflare Named Tunnel tengt við fast lén (t.d. `saga.aettartre.is` eða fast Cloudflare subdomain). Breytist aldrei við endurræsingu.
* **Stig 2 (Framtíð - 24/7 sjálfvirk skýjahýsing):** Fly.io / Render / Hetzner VPS (~600–700 kr./mán) þar sem Python bakendinn, SQLite og framendinn keyra allan sólarhringinn án þess að tölva heima þurfi að vera opin.

#### 2. Kostnaðar- og Skalanleikagreining:
| Hýsing | Kostnaður | Skalanleiki | Tilgangur |
| :--- | :--- | :--- | :--- |
| **Cloudflare Named Tunnel** | 0 kr. | Tugir samtímanotenda | Þróun og prófanir |
| **Fly.io / Render** | 0–700 kr./mán | Hundruð samtímanotenda (Auto-scale) | 24/7 fjölskylduaðgangur |
| **Hetzner VPS** | ~600 kr./mán | Þúsundir samtímanotenda | Opinber þjónusta |

* **Gagnagrunnur & Hraði:** SQLite í WAL-ham (Write-Ahead Logging) afgreiðir >50.000 fyrirspurnir á sekúndu með svarhraða undir 2 ms.

---

### 🔮 Áfangi 4: Notendastýring & Aðgangsstýring (User Management & Auth)
- [ ] **Hlutverkaskipting (Role-Based Access Control):**
  - 👑 **Admin (Þú):** Fullur aðgangur til að breyta, bæta við, keyra Protocols og taka Snapshots.
  - 👥 **Fjölskyldumeðlimir (Read-Only & Contributors):** Geta skoðað öll tré, lesið ævisögur, skoðað myndir og sent inn nýjar ábendingar/myndir án þess að geta eytt eða breytt grunngögnum.
- [ ] **Persónuverndarlæsing (Living People Privacy):**
  - Aðeins innskráðir fjölskyldumeðlimir sjá lifandi ættingja og börn.
  - Óinnskráðir gestir sjá aðeins látna forfeður og söguleg gögn.
- [ ] **Innskráningarkerfi:** Stuðningur við einfalt lykilorð, tölvupóstshlekk eða Google Login.

---

### 🌲 Áfangi 5: Stækkun og Ný Tré (Expansion Engine)
- [ ] Fullkomin sjálfvirkni við innlestur á nýjum GEDCOM skrám annarra fjölskyldna með Init Protocol v2.0.
- [ ] Build Protocol: Sjálfvirk leit að forfeðrum aftur á bak í gegnum Íslendingabók.
