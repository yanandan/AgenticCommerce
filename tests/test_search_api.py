from fastapi.testclient import TestClient

from commerceos.api.main import app
from commerceos.models import Product


def test_search_api_matches_and_ranks_known_catalog():
    def product(id, name, sport):
        return Product(id=id, name=name, sport=sport, category='Equipment',
                       brand='Test Brand', description='Practice equipment', price_cents=2599)

    with TestClient(app) as client:
        # The real catalog is loaded by startup before replacing it with a focused fixture.
        assert len(app.state.catalog) == 300
        assert len({p.id for p in app.state.catalog}) == 300
        assert len({p.category for p in app.state.catalog}) == 11
        assert client.get('/products/search', params={'category': 'Golf'}).json()['total'] == 25
        assert client.get('/products/search', params={'category': 'Women'}).json()['total'] == 25
        assert client.get('/products/search', params={'category': 'Sports'}).json()['total'] == 50
        app.state.catalog = (
            product('P-3', 'Training Ball', 'Basketball'),
            product('P-2', 'Basketball Starter', 'Basketball'),
            product('P-1', 'Basketball Starter', 'Basketball'),
            product('P-4', 'Soccer Ball', 'Soccer'),
        )
        response = client.get('/products/search', params={'q': '  BASKETBALL  '})
        assert response.status_code == 200
        data = response.json()
        assert data['query'] == 'BASKETBALL'
        assert data['total'] == 3
        assert [p['id'] for p in data['products']] == ['P-1', 'P-2', 'P-3']
        assert data['products'][0]['price_cents'] == 2599
        assert client.get('/products/search', params={'q': 'basketball starter'}).json()['total'] == 2
        assert client.get('/products/search', params={'q': 'unfindable'}).json()['products'] == []
        assert client.get('/products/search').json()['total'] == 4
        assert client.get('/products/search', params={'q': 'x' * 201}).status_code == 422
