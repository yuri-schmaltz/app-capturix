from __future__ import annotations

from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


class UndoStack(Generic[T]):
    def __init__(self, max_depth: int = 50):
        self._stack: List[T] = []
        self._redo_stack: List[T] = []
        self._max_depth = max_depth

    def push(self, state: T) -> None:
        self._stack.append(state)
        if len(self._stack) > self._max_depth:
            self._stack.pop(0)
        self._redo_stack.clear()

    def can_undo(self) -> bool:
        return len(self._stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def undo(self, current: T) -> Optional[T]:
        if not self._stack:
            return None
        last = self._stack.pop()
        self._redo_stack.append(current)
        return last

    def redo(self, current: T) -> Optional[T]:
        if not self._redo_stack:
            return None
        next_state = self._redo_stack.pop()
        self._stack.append(current)
        return next_state

    def clear(self) -> None:
        self._stack.clear()
        self._redo_stack.clear()
