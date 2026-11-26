from decimal import Decimal

import pytest

from pricewatch.price_parser import parse_price


@pytest.mark.parametrize(
    "text, expected",
    [
        # HR, DE, NL, ES – točka za tisućice, zarez za decimale
        ("1.299,99 €", "1299.99"),
        ("1.299,99 €", "1299.99"),
        ("€ 1.299,99", "1299.99"),
        ("19,99 €", "19.99"),
        ("1.299 €", "1299"),
        # FR, PL, CZ – razmak (često neprekidivi) za tisućice
        ("1 299,99 €", "1299.99"),
        ("1 299,99 €", "1299.99"),
        ("1 299,99 zł", "1299.99"),
        ("12 990 Kč", "12990"),
        ("12 990,- Kč", "12990"),
        # engleski zapis i format iz JSON-LD
        ("€1,299.99", "1299.99"),
        ("1299.99", "1299.99"),
        ("1299", "1299"),
        ("1.299.000,00", "1299000.00"),
        # tekst oko cijene
        ("Cijena: 899,00 EUR", "899.00"),
        ("Sada samo 49,9 €", "49.9"),
    ],
)
def test_parse_price_formats(text, expected):
    assert parse_price(text) == Decimal(expected)


def test_parse_price_accepts_numbers():
    assert parse_price(1299) == Decimal("1299")
    assert parse_price(19.99) == Decimal("19.99")


@pytest.mark.parametrize("value", [None, "", "Nije dostupno", True])
def test_parse_price_returns_none(value):
    assert parse_price(value) is None
