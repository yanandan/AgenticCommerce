"""Run with python -m commerceos.demo to inspect the three request-to-result flows."""
import json

from commerceos.filtering import value
from commerceos.parser import shopping_request
from commerceos.search import load_catalog


def main():
    catalog = load_catalog()
    for message in ('Show me running shoes under $150',
                    'I need wide running shoes for marathon training',
                    'Find hiking products under $100'):
        result = shopping_request(catalog, message)
        print(json.dumps({
            'request': message,
            'recognized': result['recognized'],
            'constraints': result['constraints'],
            'unverified_requirements': result['unverified_requirements'],
            'status': result['status'],
            'total': result['total'],
            'matching_product_ids': [value(p, 'id') for p in result['products']],
        }, indent=2))


if __name__ == '__main__':
    main()
