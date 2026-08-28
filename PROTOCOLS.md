# 📜 Saga Genealogy Engine — Master Protocols & Architecture

Skjal þetta skilgreinir opinberu verklagsreglurnar (**Protocols**) fyrir Saga ættfræðikerfið til að tryggja 100% nákvæmni, gæði og samræmi. Hvert nýtt tré fer sjálfkrafa í gegnum þennan feril svo engin handavinna sé nauðsynleg.

---

## 1. 🚀 INIT PROTOCOL (Upphafsvinnsla nýs trés)
*Keyrt sjálfkrafa þegar nýtt tré (t.d. GEDCOM eða stofnskrá) er flutt inn í kerfið.*

### 1.1 Íslensk stafsetningar- & Nafnahreinsun (Icelandic Orthography Normalizer):
* **Hreinsa danskar/GEDCOM afbakanir:**
  * Breyta sjálfkrafa öllum dönskum eða vanskrifuðum endingum: `Arnadr` / `Arnasdatter` ➔ `Árnadóttir`, `Jonsdr` ➔ `Jónsdóttir`, `Gisladottir` ➔ `Gísladóttir`.
  * Bæta við íslenskum broddstöfum: `Jon` ➔ `Jón`, `Arni` ➔ `Árni`, `Gudrun` ➔ `Guðrún`, `Gudbjorg` ➔ `Guðbjörg`, `Gisli` ➔ `Gísli`, `Thuridur` ➔ `Þuríður`.
* **Stök nöfn og vanskráðir forfeður (Single-Name Ancestor Resolution):**
  * Ef einstaklingur kemur inn aðeins með fornafn eða stakt orð án ártala (t.d. „Sigurpáll“ eða „Rósa“), flettir kerfið sjálfkrafa upp barni þeirra á Íslendingabók.
  * Þaðan sækir kerfið fullt nafn (*Sigurpáll Þorsteinsson*, *Rósa Jónsdóttir*), nákvæmar dagsetningar, fæðingarstaði og manntalsstörf.

### 1.2 Innskráð Íslendingabókarsannprófun (Lög 1):
* Tengjast viðkomandi aðgangi á Íslendingabók.is með Playwright vafra.
* Sækja nákvæman fæðingardag, dánardag, fæðingarstað og dánarstað.
* Sækja staðfestar sögulegar nótur (störf, búseta úr manntölum 1801–1930).
* Sækja staðfestar opinberar prófílmyndir úr Íslendingabók.
* **Varðveisla frumheimilda:** Vista nákvæman lista Íslendingabókar í `ib_sources` dálkinn í gagnagrunninum.

### 1.3 Sjálfvirk Alnafnavörn & Fjölskyldutengsl (Namesake Isolation & Kinship):
* **Alnafnavörn milli kynslóða (Namesake Isolation Guard):**
  * Þegar afi/langafi og barnabarn eru alnafnar (t.d. *Runólfur Sigtryggsson f. 1894* vs. *Runólfur Sigtryggsson f. 1955*):
  * Bannað er að yfirskrifa gögn eða ævisögu milli þeirra.
  * Hver einstaklingur er eingöngu uppfærður eftir sínu eigin `id` og staðfestum ártölum.
* **Hálfsystkini & Stjúpfjölskyldur:** Aðgreina rétt líffræðilega foreldra og stjúpforeldra út frá giftingardagsetningum og skráðum foreldrum á Íslendingabók (t.d. Sveinn Unnsteinn vs. Loftur Jóhannsson).
* **Fjölskyldustækkun:** Bæta við líffræðilegum foreldrum eða börnum sem vantaði í upprunalega innflutninginn.

### 1.4 Snjöll Mennta- & Tímaritasannprófun (Lög 2 & 3):
* **Lifandi einstaklingar (Living Person Obituary Guard):**
  * **STRÖNG REGLA:** Aldrei má tengja „Minningargrein“ við einstakling sem er á lífi (`death_year` er tómt).
  * Fyrir lifandi fólk er eingöngu leitað að staðfestum brautskráningum/útskriftum (stúdentspróf, HÍ, KHÍ, meistarapróf).
* Leita að minningargreinum á Tímarit.is og Mbl **eingöngu fyrir látna einstaklinga** með fullu samhengi (Nafn + Ártöl + Maki/Foreldrar).
* **Deduplication Guard:** Koma í veg fyrir að sama heimild bætist við oftar en einu sinni.
* Útiloka sjálfkrafa nafnarugling og óviðkomandi fréttir (t.d. brotamál eða handahófskennd brot nafna).

### 1.5 Master Sniðmát (Standard Markdown):
Fyrir hvern einasta einstakling er byggt staðlað spjald:
* `# [Fullt Nafn]`
* `## 1. Yfirlit & Fjölskylduhagir`
* `## 2. Lífshlaup, Menntun & Búseta`
* `## 3. Staðfestar heimildir`
* `## 4. Tímalína`

---

## 2. 🔄 UPDATE PROTOCOL (Regluleg uppfærsla / Endurnýjun)
*Keyrt þegar nýjar greinar koma út, notandi bætir við upplýsingum eða smellir á „Endurgera samantekt“.*

1. **Varðveisla sögulegra gagna:** Vernda allar handskráðar eða staðfestar nótur í kafla 2.
2. **Bein uppfletting á Tímarit.is / Minningar.is:** Sækja nýjustu minningargreinar og tengja beint á frumheimildina.
3. **Sjálfvirk endursamstilling tölfræði:** Uppfæra aldursmet, stærstu fjölskyldur og vinsælustu nöfn sjálfkrafa.

---

## 3. 🏗️ BUILD PROTOCOL (Stækkun trés & Leit að nýjum ættliðum)
*Keyrt þegar stækka á tréð aftur á bak eða fram á við.*

1. **Forfeðraleit (Ancestry Expansion):** Rekja foreldra og forfeður kerfisbundið aftur í aldir í gegnum Íslendingabók.
2. **Afkomendaleit (Descendant Expansion):** Fletta upp öllum börnum og mökum.
3. **Sjálfvirk samrunavörn (Deduplication Gatekeeper):** Koma í veg fyrir að nafnamargbreytileiki valdi árekstri í gagnagrunni.
