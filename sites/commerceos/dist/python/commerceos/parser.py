"""Small deterministic parser. No model calls, inferred preferences, or conversation memory."""
import re
from decimal import Decimal, localcontext

from commerceos.filtering import search_products, supports_use_case, value, width_key

CATEGORY_ALIASES = {
    'Shoes': ('shoe', 'shoes', 'footwear', 'sneakers'),
    'Women': ('women', "women's", 'womens'),
    'Men': ('men', "men's", 'mens'),
    'Kids': ('kids', "kids'", 'children', "children's"),
    'The Holiday Shop': ('holiday', 'holiday shop', 'the holiday shop'),
    'Exercise & Wellness': ('exercise', 'wellness', 'exercise and wellness', 'exercise & wellness'),
}
USE_CASE_PHRASES = ('marathon training', 'marathon', 'trail running', 'road running',
                    'race day', 'everyday walking', 'strength training', 'recovery',
                    'camping', 'training')
STOP_WORDS = set("show me i need find looking for want would like please can you could a an the some any pair of products product gear equipment shop shopping search get my to and with i'm im that's that is are it this thanks thank".split())
NUMBER = r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?'
PRICE = re.compile(
    r'\b(under|below|less than|up to|at most|no more than|maximum(?: of)?|max(?:imum)? price(?: of)?|max|budget(?: of)?)'
    r'\s*\$?\s*(' + NUMBER + r')(?:\s*(?:usd|dollars))?(?!\w|[.,]\d)')


def normalize(text):
    text = text.casefold().replace('’', "'").replace('–', '-').replace('—', '-')
    return re.sub(r'(?<=[a-z])-(?=[a-z])', ' ', text)


def parse_request(message, products):
    if not isinstance(message, str) or not message.strip() or len(message) > 500:
        raise ValueError('Use a shopping request between 1 and 500 characters.')
    text = normalize(message)
    consumed = [False] * len(text)
    constraints = dict(category=None, sport=None, max_price_cents=None,
                       max_price_inclusive=True, width=None, use_case=None, brand=None)
    recognized, unverified, clarifications = [], [], []

    def consume(start, end):
        consumed[start:end] = [True] * (end - start)

    def matches(phrase):
        return re.finditer(r'(?<!\w)' + re.escape(normalize(phrase)) + r'(?!\w)', text)

    def extract(field, choices):
        found = []
        for canonical, aliases in choices.items():
            for alias in sorted(set(aliases), key=len, reverse=True):
                for match in matches(alias):
                    consume(*match.span())
                    if canonical not in found:
                        found.append(canonical)
        if len(found) == 1:
            constraints[field] = found[0]
            recognized.append(f'{field.replace("_", " ").title()}: {found[0]}')
        elif len(found) > 1:
            clarifications.append(f'Multiple {field} values understood: {", ".join(found)}. Choose one.')

    categories = sorted({value(p, 'category') for p in products})
    extract('category', {c: (c, *CATEGORY_ALIASES.get(c, ())) for c in categories})
    sports = sorted({value(p, 'sport') for p in products})
    extract('sport', {s: (s,) for s in sports})
    brands = sorted({value(p, 'brand') for p in products})
    extract('brand', {b: (b,) for b in brands})

    prices = list(PRICE.finditer(text))
    for match in prices:
        consume(*match.span())
    if len(prices) == 1:
        match = prices[0]
        amount = match[2].replace(',', '')
        with localcontext() as context:
            context.prec = max(28, len(amount) + 2)
            cents = int(Decimal(amount) * 100)
        inclusive = match[1] not in ('under', 'below', 'less than')
        constraints.update(max_price_cents=cents, max_price_inclusive=inclusive)
        recognized.append(f'Price: {"at most" if inclusive else "below"} ${cents // 100:,}.{cents % 100:02d} USD')
    elif len(prices) > 1:
        clarifications.append('Multiple price limits understood. Specify one maximum price.')

    widths = []
    for match in re.finditer(r'\b(extra wide|wide|narrow|regular)(?:\s+width)?\b', text):
        consume(*match.span())
        if match[1] not in widths:
            widths.append(match[1])
    if len(widths) > 1:
        clarifications.append(f'Multiple widths understood: {", ".join(widths)}. Choose one.')
    elif widths:
        width = widths[0]
        if any(width in [width_key(w) for w in value(p, 'widths', [])] for p in products):
            constraints['width'] = width
            recognized.append(f'Width: {width}')
        else:
            unverified.append(f'Width: {width}. The catalog has no verified {width}-width data.')

    # Longest phrase wins only for overlapping phrases, never for distinct requirements.
    cases, case_spans = [], []
    phrases = set(USE_CASE_PHRASES) | {tag for p in products for tag in value(p, 'use_cases', [])}
    for phrase in sorted(phrases, key=lambda item: (-len(item), item)):
        for match in matches(phrase):
            start, end = match.span()
            if any(start < old_end and end > old_start for old_start, old_end in case_spans):
                continue
            case_spans.append((start, end))
            consume(start, end)
            if phrase not in cases:
                cases.append(phrase)
    if len(cases) > 1:
        clarifications.append(f'Multiple use cases understood: {", ".join(cases)}. Choose one.')
    elif cases:
        use_case = cases[0]
        if any(supports_use_case(p, use_case) for p in products):
            constraints['use_case'] = use_case
            recognized.append(f'Use case (catalog wording): {use_case}')
        else:
            unverified.append(f'Use case: {use_case}. The catalog does not verify this use case.')

    remainder = ''.join(' ' if consumed[i] else char for i, char in enumerate(text))
    if re.search(r"\b(or|not|no|without|except|excluding|avoid|over|above|minimum|between|instead)\b|don't|at least", remainder):
        clarifications.append('Alternatives, exclusions, minimums, and ranges are not supported. Restate a positive request with one maximum price.')
    unrecognized = list(dict.fromkeys(word for word in re.findall(r"[\w]+(?:'[\w]+)?|[€£%<>]", remainder)
                                      if word not in STOP_WORDS))
    if unrecognized:
        clarifications.append('Not understood: ' + ', '.join(unrecognized) + '. Rephrase or remove these words; they have not been used as filters.')
    if unverified:
        clarifications.append('These requirements cannot be verified. Remove them in a new request to search only the recognized requirements.')
    if not recognized:
        clarifications.append('Specify a catalog category, sport, brand, supported use case, or maximum USD price.')
    return dict(constraints=constraints, recognized=recognized,
                unverified_requirements=unverified, unrecognized=unrecognized,
                clarifications=clarifications)


def shopping_request(products, message):
    parsed = parse_request(message, products)
    filters = {key: val for key, val in parsed['constraints'].items() if val is not None}
    # Never present partial matches as satisfying an unverified or ambiguous request.
    needs_refinement = bool(parsed['clarifications'])
    matches = [] if needs_refinement else search_products(products, '', **filters)
    return dict(message=message.strip(), **parsed, total=len(matches), products=matches,
                status='needs_refinement' if needs_refinement else 'matches' if matches else 'no_matches')
