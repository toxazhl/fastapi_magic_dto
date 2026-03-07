"""
Example: Creating an Item
----------------------------
Demonstrates a simple POST request where `category_id` is extracted from the URL Path,
and the rest of the fields (`name`, `price`) are extracted from the JSON Body.
"""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from fastapi_magic_dto import MagicDTO, P

# --- Application Layer (Business Logic) ---


class CreateItemDTO(BaseModel):
    category_id: int
    name: str = Field(..., min_length=2, max_length=100)
    price: float = Field(...)


class CreateItemInteractor:
    async def __call__(self, data: CreateItemDTO) -> dict:
        # Business logic goes here (e.g., saving to the database)
        return {
            "status": "success",
            "message": f"Item '{data.name}' created in category {data.category_id}.",
            "item_data": data.model_dump(),
        }


create_item_interactor = CreateItemInteractor()


# --- Presentation Layer (FastAPI Route) ---

app = FastAPI()


@app.post("/items/{category_id}", tags=["Items"])
async def create_item(
    # MagicDTO extracts `category_id` from Path, and `name`/`price` from Body
    data: MagicDTO[CreateItemDTO, P.category_id],
) -> dict:
    return await create_item_interactor(data)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
