import pytest

from geometric_rewards import program


def test_push():
    stack = program.Stack()
    stack.push(500).push(200)
    assert stack == [500, 200]


def test_pop():
    stack = program.Stack()
    stack.push(500).push(200).pop()
    assert stack == [500]


def test_dup():
    stack = program.Stack()
    stack.push(500).dup()
    assert stack == [500, 500]


def test_peek():
    stack = program.Stack()
    stack.push(500).push(200)
    assert stack.peek() == 200


def test_add():
    stack = program.Stack()
    stack.push(500).push(200)
    assert stack.add() == [500 + 200]


def test_sub():
    stack = program.Stack()
    stack.push(500).push(200)
    assert stack.sub() == [500 - 200]


def test_mul():
    stack = program.Stack()
    stack.push(500).push(200)
    assert stack.mul() == [500 * 200]


def test_div():
    stack = program.Stack()
    stack.push(500).push(200)
    assert stack.div() == [500 // 200]


def test_shl():
    stack = program.Stack()
    stack.push(500).push(2)
    assert stack.shl() == [500 << 2]


def test_shr():
    stack = program.Stack()
    stack.push(500).push(2)
    assert stack.shr() == [500 >> 2]


def test_generic_exec():
    stack = program.Stack()
    stack.exec("push", 500).exec("push", 200).exec("add")
    assert stack == [700]


def test_stack_underflow():
    stack = program.Stack()
    stack.push(500)
    with pytest.raises(program.StackUnderflow):
        stack.add()
    assert isinstance(stack.peek(), program.StackUnderflow)


def test_integer_underflow():
    stack = program.Stack()
    stack.push(500).push(700)
    with pytest.raises(program.UnderflowError):
        stack.sub()
    assert isinstance(stack.peek(), program.UnderflowError)


def test_store_load():
    stack = program.Stack()
    stack.push(500).store(0).push(200).add().store(1).pop().load(0).load(1)
    assert stack == [500, 700]


def test_frozen_stack():
    stack = program.Stack()
    stack.push(500).push(700)
    # UnderflowError is stored on stacktrace
    with pytest.raises(program.UnderflowError):
        stack.sub()
    assert isinstance(stack.peek(), program.UnderflowError)
    initial_stack = stack.copy()
    # attempting an additional operation raises FrozenStack exception
    with pytest.raises(program.FrozenStack):
        stack.sub()
    # stacktrace is unaffected
    assert stack == initial_stack
