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
