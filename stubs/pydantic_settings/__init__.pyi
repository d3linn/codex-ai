from typing import Any, ClassVar

from pydantic import BaseModel

class SettingsConfigDict(dict[str, Any]):
    ...

class BaseSettings(BaseModel):
    model_config: ClassVar[Any]
    def __init__(self, **values: Any) -> None: ...
    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...
