"""
Example: Searching Items
---------------------------
Demonstrates a GET request extracting pagination and search filters
strictly from the URL Query parameters.
"""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from fastapi_magic_dto import MagicDTO, Q

# --- Application Layer (Business Logic) ---


class SearchItemsDTO(BaseModel):
    search_term: str
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    in_stock_only: bool = True


class SearchItemsInteractor:
    async def __call__(self, data: SearchItemsDTO) -> dict:
        # Business logic goes here (e.g., querying the database)
        return {
            "status": "success",
            "message": f"Searching for '{data.search_term}' (limit: {data.limit}, offset: {data.offset}).",
            "search_filters": data.model_dump(),
        }


search_items_interactor = SearchItemsInteractor()


# --- Presentation Layer (FastAPI Route) ---

app = FastAPI()


@app.get("/search", tags=["Search"])
async def search_items(
    # MagicDTO extracts all these fields from Query parameters
    data: MagicDTO[SearchItemsDTO, Q.search_term, Q.limit, Q.offset, Q.in_stock_only],
) -> dict:
    return await search_items_interactor(data)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
