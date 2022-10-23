"""
NOTE: This is actually for the whole fastapi-responses. For this module it's only step
    2.

The logic of this codemod can be seen in some steps:

1. Find where exceptions in code are being used.
2. Create a graph of calls e.g. `func1` calls `func2` which calls `func3` which raises
    `MyException`.
3. Check if the endpoint function raises any of the exceptions found.
"""

from __future__ import annotations

from collections import deque
from typing import cast

import libcst as cst
import libcst.matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.metadata import FullyQualifiedNameProvider
from rich.console import Console

from fastapi_responses.graph import Graph, Node

console = Console()


class FindExceptionsCommand(VisitorBasedCodemodCommand):
    @m.visit(m.Raise())
    def visit_raise(self, node: cst.Raise) -> None:
        print(node)


class CallGraphCommand(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (FullyQualifiedNameProvider,)

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self.context.scratch["call_graph"] = Graph()
        self.caller_queue: deque[Node] = deque()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Create the graph node for the function, and add it to the caller queue.

        The caller queue is used to keep track of the current function that is being
        visited. Local functions are not added to the graph, but their calls are added
        to the caller function. This is based on the assumption that, as the local
        function cannot be reached from outside, it means that it is only called from
        the caller function.
        """
        fqnames = self.get_metadata(FullyQualifiedNameProvider, node)
        for fqname in fqnames:
            if "<locals>" in fqname.name:
                continue
            graph_node = Node(fqname=fqname.name)
            self.caller_queue.append(graph_node)
            return None

    def visit_Assign(self, node: cst.Assign) -> None:
        """Add the local variables to the current caller node.

        Each `Assign` node has a list of targets, and a value. The targets are the
        variables that are being assigned, and the value is the expression that is
        being assigned to the variables.
        """
        fqnames = self.get_metadata(FullyQualifiedNameProvider, node.value)
        for target in node.targets:
            target = cst.ensure_type(target, cst.AssignTarget)
            if m.matches(target.target, m.Name()):
                name = cast(cst.Name, target.target).value
                for fqname in fqnames:
                    self.caller_queue[-1].locals[name] = fqname
                    return None

    @m.call_if_inside(m.FunctionDef())
    @m.visit(
        m.SimpleStatementLine(
            body=[m.ZeroOrMore(), m.Expr(value=m.Call()), m.ZeroOrMore()]
        )
    )
    def visit_simple_statement_line(self, node: cst.SimpleStatementLine) -> None:
        """Add the calls to the current caller node."""
        for statement in node.body:
            if m.matches(statement, m.Expr(value=m.Call())):
                statement = cst.ensure_type(statement, cst.Expr)
                call = cst.ensure_type(statement.value, cst.Call)
                fqnames = self.get_metadata(FullyQualifiedNameProvider, call)
                self.caller_queue[-1].called.extend(fqnames)

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Add the current caller node to the graph, and remove it from the queue."""
        fqnames = self.get_metadata(FullyQualifiedNameProvider, original_node)
        for fqname in fqnames:
            if "<locals>" in fqname.name:
                return updated_node
        graph_node = self.caller_queue.pop()
        self.context.scratch["call_graph"].add_node(graph_node)
        return updated_node
