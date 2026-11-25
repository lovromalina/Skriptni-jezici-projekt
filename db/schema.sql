-- Shema baze podataka (SQLite)
PRAGMA foreign_keys = ON;

-- Trgovine
CREATE TABLE IF NOT EXISTS stores (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    domain        TEXT NOT NULL UNIQUE,
    country       TEXT NOT NULL,                   -- ISO 3166-1, npr. 'DE'
    currency      TEXT NOT NULL DEFAULT 'EUR',     -- ISO 4217, npr. 'PLN'
    language      TEXT NOT NULL,                   -- ISO 639-1, npr. 'pl'
    requires_js   INTEGER NOT NULL DEFAULT 0,      -- 1 = dohvat Playwrightom
    active        INTEGER NOT NULL DEFAULT 1
);

-- Dnevni referentni tečajevi ECB-a (1 EUR = rate jedinica valute)
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_date     TEXT NOT NULL,                   -- YYYY-MM-DD
    currency      TEXT NOT NULL,
    rate          NUMERIC NOT NULL,
    PRIMARY KEY (rate_date, currency)
);

-- Stvarni proizvod, neovisno o trgovini
CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,                   -- kanonski naziv
    brand         TEXT,
    ean           TEXT UNIQUE,
    mpn           TEXT,                            -- šifra proizvođača
    category      TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_products_brand_mpn ON products(brand, mpn);

-- Ponuda proizvoda u jednoj trgovini
CREATE TABLE IF NOT EXISTS listings (
    id                 INTEGER PRIMARY KEY,
    store_id           INTEGER NOT NULL REFERENCES stores(id),
    product_id         INTEGER REFERENCES products(id),   -- NULL dok nije upareno
    url                TEXT NOT NULL UNIQUE,
    title_raw          TEXT,                              -- naziv kako ga navodi trgovina
    ean                TEXT,
    mpn                TEXT,
    sku                TEXT,                              -- interna šifra trgovine
    match_method       TEXT CHECK (match_method IN ('ean', 'mpn', 'name', 'manual')),
    match_score        REAL,                              -- 0..1 za uparivanje po nazivu
    match_confirmed    INTEGER NOT NULL DEFAULT 0,
    active             INTEGER NOT NULL DEFAULT 1,
    created_at         TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_listings_product ON listings(product_id);

-- Pojedinačno mjerenje cijene
CREATE TABLE IF NOT EXISTS price_observations (
    id                    INTEGER PRIMARY KEY,
    listing_id            INTEGER NOT NULL REFERENCES listings(id),
    observed_at           TEXT NOT NULL DEFAULT (datetime('now')),
    price                 NUMERIC NOT NULL,               -- trenutna (prodajna) cijena u valuti trgovine
    regular_price         NUMERIC,                        -- precrtana redovna cijena, ako postoji
    declared_lowest_30d   NUMERIC,                        -- najniža cijena u 30 dana prema trgovini
    currency              TEXT NOT NULL DEFAULT 'EUR',
    price_eur             NUMERIC,                        -- preračunato po tečaju ECB-a na dan mjerenja
    in_stock             INTEGER,
    extraction_method     TEXT CHECK (extraction_method IN
                              ('jsonld', 'opengraph', 'microdata', 'heuristic', 'selector')),
    raw                   TEXT                            -- izvorni izdvojeni podaci (JSON) za provjeru
);
CREATE INDEX IF NOT EXISTS idx_obs_listing_time ON price_observations(listing_id, observed_at);

-- Napomena: provjera akcija uvijek se radi u izvornoj valuti trgovine (price),
-- a usporedba među trgovinama u eurima (price_eur).

-- Rezultat provjere akcije
CREATE TABLE IF NOT EXISTS promo_checks (
    id                    INTEGER PRIMARY KEY,
    observation_id        INTEGER NOT NULL UNIQUE REFERENCES price_observations(id),
    our_lowest_30d        NUMERIC,
    declared_lowest_30d   NUMERIC,
    median_before         NUMERIC,                        -- medijan u [t0-60, t0-14)
    max_before            NUMERIC,                        -- najviša cijena u [t0-14, t0)
    verdict               TEXT NOT NULL CHECK (verdict IN
                              ('OK', 'NETOCNA_NAJNIZA', 'PODIZANJE_PRIJE_AKCIJE',
                               'NEDOVOLJNO_PODATAKA')),
    details               TEXT,
    checked_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Ciljane cijene korisnika
CREATE TABLE IF NOT EXISTS alerts (
    id             INTEGER PRIMARY KEY,
    product_id     INTEGER NOT NULL REFERENCES products(id),
    email          TEXT NOT NULL,
    target_price   NUMERIC NOT NULL,
    active         INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Poslane obavijesti (sprječava ponovno slanje iste obavijesti)
CREATE TABLE IF NOT EXISTS notifications (
    id              INTEGER PRIMARY KEY,
    alert_id        INTEGER NOT NULL REFERENCES alerts(id),
    observation_id  INTEGER NOT NULL REFERENCES price_observations(id),
    sent_at         TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (alert_id, observation_id)
);
