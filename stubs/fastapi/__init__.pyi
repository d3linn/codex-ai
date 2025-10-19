from typing import Any, Callable, TypeVar

_TCallable = TypeVar("_TCallable", bound=Callable[..., Any])

class APIRouter:
    def __init__(self, *, prefix: str | None = ..., tags: list[str] | None = ...) -> None: ...
    def include_router(self, router: "APIRouter", *, prefix: str | None = ..., tags: list[str] | None = ...) -> None: ...
    def get(
        self,
        path: str,
        *,
        response_model: Any | None = ...,
        status_code: int | None = ...,
        tags: list[str] | None = ...,
    ) -> Callable[[_TCallable], _TCallable]: ...
    def post(
        self,
        path: str,
        *,
        response_model: Any | None = ...,
        status_code: int | None = ...,
        tags: list[str] | None = ...,
    ) -> Callable[[_TCallable], _TCallable]: ...
    def put(
        self,
        path: str,
        *,
        response_model: Any | None = ...,
        status_code: int | None = ...,
        tags: list[str] | None = ...,
    ) -> Callable[[_TCallable], _TCallable]: ...
    def delete(
        self,
        path: str,
        *,
        response_model: Any | None = ...,
        status_code: int | None = ...,
        tags: list[str] | None = ...,
    ) -> Callable[[_TCallable], _TCallable]: ...

class FastAPI:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def include_router(self, router: APIRouter, *, prefix: str | None = ..., tags: list[str] | None = ...) -> None: ...
    def on_event(self, event_type: str) -> Callable[[_TCallable], _TCallable]: ...

class HTTPException(Exception):
    def __init__(self, *, status_code: int, detail: Any = ...) -> None: ...

class _Depends:
    def __call__(self, dependency: Any) -> Any: ...

def Depends(dependency: Any) -> Any: ...

class _Status:
    HTTP_200_OK: int
    HTTP_201_CREATED: int
    HTTP_204_NO_CONTENT: int
    HTTP_400_BAD_REQUEST: int
    HTTP_401_UNAUTHORIZED: int
    HTTP_403_FORBIDDEN: int
    HTTP_404_NOT_FOUND: int

status: _Status
