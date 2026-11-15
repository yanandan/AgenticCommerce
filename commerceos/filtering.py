"""Dependency-free catalog filtering shared by FastAPI and the hosted Python chat."""
import re
from collections.abc import Mapping


def value(product, field, default=''):
    return product.get(field, default) if isinstance(product, Mapping) else getattr(product, field, default)


def phrase_in(phrase, text):
    return re.search(r'(?<!\w)' + re.escape(phrase.casefold()) + r'(?!\w)', text.casefold()) is not None


def width_key(width):
    return re.sub(r'[-–—]', ' ', width.casefold())


def supports_use_case(product, use_case):
    tags = value(product, 'use_cases', [])
    text = ' '.join(str(value(product, field)) for field in ('name', 'product_type', 'description'))
    return any(use_case.casefold() == tag.casefold() for tag in tags) or phrase_in(use_case, text)


def search_products(products, query='', category='', *, sport='', max_price_cents=None,
                    max_price_inclusive=True, width='', use_case='', brand=''):
    """Apply every supplied constraint with AND, then preserve keyword ranking."""
    tokens = re.findall(r'\w+', query.casefold())
    ranked = []
    for product in products:
        if any(expected and value(product, field).casefold() != expected.casefold()
               for field, expected in [('category', category), ('sport', sport), ('brand', brand)]):
            continue
        if max_price_cents is not None:
            price = value(product, 'price_cents')
            if price > max_price_cents or (price == max_price_cents and not max_price_inclusive):
                continue
        if width and width_key(width) not in [width_key(w) for w in value(product, 'widths', [])]:
            continue
        if use_case and not supports_use_case(product, use_case):
            continue
        fields = [(str(value(product, field)).casefold(), weight) for field, weight in
                  [('name', 5), ('category', 3), ('product_type', 3), ('sport', 3),
                   ('brand', 2), ('description', 1)]]
        scores = [max((weight for text, weight in fields if token in text), default=0)
                  for token in tokens]
        if all(scores):
            ranked.append((sum(scores), product))
    return [product for _, product in sorted(ranked, key=lambda item: (-item[0], value(item[1], 'id')))]
