"""
Calculator Tool for the Agent.

Evaluates arithmetic expressions safely using Python's `ast` module instead
of raw `eval()` — only numbers and basic math operators are permitted, so
arbitrary code execution is not possible even if the LLM passes something
unexpected.
"""

import ast
import operator

TOOL_NAME = "calculator"
TOOL_DESCRIPTION = (
    "Evaluate a math expression and return the numeric result. "
    "Supports +, -, *, /, **, %, and parentheses. "
    "Example input: '15% of 200' should be expressed as '200 * 0.15'."
)

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed.")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed.")
        return _ALLOWED_OPERATORS[op_type](_eval_node(node.left), _eval_node(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed.")
        return _ALLOWED_OPERATORS[op_type](_eval_node(node.operand))
    else:
        raise ValueError(f"Unsupported expression: {type(node).__name__}")


def run(expression: str) -> str:
    """
    Safely evaluate a math expression string.

    Args:
        expression: e.g. "200 * 0.15" or "(45 + 55) / 2"

    Returns:
        The numeric result as a string, or an error message.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception as e:
        return f"Error: could not evaluate expression ({e})."
