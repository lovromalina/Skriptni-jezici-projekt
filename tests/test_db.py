import sqlite3

import pytest

from pricewatch import db


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    db.init_db(c)
    yield c
    c.close()


def test_schema_creates_tables(conn):
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {
        "stores", "exchange_rates", "products", "listings", "price_observations",
        "promo_checks", "alerts", "notifications",
    } <= tables


def test_load_stores_is_idempotent(conn):
    n = db.load_stores(conn)
    db.load_stores(conn)
    count = conn.execute("SELECT COUNT(*) FROM stores").fetchone()[0]
    assert n == count >= 1


def test_stores_cover_multiple_countries_and_currencies(conn):
    db.load_stores(conn)
    countries = {r[0] for r in conn.execute("SELECT country FROM stores")}
    currencies = {r[0] for r in conn.execute("SELECT currency FROM stores")}
    assert len(countries) >= 3
    assert "EUR" in currencies and len(currencies) >= 2


def test_listing_requires_existing_store(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO listings (store_id, url) VALUES (999, 'https://x.hr/p')")


def test_invalid_promo_verdict_rejected(conn):
    db.load_stores(conn)
    conn.execute("INSERT INTO listings (store_id, url) VALUES (1, 'https://links.hr/p')")
    conn.execute("INSERT INTO price_observations (listing_id, price) VALUES (1, 99.99)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO promo_checks (observation_id, verdict) VALUES (1, 'NESTO')")
