# 📜 Saga Genealogy Engine — Master Protocols & Architecture

Skjal þetta skilgreinir opinberu verklagsreglurnar (**Protocols**) fyrir Saga ættfræðikerfið til að tryggja 100% nákvæmni, gæði og samræmi. Hvert nýtt tré fer sjálfkrafa í gegnum þennan feril svo engin handavinna sé nauðsynleg.

---

## 1. 🚀 INIT PROTOCOL (Upphafsvinnsla nýs trés)
*Keyrt sjálfkrafa þegar nýtt tré (t.d. GEDCOM eða stofnskrá) er flutt inn í kerfið.*

### 1.1 Innskráð Íslendingabókarsannprófun (Lög 1):
* Tengjast viðkomandi aðgangi á Íslendingabók.is með Playwright vafra.
* Sækja nákvæman fæðingardag, dánardag, fæðingarstað og dánarstað.
* Sækja staðfestar sögulegar nótur (störf, búseta úr manntölum 1801–1930).
* Sækja staðfestar opinberar prófílmyndir úr Íslendingabók.

### 1.2 Sjálfvirk Nafna- og Ættartengslaleiðrétting (Automatic Patronymic & Kinship Repair):
* **Föðurnafnaleiðrétting:** Ef einstaklingur er aðeins með eiginnafn í innfluttri skrá (t.d. „Jónína“ í stað „Jónína Loftsdóttir“), sækir kerfið fullt nafn sjálfkrafa úr fjölskyldufærslu foreldris á Íslendingabók.
* **Hálfsystkini & Stjúpfjölskyldur:** Aðgreina rétt líffræðilega foreldra og stjúpforeldra út frá giftingardagsetningum og skráðum foreldrum á Íslendingabók (t.d. Sveinn Unnsteinn vs. Loftur Jóhannsson).
* **Fjölskyldustækkun:** Bæta við líffræðilegum foreldrum eða börnum sem vantaði í upprunalega innflutninginn.

### 1.3 Snjöll Mennta- & Tímaritasannprófun (Lög 2 & 3):
* Leita að staðfestum útskriftum (stúdentspróf, HÍ, KHÍ, BA/BSc, meistarapróf).
* Leita að minningargreinum á Tímarit.is og Mbl með fullu samhengi (Nafn + Ártöl + Maki/Foreldrar).
* Útiloka sjálfkrafa nafnarugling og óviðkomandi fréttir (t.d. brotamál nafna).

### 1.4 Master Sniðmát (Standard Markdown):
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

---

## 📚 SKILGREINING Á DJÚPLEIT Í SAGA KERFINU

### 1. 🔍 DJÚPLEIT (Lög 1, 2 og 3 - Sjálfvirkt & Ókeypis):
* **Lög 1 (Íslendingabók.is):** Innskráður vafri sækir nákvæmar dagsetningar, fæðingarstaði, foreldra, maka, börn, manntöl (1801–1930) og búsetu. Laga nöfn og hálfsystkini sjálfkrafa.
* **Lög 2 (Menntun & Útskriftir á Tímarit.is):** Sannprófa stúdentspróf, háskólapróf og sérfræðiréttindi.
* **Lög 3 (Sögulegar greinar & Minningargreinar á Tímarit.is):** Sækja minningargreinar og viðtöl, útbúa beina tengla á tímaritasíður.

### 2. 🤖 DJÚPLEIT MEÐ AI GROUNDING (Lög 1, 2, 3 og 4 - Krefst Gemini API Quota):
* **Lög 4 (Google AI Grounding):** Dregur saman heildstæða ævisögu úr öllum heimildum samtímis með Gemini 2.5 Flash.
