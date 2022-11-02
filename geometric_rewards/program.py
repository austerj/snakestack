from __future__ import annotations

import types
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class UnderflowError(Exception):
    ...


class StackUnderflowError(Exception):
    ...


class FrozenStackError(Exception):
    ...


class EmptyTraceError(Exception):
    ...


def instruction(func):
    def inner(self: Stack, *args) -> Stack:
        if self.frozen:
            raise FrozenStackError()
        stack = func(self, *args)
        if self.debug:
            self.trace.append((func.__name__, args, stack.copy()))
        # raise Exception if function raised one
        if isinstance(exception := self.peek(), Exception):
            raise exception
        return stack

    return inner


@dataclass(frozen=True, slots=True, repr=False)
class Stack(list[int]):
    bits: int = 64
    signed: bool = False
    debug: bool = True
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
        if not self.trace:
            raise EmptyTraceError()
        operands_padding = max(len(x[0]) for x in self.trace if len(x) > 1)
        stack_padding = max(len(str(x[1])) for x in self.trace if len(x) > 2) - 2
        return "\n".join(self._fmt(x, operands_padding, stack_padding) for x in self.trace)

    def print(self) -> None:
        """Print sequence of instructions and stacktrace."""
        print(self.statements)

    def freeze(self) -> None:
        object.__setattr__(self, "frozen", True)

    def _raise(self, exception: Exception) -> Stack:
        self.append(exception)  # type: ignore
        self.freeze()  # freeze stack at Exception - further instructions are not valid
        return self

    def _binary_exec(self, instruction: typing.Callable[[int, int], int]) -> Stack:
        # freeze further instructions if Exception is on stack or stack has been manually frozen
        if len(self) < 2:
            return self._raise(StackUnderflowError())
        other = list.pop(self)
        value = instruction(list.pop(self), other)
        if self.signed:
            # NOTE: bit_length always returns bits excluding sign, so need to account for this
            if value.bit_length() > self.bits - int(self.signed):
                return self._raise(OverflowError())
            elif not self.signed and value < 0:
                return self._raise(UnderflowError())
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
        if self.signed and value < 0:
            return self._raise(UnderflowError())
        self.append(value)
        return self

    @instruction
    def pop(self) -> Stack:
        list.pop(self)
        return self

    @instruction
    def dup(self) -> Stack:
        if self.is_empty:
            return self._raise(StackUnderflowError())
        self.append(self[-1])
        return self

    @instruction
    def store(self, slot: int) -> Stack:
        if self.is_empty:
            return self._raise(StackUnderflowError())
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
        if self.debug:
            self.trace.append((f"; {cmt}",))
        return self


@dataclass(frozen=True, slots=True, repr=False)
class CallStack:
    program: Program
    stack: Stack

    def __enter__(self) -> Stack:
        return self.stack.__enter__()

    def __exit__(self, type, value, traceback) -> None:
        self.program.stack = self.stack
        return self.stack.__exit__(type, value, traceback)


@dataclass(slots=True)
class Program(ABC):
    stack: Stack | None = field(default=None, init=False)
    bits: int = field(default=64, kw_only=True)
    signed: bool = field(default=False, kw_only=True)
    debug: bool = field(default=False, kw_only=True)

    def _call(self) -> CallStack:
        return CallStack(self, Stack(self.bits, self.signed, self.debug))

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Stack:
        raise NotImplementedError
