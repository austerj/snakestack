from __future__ import annotations

import typing
from dataclasses import dataclass, field


class UnderflowError(Exception):
    ...


class StackUnderflow(Exception):
    ...


def instruction(func):
    def inner(self, *args):
        self._instructions.append((func.__name__, args, self.copy()))
        return func(self, *args)

    return inner


@dataclass(frozen=True, slots=True, repr=False)
class Stack(list[int]):
    bit: int = 64
    _instructions: list[str] = field(default_factory=list)
    enforce_constraints: bool = True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list.__repr__(self)})"

    @staticmethod
    def _fmt(instruct, op_padding: int, stack_padding: int):
        args = " ".join(str(arg) for arg in instruct[1])
        return f"{f'{instruct[0]:{op_padding}} {args:{stack_padding}}'}# {instruct[2]}"

    @property
    def program(self) -> str:
        op_padding = max(len(x[0]) for x in self._instructions)
        stack_padding = max(len(str(x[1])) for x in self._instructions) - 2
        return "\n".join(self._fmt(x, op_padding, stack_padding) for x in self._instructions)

    def _apply(self, operation: typing.Callable[[int, int], int]) -> Stack:
        if len(self) < 2:
            raise StackUnderflow
        other = list.pop(self)
        self.append(value := operation(list.pop(self), other))
        if self.enforce_constraints:
            if value.bit_length() > self.bit:
                raise OverflowError
            elif value < 0:
                raise UnderflowError
        return self

    @instruction
    def add(self) -> Stack:
        return self._apply(int.__add__)

    @instruction
    def sub(self) -> Stack:
        return self._apply(int.__sub__)

    @instruction
    def shl(self) -> Stack:
        return self._apply(int.__lshift__)

    @instruction
    def shr(self) -> Stack:
        return self._apply(int.__rshift__)

    @instruction
    def mul(self) -> Stack:
        return self._apply(int.__mul__)

    @instruction
    def div(self) -> Stack:
        return self._apply(int.__floordiv__)

    @instruction
    def push(self, value: int) -> Stack:
        self.append(value)
        return self

    @instruction
    def pop(self) -> Stack:
        list.pop(self)
        return self

    def peek(self) -> int:
        return self[-1]
