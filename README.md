# 🎩 FastAPI Magic DTO

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-00a393.svg)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-V2-e92063.svg)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Stop duplicating your Pydantic schemas. Keep your Application layer pure.**

`fastapi-magic-dto` is a lightweight utility that allows you to map FastAPI request parameters (`Path`, `Query`, `Header`, `Cookie`, and `Body`) directly into a single, clean DTO (Data Transfer Object) **without polluting your business logic with HTTP-specific dependencies**.

## 🤬 The Problem

When building layered architectures (Clean Architecture, CQRS, Hexagonal), your Application layer (Interactors/Use Cases) should know **nothing** about HTTP. 

Normally, to extract data from multiple HTTP locations (like a User ID from the URL Path, and the User Name from the JSON Body), FastAPI forces you to either:
1. Write two separate schemas (one for FastAPI, one for the Application layer) and map them manually.
2. Pollute your Application DTO with `fastapi.Path` and `fastapi.Query`.

### ❌ Bad (Leaking HTTP into Domain)
```python
from fastapi import Path, Body
from pydantic import BaseModel

class UpdateUserDTO(BaseModel):
    user_id: int = Path(...)  # 🔴 Domain now depends on FastAPI!
    name: str = Body(...)
```
### ❌ Another Bad Approach (Duplication & Manual Repacking)
To keep the Domain DTO clean, you are forced to create a separate "Body" schema just for FastAPI, and then manually unpack and repack the data in every single endpoint. This leads to massive code duplication and boilerplate.

```python
from fastapi import Path, Body
from pydantic import BaseModel

# 🔴 1. Fake schema just to please FastAPI
class UpdateUserBody(BaseModel):
    name: str

# 2. Pure Application DTO
class UpdateUserDTO(BaseModel):
    user_id: int
    name: str

@app.put("/users/{user_id}")
async def update_user(
    user_id: int = Path(...),
    body: UpdateUserBody = Body(...)
):
    # 🔴 3. Ugly manual repacking everywhere!
    data = UpdateUserDTO(user_id=user_id, **body.model_dump())
    
    # Now pass `data` to your interactor...
    return await interactor(data)
```
## ✨ The Solution

`fastapi-magic-dto` allows you to write a **pure** Pydantic DTO (or standard Dataclass), and use an elegant type hint at the Router level to tell FastAPI exactly where to find the data.

### ✅ Good (Pure Domain + MagicDTO)
```python
from pydantic import BaseModel
from fastapi_magic_dto import MagicDTO, P

# 1. Pure Application DTO. Zero HTTP logic.
class UpdateUserDTO(BaseModel):
    user_id: int
    name: str

# 2. FastAPI Router mapping HTTP to the DTO
@app.put("/users/{user_id}")
async def update_user(
    data: MagicDTO[UpdateUserDTO, P.user_id]
):
    # `user_id` is extracted from the URL Path.
    # `name` is automatically extracted from the JSON Body.
    return data
```

## 📦 Installation

```bash
pip install fastapi-magic-dto
```

## 🚀 Features

- **Zero Duplication:** Write one DTO for both validation and business logic.
- **Perfect OpenAPI (Swagger):** Fully compatible with FastAPI's automatic schema generation. `Path`, `Query`, and `Body` parameters appear exactly where they should.
- **Type Checker Friendly:** Mypy, Pylance, and Pyright will see the correct types. Autocomplete works perfectly.
- **Dataclass Support:** Works natively with standard Python `@dataclass`—no Pydantic required!
- **Everything Supported:** Extract data from `Path` (P), `Query` (Q), `Header` (H), `Cookie` (C), and JSON `Body`.

## 🛠 Usage & Markers

The library provides 4 intuitive markers to define the origin of your fields:

| Marker | HTTP Location | Example |
|--------|---------------|---------|
| `P` | **Path** | `P.item_id` maps to `/items/{item_id}` |
| `Q` | **Query** | `Q.limit` maps to `?limit=10` |
| `H` | **Header** | `H.user_agent` maps to `User-Agent: ...` |
| `C` | **Cookie** | `C.session` maps to `Cookie: session=...` |

*Note: Any field in your DTO that is **not** explicitly marked will automatically be extracted from the JSON Request Body.*

## 📖 Complete Example (The Frankenstein)

You can extract data from everywhere simultaneously into a single DTO.

```python

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

app = FastAPI()


@app.post("/items/{category_id}", tags=["Items"])
async def create_item(
    # MagicDTO extracts `category_id` from Path, and `name`/`price` from Body
    data: MagicDTO[CreateItemDTO, P.category_id],
) -> dict:
    return await create_item_interactor(data)

```

## 🐍 Using Standard Dataclasses

Don't want to use Pydantic? No problem. `MagicDTO` fully supports standard Python dataclasses.

```python
from dataclasses import dataclass
from fastapi_magic_dto import MagicDTO, P, Q

@dataclass
class SearchDTO:
    category_id: int
    limit: int = 10
    search_term: str = ""

@app.get("/search/{category_id}")
async def search_items(
    data: MagicDTO[SearchDTO, P.category_id, Q.limit, Q.search_term]
):
    return data
```

## 📝 License

MIT License. See [LICENSE](LICENSE) for details.
