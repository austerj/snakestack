from dataclasses import dataclass

from geometric_rewards import program


def test_equivalence():
    @dataclass(slots=True)
    class TestProgram(program.Program):
        def __call__(self, x: int) -> program.Stack:
            with self._call() as stack:
                stack.push(x).push(200).add().push(x).mul()
            return stack

    for x in [300, 500, 700]:
        assert TestProgram()(x) == [(x + 200) * x]
