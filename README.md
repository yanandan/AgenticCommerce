# CommerceOS — product-search foundation

A Python application using Streamlit, FastAPI, and a static catalog of 300 fictional sports products: 11 retail categories. Sports contains 50 products; The Holiday Shop, Golf, Shoes, Women, Men, Kids, Accessories, Fan Shop, Exercise & Wellness, and Outdoor each contain 25. Every product has a primary category, a specific product type, and a sport or activity.

The assortment is inspired by broad sporting-goods retail categories such as those found at Dick’s Sporting Goods. Names, brands, descriptions, and prices are synthetic; no retailer listings were copied or scraped. This project has no retailer affiliation. Prices are illustrative USD values, not live offers. The catalog does not model inventory, sizes, or checkout.

## Run locally

From the project directory, with Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m uvicorn commerceos.api.main:app --reload
```

In a second terminal, activate the same environment and run:

```bash
source .venv/bin/activate
python -m streamlit run commerceos/ui/app.py
```

Open http://localhost:8501. The API documentation is at http://localhost:8000/docs.
Set `COMMERCEOS_API_URL` to change the backend URL used by the UI.

```bash
python -m pytest
curl 'http://localhost:8000/products/search?q=basketball'
```

## Architecture and data flow

```text
products.json → startup validation → in-memory catalog
                                             ↓
Streamlit form → GET /products/search?q=… → search service
       ↑                                     ↓
product cards ← JSON SearchResponse ← ranked products
```

1. FastAPI loads and validates the packaged JSON catalog once during startup. Duplicate IDs or invalid products fail startup with an error.
2. A Streamlit form sends the query as an HTTP query parameter to FastAPI. The UI initially requests the full catalog.
3. The search service tokenizes and case-folds the query. Every token must appear as a substring in a searchable field. For each token, the best matching field contributes its weight: name 5, category/product type/sport 3, brand 2, description 1.
4. Results sort by descending total score, then stable product ID. Empty or punctuation-only queries return all products ordered by ID. No matches produce an empty list. Queries longer than 200 characters receive HTTP 422.
5. FastAPI returns `query`, `total`, and validated `products`. Streamlit renders cards and converts integer cents to dollar display values. Backend failures produce a visible retry message.

Products contain `id`, `name`, `description`, `sport`, `category`, `product_type`, `brand`, `price_cents`, and `currency`. Catalog paths resolve relative to the package, independent of the server's working directory. No database or external service is required.

The integration test verifies real catalog loading and count, then uses a small fixed fixture to verify HTTP validation, case-insensitive matching, ranking, stable ties, multi-token queries, empty queries, and no-match behavior.

## Deferred phases

Memory, agents, MCP, A2A, and observability are reserved for later phases. This increment implements only the product-search foundation.

## Hosted deployment

The application requires a Python-capable host supporting long-lived WebSocket connections. Sites static/Worker hosting cannot run this Streamlit/FastAPI stack.

A Dockerfile and Render Blueprint (`render.yaml`) are included. Both processes run in one container: Streamlit listens on the host's `PORT` (default 10000), and FastAPI stays internal on 127.0.0.1:8765. The launcher waits for API readiness and stops the container if either process exits. The container runs as a non-root user. No external database, API key, or secret is needed.

To deploy with Render:

1. Push this project's source to a GitHub repository you control. Do not include `work/`, credentials, or virtual environments.
2. Sign in to Render, choose **New → Blueprint**, and connect that repository.
3. Review the `commerceos` web service and deploy. The blueprint requests the free plan, subject to current Render account eligibility and availability.
4. After the service becomes live, open the actual HTTPS URL shown by Render. No URL is reserved until the provider creates the service. Free services may sleep when idle and take time to wake up.

To verify the combined launcher locally:

```bash
PORT=10000 python -m commerceos.serve
```

To use another container host:

```bash
docker build -t commerceos .
docker run --rm -p 10000:10000 -e PORT=10000 commerceos
```

The browser talks to Streamlit; Streamlit talks to the internal FastAPI service. Only the Streamlit port needs to be public. Hosting does not add memory, agents, MCP, A2A, or observability.

The API supports an optional exact `category` query parameter, for example `/products/search?category=Women&q=hoodie`. Category names match the 11 browser navigation labels. Category selection is also available in Streamlit.

## Browser application

The browser version lives in `sites/commerceos/dist/` and has the same 300-product, 11-category catalog. It includes keyword search, category filters, sorting, and pagination. It is currently hosted privately through Sites. GitHub pushes do not automatically deploy to the existing Sites host. The `.openai/hosting.json` file identifies that existing deployment; it contains no credentials.

Run browser search and catalog checks from the repository root:

```bash
node sites/commerceos/check.mjs
```

For local static browsing (Node is only required for checks):

```bash
python -m http.server 3000 --directory sites/commerceos/dist
```

Open http://localhost:3000 on the computer running the command. The Python app runs separately using the instructions above.

To regenerate both catalog copies and browser category labels from the curated synthetic definitions:

```bash
python scripts/generate_catalog.py
```

This repository contains the search foundation only. Memory, agents, MCP, A2A, and observability remain deferred.

## Conversational shopping requests — deterministic Python

Open **Shopping chat** in Streamlit or the hosted browser app. Describe a request, inspect the recognized requirements, and refine with another complete request. Chat history is only a session-local display: the parser receives one message at a time and never inherits requirements from earlier turns. No LLM, embeddings, agent, external AI call, or persistent memory is used.

The existing keyword search remains available under **Browse catalog**. The backend's search service now delegates to a dependency-free shared filtering core. Keyword ranking is unchanged, and the same core applies all parsed constraints with AND.

### Supported constraints

- **Category and sport:** catalog values and a short explicit category alias list (`shoes`, `footwear`, `women's`, etc.). The parser never assumes Hiking means Outdoor, or that marathon training implies Running.
- **Maximum USD price:** integer cents parsed with `Decimal`. `under`, `below`, and `less than` are strict; `at most`, `up to`, `no more than`, `max`, and `budget` are inclusive. A price-only request is supported.
- **Brand:** only an explicitly mentioned full catalog brand name. No default brand or fuzzy brand matching.
- **Width:** only when a product has explicit `widths` metadata. All 300 current products have unknown widths; no width values have been invented.
- **Use case:** a small phrase list and any explicit `use_cases` tags. A recognized phrase must occur literally in a product's name, product type, or description, or match an explicit tag. This is text evidence, not a claim of performance or suitability. The current catalog supports wording such as `trail running`, but does not verify `marathon training`.

