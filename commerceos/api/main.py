from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request

from commerceos.models import SearchResponse
from commerceos.search import load_catalog, search_products


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.catalog = load_catalog()
    yield


app = FastAPI(title='CommerceOS', version='0.1.0', lifespan=lifespan)


@app.get('/products/search', response_model=SearchResponse)
def search(request: Request, q: str = Query(default='', max_length=200),
           category: str = Query(default='', max_length=100)) -> SearchResponse:
    query = q.strip()
    products = search_products(request.app.state.catalog, query, category)
    return SearchResponse(query=query, total=len(products), products=products)
