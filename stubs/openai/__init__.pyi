from typing import Any

class ResponsesClient:
    def create(self, *, model: str, input: Any, max_output_tokens: int | None = ...) -> Any: ...

class OpenAI:
    responses: ResponsesClient

    def __init__(self, *, api_key: str | None = ...) -> None: ...
