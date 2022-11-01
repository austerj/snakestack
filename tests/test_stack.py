import pytest

from geometric_rewards import program


def test_push():
    stack = program.Stack()
    stack.push(500).push(200)
    assert stack == [500, 200]


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


def test_stack_underflow():
    stack = program.Stack()
    stack.push(500)
    with pytest.raises(program.StackUnderflow):
        stack.add()


def test_integer_underflow():
    stack = program.Stack()
    stack.push(500).push(700)
    with pytest.raises(program.UnderflowError):
        stack.sub()
