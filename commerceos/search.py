import json
import re
from pathlib import Path

from pydantic import TypeAdapter

from commerceos.models import Product

CATALOG_PATH = Path(__file__).parent / 'data' / 'products.json'


def load_catalog(path: Path = CATALOG_PATH) -> tuple[Product, ...]:
    products = TypeAdapter(list[Product]).validate_python(json.loads(path.read_text()))
    if len({product.id for product in products}) != len(products):
        raise ValueError('Catalog product IDs must be unique')
    return tuple(products)


def search_products(products: tuple[Product, ...], query: str, category: str = '') -> list[Product]:
    """Require every query token; prioritize names, then category/sport/brand."""
    tokens = re.findall(r'\w+', query.casefold())
    ranked = []
    for product in products:
        if category and product.category != category:
            continue
        fields = [(product.name.casefold(), 5), (product.category.casefold(), 3), (product.product_type.casefold(), 3),
                  (product.sport.casefold(), 3), (product.brand.casefold(), 2),
                  (product.description.casefold(), 1)]
        scores = [max((weight for value, weight in fields if token in value), default=0)
                  for token in tokens]
        if all(scores):
            ranked.append((sum(scores), product))
    return [product for _, product in sorted(ranked, key=lambda item: (-item[0], item[1].id))]