Unknown words, missing metadata, multiple values for the same constraint, negation, alternatives, ranges, and minimum prices trigger a visible refinement response. No products are presented as confirmed matches until those issues are resolved. Valid requests with zero matches keep every filter; the service never loosens a price, brand, or other requirement. The browser's **Use only recognized requirements** button fills a new request for the shopper to review and send; it never silently drops requirements.

### Examples against the current catalog

| Request | Supported requirements | Outcome |
| --- | --- | --- |
| Show me running shoes under $150 | Category Shoes AND sport Running AND price < 15000 cents | 3 matches |
| I need wide running shoes for marathon training | Category Shoes AND sport Running; wide and marathon training are unverified | Refinement required; no confirmed results |
| Find hiking products under $100 | Sport Hiking AND price < 10000 cents | 5 matches; no Outdoor category inferred |

### Request-to-result flow

```text
Shopper's message
    ↓
Streamlit chat → POST /shopping/requests {"message": "Show me running shoes under $150"}
    ↓
Deterministic Python parser (commerceos/parser.py)
    ↓
category=Shoes, sport=Running, max_price_cents=15000, max_price_inclusive=false
    ↓
Shared catalog filters (commerceos/filtering.py): every constraint must hold
    ↓
3 products + recognized requirements + clarification/status fields
    ↓
Chat response: requirements, matching cards, and expandable request-to-result trace
```

The browser app runs the **identical Python parser and filtering modules** using a pinned Pyodide 0.27.7 WebAssembly runtime. Its input is the same static JSON catalog, and it renders the same response shape. The browser has no Python backend to contact and does not call the FastAPI endpoint. Its first chat request downloads Python runtime assets from jsDelivr, so it requires network access and may take a moment. If that fails, the chat reports an error and the existing catalog browser remains usable.

The FastAPI endpoint validates request length (1–500 characters), accepts only `message`, and returns `constraints`, `recognized`, `unverified_requirements`, `unrecognized`, `clarifications`, `status`, `total`, and `products`. Optional product fields `widths` and `use_cases` default to empty lists, meaning unknown, not regular width or general-purpose suitability.

```bash
curl -X POST http://localhost:8000/shopping/requests \
  -H 'Content-Type: application/json' \
  -d '{"message":"Show me running shoes under $150"}'
python -m commerceos.demo
python -m pytest -q
python scripts/sync_chat_python.py --check
node sites/commerceos/check.mjs
```

When editing the Python parser or filter, run `python scripts/sync_chat_python.py` to refresh the browser assets. A test checks byte-for-byte parity to prevent the hosted parser drifting from the backend.

### Limitations

This is a conservative phrase matcher, not general language understanding. Typos, unlisted synonyms, partial brand names, implied intent, colors, sizes, compound OR conditions, exclusions, and follow-ups such as “make those cheaper” are unsupported and surfaced for clarification. It supports one category, sport, price limit, width, use case, and brand per request. The catalog's primary categories can conflict (for example, Women and Shoes); such combinations require refinement rather than a guessed interpretation. Current width and marathon metadata are absent. Use-case matching only verifies literal catalog wording. Session chat history is not saved, and each message starts fresh. The hosted chat depends on a CDN for its Python runtime; full visual browser QA requires desktop/browser tools not available in this environment.

Memory, agents, MCP, A2A, and observability remain deferred.
