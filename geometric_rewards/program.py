from __future__ import annotations

import typing
from dataclasses import dataclass


class UnderflowError(Exception):
    ...


class StackUnderflow(Exception):
    ...


@dataclass(repr=False)
class Stack(list[int]):
    bit: int = 64
    enforce_constraints: bool = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list.__repr__(self)})"

    def _apply(self, operation: typing.Callable[[int, int], int]) -> Stack:
        if len(self) < 2:
            raise StackUnderflow
        other = self.pop()
        self.append(value := operation(self.pop(), other))
        if self.enforce_constraints:
            if value.bit_length() > self.bit:
                raise OverflowError
            elif value < 0:
                raise UnderflowError
        return self

    def add(self) -> Stack:
        return self._apply(int.__add__)

    def sub(self) -> Stack:
        return self._apply(int.__sub__)

    def shl(self) -> Stack:
        return self._apply(int.__lshift__)

    def shr(self) -> Stack:
        return self._apply(int.__rshift__)

    def mul(self) -> Stack:
        return self._apply(int.__mul__)

    def div(self) -> Stack:
        return self._apply(int.__floordiv__)

    def push(self, value: int) -> Stack:
        self.append(value)
        return self
