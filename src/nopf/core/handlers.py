from typing import Any, Callable, Awaitable

from pydantic import BaseModel

from nopf.schema import WebhookPayload


type ModelHandler = Callable[[WebhookPayload], Awaitable[None]]
type CustomHandler = Callable[[Any], Awaitable[None]]


class ModelHook(BaseModel):
    name: str
    create: bool = False
    update: bool = False
    delete: bool = False


class Handlers:
    def __init__(self) -> None:
        self.create_handlers: dict[str, list[ModelHandler]] = {}
        self.update_handlers: dict[str, list[ModelHandler]] = {}
        self.delete_handlers: dict[str, list[ModelHandler]] = {}
        self.custom_handlers: list[CustomHandler] = []

    def add_create_handler(self, model: str, handler: ModelHandler) -> None:
        self.create_handlers.setdefault(model, []).append(handler)

    def add_update_handler(self, model: str, handler: ModelHandler) -> None:
        self.update_handlers.setdefault(model, []).append(handler)

    def add_delete_handler(self, model: str, handler: ModelHandler) -> None:
        self.delete_handlers.setdefault(model, []).append(handler)

    def add_custom_handler(self, handler: CustomHandler) -> None:
        self.custom_handlers.append(handler)

    async def invoke_create_handlers(self, payload: WebhookPayload) -> None:
        handlers = self.create_handlers.get(payload.model, [])
        for handler in handlers:
            await handler(payload)

    async def invoke_update_handlers(self, payload: WebhookPayload) -> None:
        handlers = self.update_handlers.get(payload.model, [])
        for handler in handlers:
            await handler(payload)

    async def invoke_delete_handlers(self, payload: WebhookPayload) -> None:
        handlers = self.delete_handlers.get(payload.model, [])
        for handler in handlers:
            await handler(payload)

    async def invoke_custom_handlers(self, data: Any) -> None:
        for handler in self.custom_handlers:
            await handler(data)

    def get_hooks(self) -> list[ModelHook]:
        hooks_by_name: dict[str, ModelHook] = {}

        for model in self.create_handlers.keys():
            model_hook = hooks_by_name.setdefault(model, ModelHook(name=model))
            model_hook.create = True

        for model in self.update_handlers.keys():
            model_hook = hooks_by_name.setdefault(model, ModelHook(name=model))
            model_hook.update = True

        for model in self.delete_handlers.keys():
            model_hook = hooks_by_name.setdefault(model, ModelHook(name=model))
            model_hook.delete = True

        return list(hooks_by_name.values())
