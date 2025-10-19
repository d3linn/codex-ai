from typing import Any, Generic, TypeVar

_T = TypeVar("_T")

class DeclarativeBase:
    metadata: Any

class Mapped(Generic[_T]):
    def __get__(self, instance: Any, owner: type[Any]) -> _T: ...
    def __set__(self, instance: Any, value: _T) -> None: ...

def mapped_column(*args: Any, **kwargs: Any) -> Mapped[Any]: ...

def relationship(*args: Any, **kwargs: Any) -> Mapped[Any]: ...
