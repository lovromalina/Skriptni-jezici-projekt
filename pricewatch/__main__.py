"""Naredbe: python -m pricewatch init-db"""

import argparse

from . import db


def main() -> None:
    parser = argparse.ArgumentParser(prog="pricewatch")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-db", help="kreira bazu i upisuje trgovine")
    p_init.add_argument("--db", default=str(db.DEFAULT_DB))

    args = parser.parse_args()

    if args.command == "init-db":
        conn = db.connect(args.db)
        db.init_db(conn)
        n = db.load_stores(conn)
        print(f"Baza spremna: {args.db} ({n} trgovina)")


if __name__ == "__main__":
    main()
