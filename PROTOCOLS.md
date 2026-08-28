# 📜 Saga Genealogy Engine — Master Protocols & Architecture

Skjal þetta skilgreinir opinberu verklagsreglurnar (**Protocols**) fyrir Saga ættfræðikerfið til að tryggja 100% nákvæmni, gæði og samræmi.

---

## 1. 🚀 INIT PROTOCOL (Upphafsvinnsla nýs trés)
*Keyrt þegar nýtt tré (t.d. GEDCOM eða stofnskrá) er flutt inn í kerfið.*

1. **Innskráð Íslendingabókarsannprófun (Ítrun 1):**
   * Tengjast viðkomandi aðgangi á Íslendingabók.is með Playwright vafra.
   * Sækja nákvæman fæðingardag, dánardag, fæðingarstað og dánarstað.
   * Sækja staðfestar sögulegar nótur (störf, búseta úr manntölum 1801–1930).
   * Sækja staðfestar opinberar prófílmyndir úr Íslendingabók.
2. **Tengslastilling & Samræming:**
   * Samræma fæðingar- og dánarár hjá öllum mökum, foreldrum og börnum.
   * Hreinsa út allar óviðkomandi heimildir (t.d. Tannlæknatal hjá bændum).
3. **Snjöll Vef- & Tímaritasannprófun (Ítrun 2):**
   * Leita að minningargreinum á Tímarit.is og Mbl með fullu samhengi (Nafn + Ártöl + Maki).
   * Google AI Search Grounding (Gemini API) til að koma í veg fyrir IP-blökkun.
4. **Master Sniðmát (Standard Markdown):**
   * # [Nafn]
   * ## 1. Yfirlit & Fjölskylduhagir
   * ## 2. Lífshlaup, Störf & Búseta
   * ## 3. Staðfestar heimildir
   * ## 4. Tímalína

---

## 2. 🔄 UPDATE PROTOCOL (Regluleg uppfærsla / Endurnýjun)
*Keyrt þegar nýjar greinar koma út, notandi bætir við upplýsingum eða smellir á „Endurgera samantekt“.*

1. **Varðveisla sögulegra gagna:**
   * Vernda allar handskráðar eða staðfestar Íslendingabókarnótur í kafla 2.
2. **Bein uppfletting á Tímarit.is / Minningar.is:**
   * Sækja nýjustu minningargreinar og tengja beint á frumheimildina.
3. **Sjálfvirk endursamstilling tölfræði:**
   * Uppfæra aldursmet, stærstu fjölskyldur og vinsælustu nöfn sjálfkrafa.

---

## 3. 🏗️ BUILD PROTOCOL (Stækkun trés & Leit að nýjum ættliðum)
*Keyrt þegar byrjað er á örfáum einstaklingum eða þegar óskað er eftir að stækka tréð aftur á bak eða fram á við.*

1. **Forfeðraleit (Ancestry Expansion):**
   * Rekja foreldra og forfeður kerfisbundið aftur í aldir í gegnum Íslendingabók.
2. **Afkomendaleit (Descendant Expansion):**
   * Fletta upp öllum börnum og mökum.
3. **Sjálfvirk samrunavörn (Deduplication Gatekeeper):**
   * Koma í veg fyrir að nafnamargbreytileiki (t.d. Sigurjón afi vs. Sigurjón sonarsonur) valdi árekstri í gagnagrunni.


---

---

## 📚 SKILGREINING Á DJÚPLEIT Í SAGA KERFINU

### 1. 🔍 DJÚPLEIT (Lög 1, 2 og 3 - Sjálfvirkt & Ókeypis með Playwright vafra):
* **Lög 1 (Íslendingabók.is):** Innskráður vafri sækir nákvæmar dagsetningar, fæðingarstaði, foreldra, maka, börn, manntalsfærslur (1801–1930) og búsetu.
* **Lög 2 (Menntun & Útskriftir):** Leit á Tímarit.is og skólablöðum að stúdentsprófi, háskólaprófi, sveinsprófi og brautskráningum.
* **Lög 3 (Minningargreinar & Tímarit):** Leit að minningargreinum á Mbl/DV, afmælisviðtölum og sögulegum greinum með beinum tenglum.

### 2. 🧠 DJÚPLEIT MEÐ AI GROUNDING (Lög 1, 2, 3 + 4 - Gemini API):
* Bætir við Google AI Grounding til að semja samfellda ævisögu þegar API lykill með Pay-As-You-Go er til staðar.