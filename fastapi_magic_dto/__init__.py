"""
FastAPI Magic DTO
=================

A utility library to automatically map FastAPI request parameters
(Path, Query, Header, Cookie) into a single Pydantic DTO without duplicating schemas.

Example Usage:
--------------
```python
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi_magic_dto import MagicDTO, P, Q, H, C

app = FastAPI()

class UpdateUserDTO(BaseModel):
    user_id: int          # Extracted from Path
    include_posts: bool   # Extracted from Query
    user_agent: str       # Extracted from Header
    session: str          # Extracted from Cookie
    name: str             # Extracted from JSON Body
    age: int              # Extracted from JSON Body

@app.put("/users/{user_id}")
async def update_user(
    data: MagicDTO[
        UpdateUserDTO,
        P.user_id,
        Q.include_posts,
        H.user_agent,
        C.session
    ]
) -> dict:
    return {"extracted_data": data}
"""

from .builder import MagicDTO
from .markers import C, H, P, Q

__all__ = [
    "MagicDTO",
    "P",
    "Q",
    "H",
    "C",
]
