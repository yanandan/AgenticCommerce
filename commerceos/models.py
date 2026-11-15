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
    widths: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    total: int
    products: list[Product]


class ShoppingConstraints(BaseModel):
    category: str | None = None
    sport: str | None = None
    max_price_cents: int | None = None
    max_price_inclusive: bool = True
    width: str | None = None
    use_case: str | None = None
    brand: str | None = None


class ShoppingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    message: str = Field(min_length=1, max_length=500)


class ShoppingResponse(BaseModel):
    message: str
    constraints: ShoppingConstraints
    recognized: list[str]
    unverified_requirements: list[str]
    unrecognized: list[str]
    clarifications: list[str]
    status: Literal['matches', 'no_matches', 'needs_refinement']
    total: int
    products: list[Product]
