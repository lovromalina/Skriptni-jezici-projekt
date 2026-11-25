# Arhitektura i funkcionalna specifikacija

## 1. Pojmovi

- **Proizvod** – stvarni artikl neovisno o trgovini (npr. "Samsung Galaxy S24
  128 GB crni"). Identificira se EAN-om ili šifrom proizvođača.
- **Ponuda (listing)** – stranica tog proizvoda u jednoj trgovini, s vlastitim
  nazivom, opisom i cijenom. Jedan proizvod ima više ponuda.
- **Mjerenje** – jedno očitanje cijene ponude u određenom trenutku, u valuti
  trgovine i preračunato u eure.

Opseg: trgovine računala, računalnih komponenti i elektronike u državama EU
(trenutno HR, DE, NL, FR, ES, CZ, PL – vidi `config/trgovine.yaml`).

## 2. Moduli

```
            poveznica
                │
                ▼
 ┌───────────────────────────┐    ┌──────────────────────┐
 │ extractor                 │───▶│ matcher              │
 │ JSON-LD → OG → microdata  │    │ EAN → MPN → naziv    │
 │ → heuristika → selektori  │    │ (+ ručna potvrda)    │
 └───────────────────────────┘    └──────────┬───────────┘
                │                             │
                ▼                             ▼
 ┌──────────────────────────────────────────────────────┐
 │ baza (SQLite): stores, products, listings,           │
 │ price_observations, promo_checks, alerts, ...        │
 └──────────────────────────────────────────────────────┘
        ▲                  │                   │
        │                  ▼                   ▼
 ┌─────────────┐   ┌──────────────┐    ┌──────────────┐
 │ scheduler   │   │ promo_check  │───▶│ notifier     │
 │ (1–2× dnev.)│   │ 30 dana,     │    │ e-mail       │
 └─────────────┘   │ podizanje    │    └──────────────┘
                   └──────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ dashboard    │
                   │ (Streamlit)  │
                   └──────────────┘
```

## 3. Automatsko izdvajanje naziva i cijene

Korisnik unosi samo poveznicu. Extractor isprobava izvore redom i zaustavlja
se na prvom koji vrati valjanu cijenu:

1. **schema.org JSON-LD** – `<script type="application/ld+json">` s tipom
   `Product`; čitaju se `name`, `gtin13`/`gtin`, `mpn`, `sku`, `brand`,
   `offers.price`, `offers.priceCurrency`, `offers.availability`.
2. **OpenGraph / meta oznake** – `og:title`, `product:price:amount`,
   `product:price:currency`.
3. **Microdata** – elementi s `itemprop="name"`, `itemprop="price"`.
4. **Heuristika** – kandidati su tekstovi koji odgovaraju uzorku cijene
   (`1.299,99 €`, `€ 1299.99`); boduju se prema blizini naslova `<h1>`,
   veličini fonta / nazivu klase (`price`, `cijena`), te se odbacuju
   precrtane cijene (`<del>`, `<s>`, klase `old`, `regular`) koje se
   posebno bilježe kao **redovna cijena**.
5. **Ručni selektori** – samo ako sve navedeno ne uspije, iz
   `config/trgovine.yaml`.

Uz cijenu traži se i tekst deklarirane najniže cijene u 30 dana pomoću
regularnih izraza nad tekstom stranice. Izrazi su zadani po jeziku trgovine
(`lowest_30d_patterns` u `config/trgovine.yaml`), npr.
"Najniža cijena u posljednjih 30 dana", "Niedrigster Preis der letzten
30 Tage", "Najniższa cena z 30 dni".

**Formati brojeva** razlikuju se po državama (`1.299,99 €`, `1 299,99 zł`,
`1299,99 Kč`, `€1,299.99`), pa parser cijene uzima u obzir jezik trgovine i
simbol valute.

Svako mjerenje bilježi koja je metoda upotrijebljena (`extraction_method`),
čime se može izmjeriti uspješnost automatike po trgovinama.

## 4. Uparivanje istog proizvoda među trgovinama

Redoslijed pravila, od najpouzdanijeg:

| Korak | Pravilo | Pouzdanost |
|---|---|---|
| 1 | Isti EAN/GTIN | automatski prihvaćeno |
| 2 | Ista marka + šifra proizvođača (MPN) | automatski prihvaćeno |
| 3 | Sličnost normaliziranih naziva ≥ 0,90 i podudaranje ključnih atributa | prihvaćeno, označeno za provjeru |
| 4 | Sličnost 0,70 – 0,90 | prijedlog, korisnik potvrđuje |
| 5 | Sličnost < 0,70 | novi proizvod |

Kod računalne opreme EAN i MPN gotovo su uvijek dostupni i jednaki u svim
državama, pa se većina uparivanja rješava u koracima 1 i 2. Usporedba naziva
služi za trgovine koje te oznake ne objavljuju.

**Normalizacija naziva:** mala slova, uklanjanje dijakritika, uklanjanje
marketinških i opisnih riječi na svim jezicima trgovina ("akcija",
"Grafikkarte", "karta graficzna", "carte graphique", "+ poklon"), pri čemu
ostaju marka, model i tehnički atributi koji su jednaki u svim jezicima,
ujednačavanje jedinica
(`128GB` = `128 gb`), izdvajanje atributa (marka, model, kapacitet, RAM,
boja, veličina zaslona).

**Ključni atributi** (kapacitet, boja, model) moraju se podudarati – razlika u
njima isključuje uparivanje bez obzira na sličnost teksta (npr. 128 GB i
256 GB nisu isti artikl).

**Evaluacija:** za početni skup ručno se označi točno uparivanje te se
računaju preciznost i odziv algoritma.

## 5. Valute

Cijene u trgovinama izvan eurozone (CZK, PLN) preračunavaju se u eure po
dnevnom referentnom tečaju Europske središnje banke (tablica
`exchange_rates`), na dan mjerenja. Usporedba među trgovinama radi se u
eurima, a provjera akcija u izvornoj valuti trgovine, kako promjena tečaja
ne bi izgledala kao promjena cijene.

## 6. Provjera akcija

Pravilo (čl. 6.a Direktive 98/6/EZ, preneseno u zakonodavstvo svih država
članica): kod objave sniženja trgovac mora navesti najnižu cijenu koju je
primjenjivao u razdoblju od 30 dana prije sniženja. Budući da pravilo vrijedi
u cijelom EU, ista provjera primjenjuje se na sve trgovine.

**Prepoznavanje akcije:** postoji precrtana redovna cijena veća od trenutne,
ili je na stranici navedena najniža cijena u 30 dana, ili je trenutna cijena
pala za više od 5 % u odnosu na prethodno mjerenje.

**Provjere** (`t0` = prvo mjerenje akcijske cijene):

1. **Točnost deklarirane najniže cijene** –
   `naša_min = min(cijena u [t0 − 30 dana, t0))`.
   Ako je deklarirana cijena veća od `naša_min` za više od 0,01 €, oznaka
   `NETOCNA_NAJNIZA`.
2. **Podizanje cijene prije sniženja** – uspoređuje se medijan cijene u
   razdoblju `[t0 − 60, t0 − 14)` s najvišom cijenom u `[t0 − 14, t0)`.
   Ako je porast veći od 10 % i sniženje ne spušta cijenu značajno ispod
   ranijeg medijana, oznaka `PODIZANJE_PRIJE_AKCIJE`.
3. **Prikazani postotak popusta** – ako se popust računa od redovne cijene,
   a ne od najniže u 30 dana, bilježi se i "stvarni" popust.
4. Ako povijest pokriva manje od 30 dana, oznaka `NEDOVOLJNO_PODATAKA`.

Pragovi (14 dana, 10 %, 5 %) su parametri u konfiguraciji i odredit će se
na temelju prikupljenih podataka.

**Napomena:** zbog provjere od 30 dana prikupljanje mora početi što ranije,
kako bi do kraja projekta postojala dovoljna povijest.

## 7. Obavijesti

E-mail se šalje kad cijena proizvoda u bilo kojoj trgovini padne ispod
ciljane cijene korisnika. Sadrži:

- cijenu u svim trgovinama u kojima se proizvod prati, u eurima i izvornoj
  valuti (najpovoljnija prva),
- najnižu cijenu iz vlastite povijesti u zadnjih 30 i 90 dana,
- rezultat provjere akcije: ✅ vjerodostojna / ⚠️ netočna najniža cijena /
  ⚠️ cijena podignuta prije sniženja / ℹ️ nedovoljno podataka.

Ista obavijest za isti proizvod i cijenu ne šalje se ponovno.

## 8. Model podataka

Shema je u [`db/schema.sql`](../db/schema.sql). Tablice:

| Tablica | Sadržaj |
|---|---|
| `stores` | trgovine (naziv, domena, država, valuta, jezik, treba li JavaScript) |
| `exchange_rates` | dnevni tečajevi ECB-a |
| `products` | stvarni proizvodi (naziv, marka, EAN, MPN, kategorija) |
| `listings` | ponude u trgovinama, veza na proizvod i način uparivanja |
| `price_observations` | mjerenja: cijena, redovna cijena, deklarirana najniža u 30 dana, dostupnost |
| `promo_checks` | rezultati provjere akcija |
| `alerts` | ciljane cijene korisnika |
| `notifications` | poslane obavijesti (sprječava duplikate) |

## 9. Rizici

| Rizik | Ublažavanje |
|---|---|
| Promjena HTML-a trgovine | izdvajanje preko strukturiranih podataka (JSON-LD) koji se rjeđe mijenjaju; bilježenje neuspjelih dohvata |
| Pogrešno uparivanje | stroga pravila za ključne atribute, ručna potvrda nesigurnih slučajeva, evaluacija na označenom skupu |
| Nedovoljna povijest za provjeru 30 dana | rani početak prikupljanja, oznaka `NEDOVOLJNO_PODATAKA` |
| Anti-bot zaštita | 1–2 dohvata dnevno, nasumične pauze, poštivanje `robots.txt` |
| Cijene učitane JavaScriptom | Playwright samo za trgovine označene s `requires_js` |
| Stranica prikazuje drugu cijenu ovisno o državi posjetitelja | dohvat uvijek s istom postavkom jezika/države, bilježenje valute sa stranice |
| Različite formulacije najniže cijene na jezicima | izrazi po jeziku u konfiguraciji, dopunjavaju se iz stvarnih stranica |
