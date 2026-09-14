from collections.abc import Callable
from typing import Protocol

from tictactoe.events import DomainEvent

EventHandler = Callable[[DomainEvent], None]


class EventBus(Protocol):
    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        ...

    def publish(self, event: DomainEvent) -> None:
        ...


class SimpleEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        for event_type, handlers in self._handlers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)
