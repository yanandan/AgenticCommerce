import json
from pathlib import Path

from pydantic import TypeAdapter

from commerceos.models import Product
from commerceos.filtering import search_products  # Public search service; existing imports stay valid.

CATALOG_PATH = Path(__file__).parent / 'data' / 'products.json'


def load_catalog(path: Path = CATALOG_PATH) -> tuple[Product, ...]:
    products = TypeAdapter(list[Product]).validate_python(json.loads(path.read_text()))
    if len({product.id for product in products}) != len(products):
        raise ValueError('Catalog product IDs must be unique')
    return tuple(products)
