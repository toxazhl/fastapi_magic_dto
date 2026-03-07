"""
Example: Standard Python Dataclasses
---------------------------------------
Demonstrates that the MagicDTO library works flawlessly with pure Python `@dataclass`.
No Pydantic dependency required for the DTO definition!
"""

import dataclasses

import uvicorn
from fastapi import FastAPI

from fastapi_magic_dto import H, MagicDTO, P, Q

# --- Application Layer (Business Logic) ---


@dataclasses.dataclass
class CreateUserDataclassDTO:
    # Extracted from Path
    user_id: int

    # Extracted from Query (with default value)
    include_history: bool = False

    # Extracted from Header (with default value)
    user_agent: str | None = None

    # Extracted from JSON Body
    # In dataclasses, fields without defaults must precede fields with defaults.
    username: str = dataclasses.field(default="Unknown User")
    age: int = 18


class CreateUserInteractor:
    async def __call__(self, data: CreateUserDataclassDTO) -> dict:
        # The interactor receives a standard Python Dataclass.
        return {
            "status": "success",
            "message": f"User {data.user_id} processed successfully via Dataclass.",
            "dataclass_payload": dataclasses.asdict(data),
        }


create_user_interactor = CreateUserInteractor()


# --- Presentation Layer (FastAPI Route) ---

app = FastAPI()


@app.post("/users/{user_id}", tags=["Dataclass Examples"])
async def create_user_endpoint(
    # MagicDTO natively supports standard Dataclasses!
    data: MagicDTO[
        CreateUserDataclassDTO,
        P.user_id,
        Q.include_history,
        H.user_agent,
    ],
) -> dict:
    """
    This endpoint parses Path, Query, Header, and Body directly into a standard
    Python `@dataclass` without explicitly depending on Pydantic schemas.
    """
    return await create_user_interactor(data)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
