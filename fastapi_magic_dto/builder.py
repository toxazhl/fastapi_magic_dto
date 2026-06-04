import dataclasses
import inspect
import typing
from typing import Annotated, Any, Dict, List, Optional, Type, TypeVar

from fastapi import Body, Cookie, Depends, Header, Path, Query
from pydantic import BaseModel, create_model

from .markers import FieldMarker

T = TypeVar("T")


def _unwrap_optional(annotation: Any) -> Any:
    """Removes `Optional` (or `| None`) from the type annotation to prevent OpenAPI duplicate nulls."""
    origin = typing.get_origin(annotation)
    if origin is typing.Union or getattr(origin, "__name__", "") == "UnionType":
        args = typing.get_args(annotation)
        if type(None) in args:
            clean_args = tuple(a for a in args if a is not type(None))
            return clean_args[0] if len(clean_args) == 1 else typing.Union[clean_args]
    return annotation


# Constraint attributes carried on Pydantic / annotated-types metadata objects that map
# 1:1 onto the validation keyword arguments accepted by FastAPI's Query/Path/Header/Cookie.
# annotated-types exposes ge/gt/le/lt/multiple_of/min_length/max_length on its own classes;
# Pydantic packs pattern/max_digits/decimal_places/allow_inf_nan into a single
# _PydanticGeneralMetadata object — getattr finds them on either.
# NOTE: ``strict`` is intentionally excluded — Path/Query/Header/Cookie values arrive as
# strings and rely on coercion, so strict mode would reject e.g. "50" for an int param.
_CONSTRAINT_ATTRS = (
    "gt",
    "ge",
    "lt",
    "le",
    "min_length",
    "max_length",
    "multiple_of",
    "pattern",
    "max_digits",
    "decimal_places",
    "allow_inf_nan",
)


def _constraints_to_kwargs(metadata: List[Any]) -> Dict[str, Any]:
    """Extract a Pydantic field's constraints into FastAPI param kwargs.

    Pydantic keeps constraints (``ge``/``le``/``max_length``/...) in ``FieldInfo.metadata`` as
    ``annotated_types`` objects, not on the bare type. They must be passed to ``Query``/``Path``
    so FastAPI validates them at the request level — otherwise they are only enforced when the
    DTO is instantiated inside the dependency, raising a ``pydantic.ValidationError`` that never
    becomes a ``RequestValidationError`` and so surfaces as a 500 instead of a 422. (FastAPI does
    not merge ``Annotated`` constraint metadata with a separate ``Query(...)`` default, so the
    values have to be lifted out explicitly.)
    """
    kwargs: Dict[str, Any] = {}
    for meta in metadata:
        for attr in _CONSTRAINT_ATTRS:
            value = getattr(meta, attr, None)
            if value is not None:
                kwargs[attr] = value
    return kwargs


def _apply_constraints(annotation: Any, metadata: List[Any]) -> Any:
    """Fold constraint metadata back into the type via ``Annotated`` (used for body fields,
    which are validated through a generated Pydantic model that reads ``Annotated`` natively)."""
    if not metadata:
        return annotation
    return Annotated[tuple([annotation, *metadata])]


def _get_fields_info(dto_class: Type[T]) -> Dict[str, Dict[str, Any]]:
    """
    Normalizes field extraction for both Pydantic BaseModels and standard Dataclasses.
    """
    fields_info = {}

    if isinstance(dto_class, type) and issubclass(dto_class, BaseModel):
        for name, field in dto_class.model_fields.items():
            fields_info[name] = {
                "annotation": field.annotation,
                "default": ... if field.is_required() else field.default,
                "is_required": field.is_required(),
                "description": field.description or "",
                "metadata": list(field.metadata),
            }
    elif dataclasses.is_dataclass(dto_class):
        for f in dataclasses.fields(dto_class):
            is_req = (
                f.default is dataclasses.MISSING
                and f.default_factory is dataclasses.MISSING
            )
            default_val = (
                ...
                if is_req
                else (
                    f.default
                    if f.default is not dataclasses.MISSING
                    else f.default_factory()  # type: ignore
                )
            )
            fields_info[f.name] = {
                "annotation": f.type,
                "default": default_val,
                "is_required": is_req,
                "description": "",  # Dataclasses don't natively support field descriptions
                "metadata": [],  # constraints, if any, already live in the Annotated type
            }
    else:
        raise TypeError(
            "MagicDTO only supports Pydantic BaseModel or standard @dataclass!"
        )

    return fields_info


def _build_dependency(dto_class: Type[T], markers: List[FieldMarker]) -> Any:
    body_fields: Dict[str, Any] = {}
    sig_params: List[inspect.Parameter] = []

    marker_map = {m.name: m.location for m in markers}
    fields_info = _get_fields_info(dto_class)

    for marker_name in marker_map:
        if marker_name not in fields_info:
            raise ValueError(
                f"Field marker '{marker_name}' not found in {dto_class.__name__}!"
            )

    for name, info in fields_info.items():
        if name in marker_map:
            location = marker_map[name]
            default_val = info["default"]
            description = info["description"]
            constraints = _constraints_to_kwargs(info["metadata"])

            if location == "path":
                param_default = Path(..., description=description, **constraints)
            elif location == "query":
                param_default = Query(default_val, description=description, **constraints)
            elif location == "header":
                param_default = Header(default_val, description=description, **constraints)
            elif location == "cookie":
                param_default = Cookie(default_val, description=description, **constraints)
            else:
                raise ValueError(f"Unknown parameter location: {location}")

            param = inspect.Parameter(
                name=name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=param_default,
                annotation=_unwrap_optional(info["annotation"]),
            )
            sig_params.append(param)
        else:
            body_fields[name] = (
                _apply_constraints(info["annotation"], info["metadata"]),
                info["default"],
            )

    if body_fields:
        body_model = create_model(f"{dto_class.__name__}Body", **body_fields)
        body_param = inspect.Parameter(
            name="body_data",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=Body(...),
            annotation=body_model,
        )
        sig_params.insert(0, body_param)

    async def _dependency(**kwargs: Any) -> T:
        body_data: Optional[BaseModel] = kwargs.pop("body_data", None)
        body_dict = body_data.model_dump(exclude_unset=True) if body_data else {}
        return dto_class(**kwargs, **body_dict)

    _dependency.__signature__ = inspect.Signature(parameters=sig_params)  # type: ignore

    return Depends(_dependency)


if typing.TYPE_CHECKING:
    MagicDTO = Annotated
else:

    class _MagicDTOMeta:
        __doc__ = """
        A type hint and dependency injector for FastAPI that aggregates Request data 
        (Path, Query, Header, Cookie, Body) into a single Pydantic model.

        Example:
        --------
        ```python
        class MyDTO(BaseModel):
            item_id: int      # From Path
            limit: int = 10   # From Query
            name: str         # From Body

        @app.post("/items/{item_id}")
        async def create_item(
            data: MagicDTO[MyDTO, P.item_id, Q.limit]
        ):
            ...
        ```
        """

        @classmethod
        def __class_getitem__(cls, params: Any) -> Any:
            if not isinstance(params, tuple) or len(params) < 2:
                raise TypeError(
                    "Invalid usage. Expected format: MagicDTO[DTOClass, P.id, Q.limit]"
                )
            dto_class = params[0]
            markers = list(params[1:])
            return Annotated[dto_class, _build_dependency(dto_class, markers)]

    MagicDTO = _MagicDTOMeta
