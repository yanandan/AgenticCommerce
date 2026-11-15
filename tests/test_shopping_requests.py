import pytest
from fastapi.testclient import TestClient

from commerceos.api.main import app
from commerceos.filtering import search_products
from commerceos.models import Product
from commerceos.parser import shopping_request
from commerceos.search import load_catalog


@pytest.fixture(scope='module')
def catalog():
    return load_catalog()


def test_running_shoes_under_150(catalog):
    result = shopping_request(catalog, 'Show me running shoes under $150')
    assert result['status'] == 'matches'
    assert result['constraints']['category'] == 'Shoes'
    assert result['constraints']['sport'] == 'Running'
    assert result['constraints']['max_price_cents'] == 15000
    assert result['constraints']['max_price_inclusive'] is False
    assert result['constraints']['brand'] is None
    assert result['total'] == 3
    assert all(p.category == 'Shoes' and p.sport == 'Running' and p.price_cents < 15000
               for p in result['products'])


def test_wide_marathon_request_explains_missing_catalog_metadata(catalog):
    result = shopping_request(catalog, 'I need wide running shoes for marathon training')
    assert result['constraints']['category'] == 'Shoes'
    assert result['constraints']['sport'] == 'Running'
    assert result['constraints']['width'] is None
    assert result['constraints']['use_case'] is None
    assert len(result['unverified_requirements']) == 2
    assert 'wide' in result['unverified_requirements'][0]
    assert 'marathon training' in result['unverified_requirements'][1]
    assert result['status'] == 'needs_refinement'
    assert result['products'] == []
    # A new, explicitly less restrictive request works; no requirements carry over.
    assert shopping_request(catalog, 'running shoes')['total'] == 3


def test_hiking_products_under_100(catalog):
    result = shopping_request(catalog, 'Find hiking products under $100')
    assert result['constraints']['sport'] == 'Hiking'
    assert result['constraints']['category'] is None  # Do not infer Outdoor.
    assert result['constraints']['max_price_cents'] == 10000
    assert result['total'] == 5
    assert all(p.sport == 'Hiking' and p.price_cents < 10000 for p in result['products'])


def test_explicit_brand_and_all_filters(catalog):
    result = shopping_request(catalog, 'Show me Summit Arc running shoes under $150')
    expected = search_products(catalog, '', 'Shoes', sport='Running', brand='Summit Arc',
                               max_price_cents=15000, max_price_inclusive=False)
    assert result['constraints']['brand'] == 'Summit Arc'
    assert result['status'] == 'matches'
    assert result['products'] == expected
    assert all(p.brand == 'Summit Arc' for p in result['products'])
    assert shopping_request(catalog, 'running shoes')['constraints']['brand'] is None


def test_supported_use_case_is_literal_catalog_wording(catalog):
    result = shopping_request(catalog, 'Show me trail running shoes under $150')
    assert result['constraints']['use_case'] == 'trail running'
    assert result['total'] == 1
    assert 'Trail Running' in result['products'][0].name


def test_width_and_use_case_when_explicit_metadata_exists():
    def product(id, widths, cases, price=9999, brand='Test Brand'):
        return Product(id=id, name='Running Shoes', description='Footwear', category='Shoes',
                       sport='Running', brand=brand, price_cents=price,
                       widths=widths, use_cases=cases)
    products = (product('yes', ['wide'], ['marathon training']),
                product('wrong-width', ['regular'], ['marathon training']),
                product('wrong-case', ['wide'], ['trail running']),
                product('unknown', [], []),
                product('too-expensive', ['wide'], ['marathon training'], 16000))
    result = shopping_request(products, 'wide running shoes for marathon training under $150')
    assert result['constraints']['width'] == 'wide'
    assert result['constraints']['use_case'] == 'marathon training'
    assert [p.id for p in result['products']] == ['yes']


def test_price_boundaries_decimal_comma_and_case():
    products = tuple(Product(id=str(price), name='Running Shoes', description='Footwear',
                             category='Shoes', sport='Running', brand='Test', price_cents=price)
                     for price in [9999, 10000, 10001])
    assert shopping_request(products, 'RUNNING SHOES under $100')['total'] == 1
    assert shopping_request(products, 'running shoes at most $100')['total'] == 2
    assert shopping_request(products, 'running shoes at most $100.')['total'] == 2
    assert shopping_request(products, 'running shoes below $100.01')['total'] == 2
    assert shopping_request(products, 'running shoes up to $1,000.50')['constraints']['max_price_cents'] == 100050


@pytest.mark.parametrize('message', [
    'running or hiking shoes', 'running hiking shoes', 'running shoes not wide',
    'running shoes without Strideforge', 'running shoes under $100 under $150',
    'running shoes over $100', 'comfortable running shoes', 'Nike running shoes',
    'running shoes under -$100', 'running shoes under $100.999',
    'running shoes under €100', 'not running shoes', 'hello', 'under 100%',
    'running shoes between $50 and $100', 'women men shoes',
])
def test_ambiguity_or_unsupported_language_never_silently_relaxes(catalog, message):
    result = shopping_request(catalog, message)
    assert result['status'] == 'needs_refinement'
    assert result['clarifications']
    assert result['products'] == []


def test_no_matches_keeps_every_constraint(catalog):
    result = shopping_request(catalog, 'running shoes under $1')
    assert result['status'] == 'no_matches'
    assert result['constraints']['max_price_cents'] == 100
    assert result['products'] == []


def test_chat_endpoint_examples_and_validation():
    with TestClient(app) as client:
        for message, status, total in [
            ('Show me running shoes under $150', 'matches', 3),
            ('I need wide running shoes for marathon training', 'needs_refinement', 0),
            ('Find hiking products under $100', 'matches', 5),
        ]:
            response = client.post('/shopping/requests', json={'message': message})
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == status and data['total'] == total
            assert data['recognized']
        for message in ['', '   ', 'x' * 501]:
            assert client.post('/shopping/requests', json={'message': message}).status_code == 422
        assert client.post('/shopping/requests', json={'message': 'running shoes', 'history': []}).status_code == 422


def test_browser_and_backend_share_identical_python():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for name in ('__init__.py', 'filtering.py', 'parser.py'):
        assert (root / 'commerceos' / name).read_bytes() == (
            root / 'sites' / 'commerceos' / 'dist' / 'python' / 'commerceos' / name).read_bytes()


def test_hyphenated_explicit_width_is_filtered_consistently():
    product = Product(id='wide', name='Running Shoes', description='Footwear', category='Shoes',
                      sport='Running', brand='Test', price_cents=10000, widths=['extra-wide'])
    result = shopping_request((product,), 'extra-wide running shoes')
    assert result['constraints']['width'] == 'extra wide'
    assert result['status'] == 'matches'
    assert result['total'] == 1
