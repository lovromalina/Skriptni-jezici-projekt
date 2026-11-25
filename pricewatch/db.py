"""Inicijalizacija baze i punjenje trgovina iz konfiguracije."""

import sqlite3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "db" / "schema.sql"
STORES_CONFIG = ROOT / "config" / "trgovine.yaml"
DEFAULT_DB = ROOT / "data" / "pricewatch.db"


def connect(db_path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def load_stores(conn: sqlite3.Connection, config_path: Path = STORES_CONFIG) -> int:
    """Upisuje trgovine iz YAML konfiguracije; postojeće ažurira. Vraća broj trgovina."""
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    stores = data.get("stores", [])
    for s in stores:
        conn.execute(
            """
            INSERT INTO stores (name, domain, country, currency, language, requires_js)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                name = excluded.name,
                country = excluded.country,
                currency = excluded.currency,
                language = excluded.language,
                requires_js = excluded.requires_js
            """,
            (
                s["name"],
                s["domain"],
                s["country"],
                s.get("currency", "EUR"),
                s["language"],
                int(bool(s.get("requires_js", False))),
            ),
        )
    conn.commit()
    return len(stores)
