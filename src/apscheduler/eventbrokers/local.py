from __future__ import annotations

from asyncio import iscoroutinefunction
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from threading import Lock
from typing import Any, Callable, Iterable, Optional

import attr

from ..abc import Subscription
from ..events import Event
from ..util import reentrant
from .base import BaseEventBroker


@reentrant
@attr.define(eq=False)
class LocalEventBroker(BaseEventBroker):
    _executor: ThreadPoolExecutor = attr.field(init=False)
    _exit_stack: ExitStack = attr.field(init=False)
    _subscriptions_lock: Lock = attr.field(init=False, factory=Lock)

    def __enter__(self):
        self._exit_stack = ExitStack()
        self._executor = self._exit_stack.enter_context(ThreadPoolExecutor(1))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
        del self._executor

    def subscribe(self, callback: Callable[[Event], Any],
                  event_types: Optional[Iterable[type[Event]]] = None, *,
                  one_shot: bool = False) -> Subscription:
        if iscoroutinefunction(callback):
            raise ValueError('Coroutine functions are not supported as callbacks on a synchronous '
                             'event source')

        with self._subscriptions_lock:
            return super().subscribe(callback, event_types, one_shot=one_shot)

    def unsubscribe(self, token: object) -> None:
        with self._subscriptions_lock:
            super().unsubscribe(token)

    def publish(self, event: Event) -> None:
        self.publish_local(event)

    def publish_local(self, event: Event) -> None:
        event_type = type(event)
        with self._subscriptions_lock:
            one_shot_tokens: list[object] = []
            for token, subscription in self._subscriptions.items():
                if subscription.event_types is None or event_type in subscription.event_types:
                    self._executor.submit(self._deliver_event, subscription.callback, event)
                    if subscription.one_shot:
                        one_shot_tokens.append(subscription.token)

            for token in one_shot_tokens:
                super().unsubscribe(token)

    def _deliver_event(self, func: Callable[[Event], Any], event: Event) -> None:
        try:
            func(event)
        except BaseException:
            self._logger.exception('Error delivering %s event', event.__class__.__name__)
