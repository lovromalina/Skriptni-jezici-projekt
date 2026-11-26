"""Izdvajanje podataka o proizvodu iz schema.org JSON-LD oznaka na stranici.

Većina web trgovina u <script type="application/ld+json"> objavljuje podatke
o proizvodu (naziv, EAN, šifru proizvođača, cijenu) za tražilice. To je
najpouzdaniji izvor jer se rijetko mijenja kad trgovina promijeni izgled stranice.
"""

import json

from bs4 import BeautifulSoup

from .price_parser import parse_price

_GTIN_KEYS = ("gtin13", "gtin", "gtin14", "gtin12", "gtin8", "ean")


def extract_jsonld(html: str) -> dict | None:
    """Vraća podatke o prvom proizvodu (@type Product) iz JSON-LD-a ili None.

    Rezultat:
        {"name", "brand", "ean", "mpn", "sku", "price", "currency", "in_stock"}
    Polja koja stranica ne navodi imaju vrijednost None.
    """
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue  # neke trgovine imaju neispravan JSON – preskoči taj blok

        product = _find_product(data)
        if product is not None:
            return _to_result(product)

    return None


def _find_product(data):
    """Rekurzivno traži objekt tipa Product (može biti u listi ili u @graph)."""
    if isinstance(data, list):
        for item in data:
            found = _find_product(item)
            if found is not None:
                return found
        return None

    if not isinstance(data, dict):
        return None

    types = data.get("@type", [])
    if isinstance(types, str):
        types = [types]
    if "Product" in types or "ProductGroup" in types:
        return data

    for key in ("@graph", "mainEntity", "itemListElement"):
        if key in data:
            found = _find_product(data[key])
            if found is not None:
                return found
    return None


def _to_result(product: dict) -> dict:
    offer = _first_offer(product.get("offers"))

    price = None
    currency = None
    in_stock = None
    if offer:
        spec = offer.get("priceSpecification")
        if isinstance(spec, list):
            spec = spec[0] if spec else None
        if not isinstance(spec, dict):
            spec = {}

        raw_price = offer.get("price", offer.get("lowPrice", spec.get("price")))
        price = parse_price(raw_price)
        currency = offer.get("priceCurrency") or spec.get("priceCurrency")
        in_stock = _parse_availability(offer.get("availability"))

    return {
        "name": _clean(product.get("name")),
        "brand": _brand_name(product.get("brand")),
        "ean": next((_clean(product[k]) for k in _GTIN_KEYS if product.get(k)), None),
        "mpn": _clean(product.get("mpn")),
        "sku": _clean(product.get("sku")),
        "price": price,
        "currency": currency,
        "in_stock": in_stock,
    }


def _first_offer(offers):
    if isinstance(offers, list):
        return offers[0] if offers and isinstance(offers[0], dict) else None
    if isinstance(offers, dict):
        # AggregateOffer može sadržavati listu pojedinačnih ponuda
        if offers.get("price") is None and offers.get("lowPrice") is None and offers.get("offers"):
            return _first_offer(offers["offers"])
        return offers
    return None


def _brand_name(brand):
    if isinstance(brand, dict):
        return _clean(brand.get("name"))
    if isinstance(brand, list) and brand:
        return _brand_name(brand[0])
    return _clean(brand)


def _parse_availability(value):
    if not value:
        return None
    value = str(value)
    if value.endswith(("InStock", "LimitedAvailability", "OnlineOnly", "InStoreOnly")):
        return True
    if value.endswith(("OutOfStock", "SoldOut", "Discontinued")):
        return False
    return None


def _clean(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None
