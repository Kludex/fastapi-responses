from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterator

from libcst.metadata.scope_provider import QualifiedName
from rich.console import Console

console = Console()


@dataclass
class Node:
    fqname: str
    locals: dict[str, QualifiedName] = field(default_factory=dict)
    called: list[QualifiedName] = field(default_factory=list)

    def __rich_repr__(self) -> Iterator[tuple[str, Any]]:
        yield "fqname", self.fqname
        yield "locals", self.locals
        yield "called", self.called


class Graph:
    """Graph representation of the call graph.

    The graph is represented as a dictionary of nodes where each node is
    represented as a list of edges.

    Example:
        {
            "a": {"b", "c"},
            "b": {"c", "d"},
            "c": {"d"},
            "d": {"c"},
            "e": {"f"},
            "f": {"c"},
        }
    """

    def __init__(self) -> None:
        self.graph: defaultdict[str, set[str]] = defaultdict(set)

    def add_node(self, node: Node) -> None:
        for called in self._normalize_called(node):
            self.graph[node.fqname].add(called)

    # TODO: This method shouldn't be on `Graph`.
    def _normalize_called(self, node: Node) -> Iterator[str]:
        for called in node.called:
            if "<locals>" not in called.name:
                yield called.name
            else:
                call_path = called.name.split("<locals>.")[1]
                var_name = call_path.split(".")[0]
                for name, fqname in node.locals.items():
                    if var_name.startswith(name):
                        yield fqname.name + call_path.removeprefix(var_name)

    def __rich_repr__(self) -> Iterator[tuple[str, defaultdict[str, set[str]]]]:
        yield "graph", self.graph


if __name__ == "__main__":
    graph = Graph()
