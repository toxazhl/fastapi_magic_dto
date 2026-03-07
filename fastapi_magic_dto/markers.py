import typing
from typing import Any


class FieldMarker:
    """
    Represents a specific field's origin location in the HTTP request.
    Created dynamically by P, Q, H, or C builders.
    """

    __slots__ = ("location", "name")

    def __init__(self, location: str, name: str) -> None:
        self.location = location
        self.name = name


if typing.TYPE_CHECKING:

    class _DummyMarkerBuilder:
        __doc__ = """
            Dynamic marker builder for FastAPI Magic DTO.
            Use this to specify where a field should be extracted from.

            Available markers:
            - `P`: Path parameters
            - `Q`: Query parameters
            - `H`: Header parameters
            - `C`: Cookie parameters

            Example:
                `MagicDTO[MyDTO, P.item_id, Q.limit, H.user_agent, C.session]`
            """

        def __getattr__(self, item: str) -> Any: ...

    P = _DummyMarkerBuilder()
    Q = _DummyMarkerBuilder()
    H = _DummyMarkerBuilder()
    C = _DummyMarkerBuilder()
else:

    class _MarkerBuilder:
        __slots__ = ("location",)

        def __init__(self, location: str) -> None:
            self.location = location

        def __getattr__(self, item: str) -> FieldMarker:
            return FieldMarker(self.location, item)

    P = _MarkerBuilder("path")
    Q = _MarkerBuilder("query")
    H = _MarkerBuilder("header")
    C = _MarkerBuilder("cookie")
