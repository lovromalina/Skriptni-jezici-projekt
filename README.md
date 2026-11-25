# Sustav za usporedbu i praćenje cijena računalne opreme u europskim trgovinama

Alat koji isti proizvod prati u web trgovinama računala, računalnih komponenti
i elektronike u više država EU, prepoznaje da je riječ o istom artiklu iako se
naziv i opis razlikuju (i pisani su na različitim jezicima), uspoređuje cijene
preračunate u eure, bilježi povijest cijena
i provjerava jesu li akcije u skladu s pravilom o najnižoj cijeni u zadnjih
30 dana (Direktiva 98/6/EZ, čl. 6.a, uveden Direktivom (EU) 2019/2161).

## Po čemu se razlikuje od običnog "price trackera"

| Uobičajeni tracker | Ovaj projekt |
|---|---|
| Jedan URL = jedan proizvod | Jedan proizvod = više ponuda u različitim trgovinama |
| Jedna trgovina ili jedna država | Trgovine iz više država EU, različiti jezici i valute (EUR, CZK, PLN) |
| Selektori se ručno upisuju za svaku trgovinu | Korisnik upiše samo poveznicu, alat sam pronalazi naziv i cijenu |
| Obavijest kad cijena padne ispod praga | Obavijest uz usporedbu trgovina i ocjenu vjerodostojnosti akcije |
| Nema analize akcija | Provjera najniže cijene u 30 dana i otkrivanje podizanja cijene prije sniženja |

## Opseg praćenja

Kategorije: **računala, računalne komponente i elektronika** – procesori,
grafičke kartice, SSD diskovi, RAM, monitori, laptopi, periferija.
Ovi artikli prodaju se u cijeloj Europi pod istom oznakom proizvođača i istim
EAN-om, pa se mogu pouzdano upariti među trgovinama unatoč različitim jezicima
naziva i opisa.

Trgovine (početni skup, definiran u `config/trgovine.yaml`):

| Država | Trgovina | Valuta | Jezik |
|---|---|---|---|
| Hrvatska | Links (links.hr) | EUR | hr |
| Hrvatska | Instar informatika (instar-informatika.hr) | EUR | hr |
| Njemačka | Alternate (alternate.de) | EUR | de |
| Nizozemska | Megekko (megekko.nl) | EUR | nl |
| Francuska | LDLC (ldlc.com) | EUR | fr |
| Španjolska | PcComponentes (pccomponentes.com) | EUR | es |
| Češka | Alza (alza.cz) | CZK | cs |
| Poljska | x-kom (x-kom.pl) | PLN | pl |

Trgovine na kojima se u fazi 2 pokaže da dohvat nije moguć (blokada, CAPTCHA)
zamijenit će se drugom trgovinom iz iste države.

Početni skup od 20 do 30 proizvoda koji se nalaze u barem četiri od navedenih
trgovina bit će definiran u fazi 2 (`config/proizvodi.yaml`). Prate se cijene
s PDV-om, bez troškova dostave.

## Ključne funkcionalnosti

1. **Automatsko izdvajanje podataka iz poveznice** – redom se pokušavaju
   schema.org JSON-LD (`Product`/`Offer`), OpenGraph meta oznake, microdata
   (`itemprop="price"`) i heuristika nad HTML-om. Ručni selektori ostaju samo
   kao rezervna opcija za trgovine na kojima automatika ne uspije.
2. **Uparivanje istog proizvoda** – EAN/GTIN → šifra proizvođača (MPN) →
   usporedba normaliziranih naziva (marka, model, kapacitet, boja) uz prag
   sličnosti. Nesigurna uparivanja korisnik potvrđuje ručno.
3. **Povijest i usporedba cijena** – graf kretanja cijene istog proizvoda u
   svim trgovinama, preračunato u eure po dnevnom tečaju ECB-a, i trenutno
   najpovoljnija ponuda u Europi.
4. **Provjera akcija** – usporedba deklarirane "najniže cijene u 30 dana" s
   vlastitom poviješću te otkrivanje podizanja cijene neposredno prije sniženja.
5. **E-mail obavijesti** – pri postizanju ciljane cijene u bilo kojoj
   trgovini, s oznakom je li akcija vjerodostojna.

Detaljna specifikacija: [`docs/ARHITEKTURA.md`](docs/ARHITEKTURA.md).

## Tehnologije

Python 3.11+, Requests + BeautifulSoup (Playwright za stranice koje zahtijevaju
JavaScript), SQLite, APScheduler, Streamlit, SMTP, Docker.

## Pokretanje (trenutno stanje)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pricewatch init-db     # kreira data/pricewatch.db iz db/schema.sql
python -m pytest
```

## Plan rada

| Faza | Sadržaj | Status |
|---|---|---|
| 1 | Specifikacija, model podataka, postavka okruženja | u tijeku |
| 2 | Automatsko izdvajanje naziva i cijene, prikupljanje i pohrana | – |
| 3 | Uparivanje proizvoda među trgovinama | – |
| 4 | Provjera akcija (30 dana, podizanje prije sniženja) | – |
| 5 | Dashboard s usporedbom i grafovima | – |
| 6 | Obavijesti, testiranje, Docker | – |
