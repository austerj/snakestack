from __future__ import annotations

import types
import typing
from dataclasses import dataclass, field


class UnderflowError(Exception):
    ...


class StackUnderflow(Exception):
    ...


class FrozenStack(Exception):
    ...


def instruction(func):
    def inner(self: Stack, *args) -> Stack:
        if self.frozen:
            raise FrozenStack()
        stack = func(self, *args)
        self.trace.append((func.__name__, args, stack.copy()))
        # raise Exception if function raised one
        if isinstance(exception := self.peek(), Exception):
            raise exception
        return stack

    return inner


@dataclass(frozen=True, slots=True, repr=False)
class Stack(list[int]):
    bit: int = 64
    enforce_constraints: bool = True
    trace: list[tuple] = field(default_factory=list, init=False)
    registers: dict[int, int] = field(default_factory=dict, init=False)
    frozen: bool = field(default=False, init=False, compare=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list.__repr__(self)})"

    def __enter__(self) -> Stack:
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.freeze()

    @staticmethod
    def _fmt(statement, operands_padding: int, stack_padding: int) -> str:
        if len(statement) == 1:  # comment
            return statement[0]
        operands = " ".join(str(arg) for arg in statement[1])
        return f"{f'{statement[0]:{operands_padding}} {operands:{stack_padding}}'}# {statement[2]}"

    @property
    def statements(self) -> str:
        operands_padding = max(len(x[0]) for x in self.trace if len(x) > 1)
        stack_padding = max(len(str(x[1])) for x in self.trace if len(x) > 2) - 2
        return "\n".join(self._fmt(x, operands_padding, stack_padding) for x in self.trace)

    def print(self) -> None:
        """Print sequence of instructions and stacktrace."""
        print(self.statements)

    def freeze(self) -> None:
        object.__setattr__(self, "frozen", True)

    def __raise(self, exception: Exception) -> Stack:
        self.append(exception)  # type: ignore
        self.freeze()  # freeze stack at Exception - further instructions are not valid
        return self

    def _binary_exec(self, instruction: typing.Callable[[int, int], int]) -> Stack:
        # freeze further instructions if Exception is on stack or stack has been manually frozen
        if len(self) < 2:
            return self.__raise(StackUnderflow())
        other = list.pop(self)
        value = instruction(list.pop(self), other)
        if self.enforce_constraints:
            if value.bit_length() > self.bit:
                return self.__raise(OverflowError())
            elif value < 0:
                return self.__raise(UnderflowError())
        self.append(value)
        return self

    @property
    def is_empty(self) -> bool:
        return not bool(len(self))

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
            return self.__raise(UnderflowError())
        self.append(value)
        return self

    @instruction
    def pop(self) -> Stack:
        list.pop(self)
        return self

    @instruction
    def dup(self) -> Stack:
        if self.is_empty:
            return self.__raise(StackUnderflow())
        self.append(self[-1])
        return self

    @instruction
    def store(self, slot: int) -> Stack:
        if self.is_empty:
            return self.__raise(StackUnderflow())
        self.registers[slot] = self[-1]
        return self

    @instruction
    def load(self, slot: int) -> Stack:
        self.append(int(self.registers[slot]))
        return self

    def exec(self, instruction: str, *args) -> Stack:
        if not hasattr(self, instruction) or not isinstance(method := getattr(self, instruction), types.MethodType):
            raise ValueError(f"Invalid instruction: '{instruction}'")
        return method(*args)

    def peek(self) -> int | None:
        if self.is_empty:
            return None
        return self[-1]

    def comment(self, cmt) -> Stack:
        self.trace.append((f"; {cmt}",))
        return self
