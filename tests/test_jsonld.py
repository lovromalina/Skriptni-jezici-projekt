from decimal import Decimal

from pricewatch.jsonld import extract_jsonld


def _page(jsonld: str) -> str:
    return f"""<html><head>
    <script type="application/ld+json">{{"@type": "BreadcrumbList"}}</script>
    <script type="application/ld+json">{jsonld}</script>
    </head><body><h1>Proizvod</h1></body></html>"""


def test_simple_product():
    html = _page("""{
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "  Samsung 990 PRO 2TB NVMe SSD ",
        "brand": {"@type": "Brand", "name": "Samsung"},
        "gtin13": "8806094215038",
        "mpn": "MZ-V9P2T0BW",
        "sku": "123456",
        "offers": {
            "@type": "Offer",
            "price": "189.99",
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock"
        }
    }""")
    assert extract_jsonld(html) == {
        "name": "Samsung 990 PRO 2TB NVMe SSD",
        "brand": "Samsung",
        "ean": "8806094215038",
        "mpn": "MZ-V9P2T0BW",
        "sku": "123456",
        "price": Decimal("189.99"),
        "currency": "EUR",
        "in_stock": True,
    }


def test_product_inside_graph_with_offer_list():
    html = _page("""{
        "@graph": [
            {"@type": "WebPage", "name": "Stranica"},
            {"@type": ["Product"], "name": "AMD Ryzen 7 7800X3D",
             "brand": "AMD", "gtin": "0730143314930",
             "offers": [{"@type": "Offer", "price": 1549,
                         "priceCurrency": "PLN",
                         "availability": "http://schema.org/OutOfStock"}]}
        ]
    }""")
    result = extract_jsonld(html)
    assert result["name"] == "AMD Ryzen 7 7800X3D"
    assert result["brand"] == "AMD"
    assert result["ean"] == "0730143314930"
    assert result["price"] == Decimal("1549")
    assert result["currency"] == "PLN"
    assert result["in_stock"] is False


def test_aggregate_offer_and_price_specification():
    html = _page("""[
        {"@type": "Product", "name": "Monitor",
         "offers": {"@type": "AggregateOffer", "lowPrice": "249,90",
                    "priceCurrency": "EUR"}},
        {"@type": "Product", "name": "Drugi"}
    ]""")
    assert extract_jsonld(html)["price"] == Decimal("249.90")

    html = _page("""{"@type": "Product", "name": "Tipkovnica",
        "offers": {"@type": "Offer",
                   "priceSpecification": {"price": "79.00", "priceCurrency": "EUR"}}}""")
    result = extract_jsonld(html)
    assert result["price"] == Decimal("79.00")
    assert result["currency"] == "EUR"


def test_invalid_json_is_skipped():
    html = """<script type="application/ld+json">{ neispravno </script>
    <script type="application/ld+json">{"@type": "Product", "name": "Miš"}</script>"""
    result = extract_jsonld(html)
    assert result["name"] == "Miš"
    assert result["price"] is None


def test_no_product_returns_none():
    assert extract_jsonld("<html><body>Nema podataka</body></html>") is None
    assert extract_jsonld(_page('{"@type": "Organization", "name": "Trgovina"}')) is None
