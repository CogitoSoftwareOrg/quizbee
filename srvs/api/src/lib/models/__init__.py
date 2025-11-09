from typing import (
    TypeVar,
    Type,
    Union,
    cast,
    Optional,
    get_args,
    get_origin,
    Any,
)
from dataclasses import make_dataclass, fields, Field, MISSING, is_dataclass

T = TypeVar("T")

_cache: dict[Type[Any], Type[Any]] = {}


class _PartialMeta(type):
    """Metaclass that enables both Partial[T] syntax for type annotations."""

    def __getitem__(cls, item: Type[T]) -> Type[T]:
        """Support Partial[Material] syntax for type annotations."""
        return _make_partial(item)


def _make_partial(cls: Type[T]) -> Type[T]:
    """Internal function to create partial dataclass."""
    # Validate that cls is a dataclass
    if not is_dataclass(cls):
        raise TypeError(f"{cls} must be a dataclass")

    # Check cache first
    if cls in _cache:
        return _cache[cls]  # type: ignore[return-value]

    field_defs = []
    for f in fields(cls):  # type: ignore[arg-type]
        # Check if field is already optional
        origin = get_origin(f.type)
        if origin is Union:
            args = get_args(f.type)
            # If None is already in the union, keep it as is
            if type(None) in args:
                new_type = f.type
            else:
                new_type = Union[f.type, type(None)]
        else:
            # Make field optional
            new_type = Optional[f.type]

        # Set default to None if not already set
        if f.default is not MISSING:
            field_defs.append((f.name, new_type, f.default))
        elif f.default_factory is not MISSING:  # type: ignore[misc]
            field_defs.append(
                (f.name, new_type, Field(default_factory=f.default_factory))  # type: ignore[misc]
            )
        else:
            field_defs.append((f.name, new_type, None))

    # Create new dataclass
    partial_cls = make_dataclass(
        f"Partial{cls.__name__}",
        field_defs,
        frozen=False,
    )

    # Cache the result
    _cache[cls] = partial_cls
    return cast(Type[T], partial_cls)


class Partial(metaclass=_PartialMeta):
    """
    Creates a new dataclass type with all fields made optional (type | None) and defaulted to None.

    Usage in type annotations:
        @dataclass
        class Material:
            title: str
            user_id: str
            status: str

        # Use in function signature - type checkers will understand this
        async def update(self, m_id: str, dto: Partial[Material]) -> Material:
            ...

    Note: For runtime usage, call _make_partial(Material) directly.
    The Partial[Material] syntax is primarily for static type checking.
    """

    def __class_getitem__(cls, item: Type[T]) -> Type[T]:
        """Support Partial[Material] syntax for better type checker compatibility."""
        return _make_partial(item)
