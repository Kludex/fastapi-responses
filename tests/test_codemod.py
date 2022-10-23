import textwrap

import libcst as cst
import pytest
from libcst.codemod import CodemodContext
from libcst.metadata import FullRepoManager, FullyQualifiedNameProvider

from fastapi_responses.codemods.call_graph import CallGraphCommand


@pytest.mark.parametrize(
    "source, graph",
    [
        pytest.param(
            textwrap.dedent(
                """
                def a():
                    b()

                def b():
                    ...
                """
            ),
            {"main.a": {"main.b"}},
            id="simple",
        ),
        pytest.param(
            textwrap.dedent(
                """
                from pathlib import Path

                def a():
                    path = Path("potato")
                    path.exists()
                """
            ),
            {"main.a": {"pathlib.Path.exists"}},
            id="external call",
        ),
        pytest.param(
            textwrap.dedent(
                """
                class Potato:
                    def get(self):
                        ...

                def a():
                    potato = Potato()
                    potato.get()
                """
            ),
            {"main.a": {"main.Potato.get"}},
            id="class call",
        ),
        pytest.param(
            textwrap.dedent(
                """
                def a():
                    b()
                    c()

                def b():
                    ...

                def c():
                    ...
                """
            ),
            {"main.a": {"main.b", "main.c"}},
            id="multiple calls",
        ),
        pytest.param(
            textwrap.dedent(
                """
                class Potato:
                    def get(self):
                        ...

                    def __call__(self):
                        self.get()
                """
            ),
            {"main.Potato.__call__": {"main.Potato.get"}},
            id="internal class call",
            marks=pytest.mark.xfail,
        ),
        pytest.param(
            textwrap.dedent(
                """
                def a():
                    b()
                    if True:
                        c()

                def b():
                    ...

                def c():
                    ...
                """
            ),
            {"main.a": {"main.b", "main.c"}},
            id="indent block",
        ),
        pytest.param(
            textwrap.dedent(
                """
                def a():
                    def b():
                        c()
                    b()

                def c():
                    ...
                """
            ),
            {"main.a": {"main.c"}},
            id="nested function",
        ),
        pytest.param(
            textwrap.dedent(
                """
                from contextlib import contextmanager

                def a():
                    with b():
                        ...

                @contextmanager
                def b():
                    yield
                """,
            ),
            {"main.a": {"main.b"}},
            id="context manager",
            marks=pytest.mark.xfail,
        ),
        pytest.param(
            textwrap.dedent(
                """
                def decorator(func):
                    def wrapper():
                        return func()
                    return wrapper

                def a():
                    b()

                @decorator
                def b():
                    ...
                """
            ),
            {"main.a": {"main.b"}},
            id="decorator",
        ),
    ],
)
def test_call_graph(source: str, graph: dict[str, set[str]]) -> None:
    mod = cst.parse_module(source)
    mgr = FullRepoManager(".", {"main.py"}, {FullyQualifiedNameProvider})
    wrapper = mgr.get_metadata_wrapper_for_path("main.py")
    context = CodemodContext(wrapper=wrapper, filename="main.py", metadata_manager=mgr)
    CallGraphCommand(context).transform_module(mod)
    assert context.scratch["call_graph"].graph == graph
