"""
Example: Complex Parsing
-----------------------------------------------
Demonstrates mapping data from absolutely everywhere in the HTTP request:
Path, Query, Header, Cookie, and JSON Body into a single, clean DTO.
"""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from fastapi_magic_dto import C, H, MagicDTO, P, Q

# --- Application Layer (Business Logic) ---


class ComplexActionDTO(BaseModel):
    # From URL Path
    category_id: int
    subcategory_id: int

    # From URL Query
    promo_code: str | None = None

    # From HTTP Headers
    user_agent: str | None = None

    # From HTTP Cookies
    session_id: str | None = None

    # From JSON Body
    name: str = Field(..., description="The name of the item")
    description: str = Field(..., description="Detailed description")


class ComplexActionInteractor:
    async def __call__(self, data: ComplexActionDTO) -> dict:
        # The interactor has no idea this data came from 5 different HTTP locations.
        # It just receives a pure, validated Python object.
        return {
            "status": "success",
            "message": "Successfully parsed data from all HTTP locations.",
            "parsed_dto": data.model_dump(),
        }


complex_action_interactor = ComplexActionInteractor()


# --- Presentation Layer (FastAPI Route) ---

app = FastAPI(title="Example 03: Complex Parsing")


@app.post("/items/{category_id}/{subcategory_id}", tags=["Items"])
async def create_complex_item(
    # MagicDTO is doing the heavy lifting here!
    data: MagicDTO[
        ComplexActionDTO,
        P.category_id,
        P.subcategory_id,
        Q.promo_code,
        H.user_agent,
        C.session_id,
    ],
) -> dict:
    return await complex_action_interactor(data)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
