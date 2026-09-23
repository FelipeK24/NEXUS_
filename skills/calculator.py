from __future__ import annotations

import ast
import operator
import re
from typing import Any

_OPERATORS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_WORD_REPLACEMENTS = [
    (r"\bmais\b", "+"),
    (r"\bmenos\b", "-"),
    (r"\bvezes\b", "*"),
    (r"\bdividido por\b", "/"),
    (r"\bdividido\b", "/"),
    (r"\bx\b", "*"),
]


def _safe_eval(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _safe_eval(node.operand)
        return +value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ZeroDivisionError
        if isinstance(node.op, ast.Pow) and abs(right) > 12:
            raise ValueError("Potência muito grande.")
        return _OPERATORS[type(node.op)](left, right)
    raise ValueError("Expressão não permitida.")


def calcular(expression: str) -> str:
    expression = expression.strip().rstrip("?")
    for pattern, replacement in _WORD_REPLACEMENTS:
        expression = re.sub(pattern, replacement, expression, flags=re.IGNORECASE)
    expression = re.sub(r"[^0-9+\-*/%.()\s]", "", expression)
    expression = expression.replace("%", "/100")
    if not expression or not re.search(r"\d", expression):
        return "Não consegui identificar a conta."

    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"O resultado é {result}."
    except ZeroDivisionError:
        return "Não posso dividir por zero."
    except Exception:
        return "Não consegui calcular essa expressão com segurança."
