from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class Product(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    sport: str = Field(min_length=1)
    category: str = Field(min_length=1)
    product_type: str = ''
    brand: str = Field(min_length=1)
    price_cents: int = Field(gt=0, strict=True)
    currency: Literal['USD'] = 'USD'


class SearchResponse(BaseModel):
    query: str
    total: int
    products: list[Product]
