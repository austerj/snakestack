from __future__ import annotations

import types
import typing
from dataclasses import dataclass, field


class UnderflowError(Exception):
    ...


class StackUnderflow(Exception):
    ...


def instruction(func):
    def inner(self: Stack, *args) -> Stack:
        stack = func(self, *args)
        self._stacktrace.append((func.__name__, args, stack.copy()))
        return stack

    return inner


@dataclass(frozen=True, slots=True, repr=False)
class Stack(list[int]):
    bit: int = 64
    enforce_constraints: bool = True
    _stacktrace: list[tuple] = field(default_factory=list, init=False)
    _registers: dict[int, int] = field(default_factory=dict, init=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list.__repr__(self)})"

    @staticmethod
    def _fmt(instruct, instruction_padding: int, stack_padding: int):
        if len(instruct) == 1:  # comment
            return instruct[0]
        args = " ".join(str(arg) for arg in instruct[1])
        return f"{f'{instruct[0]:{instruction_padding}} {args:{stack_padding}}'}# {instruct[2]}"

    @property
    def program(self) -> str:
        instruction_padding = max(len(x[0]) for x in self._stacktrace if len(x) > 1)
        stack_padding = max(len(str(x[1])) for x in self._stacktrace if len(x) > 2) - 2
        return "\n".join(self._fmt(x, instruction_padding, stack_padding) for x in self._stacktrace)

    def _binary_exec(self, instruction: typing.Callable[[int, int], int]) -> Stack:
        if len(self) < 2:
            raise StackUnderflow
        other = list.pop(self)
        self.append(value := instruction(list.pop(self), other))
        if self.enforce_constraints:
            if value.bit_length() > self.bit:
                raise OverflowError
            elif value < 0:
                raise UnderflowError
        return self

    @instruction
    def add(self) -> Stack:
        return self._binary_exec(int.__add__)

    @instruction
    def sub(self) -> Stack:
        return self._binary_exec(int.__sub__)

    @instruction
    def shl(self) -> Stack:
        return self._binary_exec(int.__lshift__)

    @instruction
    def shr(self) -> Stack:
        return self._binary_exec(int.__rshift__)

    @instruction
    def mul(self) -> Stack:
        return self._binary_exec(int.__mul__)

    @instruction
    def div(self) -> Stack:
        return self._binary_exec(int.__floordiv__)

    @instruction
    def push(self, value: int) -> Stack:
        if self.enforce_constraints and value < 0:
            raise UnderflowError
        self.append(value)
        return self

    @instruction
    def pop(self) -> Stack:
        list.pop(self)
        return self

    @instruction
    def dup(self) -> Stack:
        self.append(self.peek())
        return self

    @instruction
    def store(self, slot: int) -> Stack:
        self._registers[slot] = self.peek()
        return self

    @instruction
    def load(self, slot: int) -> Stack:
        self.append(int(self._registers[slot]))
        return self

    def exec(self, instruction: str, *args) -> Stack:
        if not hasattr(self, instruction) or not isinstance(method := getattr(self, instruction), types.MethodType):
            raise ValueError(f"Invalid instruction: '{instruction}'")
        return method(*args)

    def peek(self) -> int:
        return self[-1]

    def comment(self, cmt) -> Stack:
        self._stacktrace.append((f"; {cmt}",))
        return self
