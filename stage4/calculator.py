import ast
import math
import operator

from tool_loop import chat, run, MODEL


# =====================================================================
# THE CALCULATOR TOOL
#
# ⚠️ SECURITY: never use Python's eval() on text from an LLM!
# eval("__import__('os').system('del /s C:\\')") would run that command.
# LLM output is UNTRUSTED input, like text typed by a stranger.
#
# Instead we parse the expression into a tree (ast) and only allow
# numbers, + - * / // % **, parentheses, and a few math functions.
# Anything else is rejected.
# =====================================================================

_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
_FUNCTIONS = {"sqrt": math.sqrt, "round": round, "abs": abs}


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        if isinstance(node.op, ast.Pow) and abs(_evaluate(node.right)) > 100:
            raise ValueError("exponent too large")  # stop 9**9**9 freezing the PC
        return _OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
        return _FUNCTIONS[node.func.id](*[_evaluate(a) for a in node.args])
    raise ValueError(f"Not allowed: {ast.dump(node)[:60]}")


def calculate(expression: str) -> dict:
    """Evaluate a math expression exactly. Use this for ANY arithmetic.

    Args:
        expression: A math expression using numbers, + - * / ** % and parentheses,
            e.g. "48723 * 9617" or "15000 * (1 + 0.065) ** 12". Also supports sqrt(x).
    """
    expression = str(expression).replace(",", "").replace("×", "*").replace("^", "**")
    try:
        result = _evaluate(ast.parse(expression, mode="eval").body)
    except ZeroDivisionError:
        return {"error": "division by zero"}
    except Exception as e:
        return {"error": f"Could not calculate '{expression}': {e}"}
    if isinstance(result, float):
        result = round(result, 6)
    return {"expression": expression, "result": result}


SYSTEM_PROMPT = (
    "You are a helpful assistant. For any arithmetic, ALWAYS use the calculate tool "
    "instead of doing math in your head, then state the result clearly. "
    "Copy every number into the expression EXACTLY as written, keeping decimal points "
    "(e.g. $2,846.50 -> 2846.50). Check that the result is sensible before answering. "
    "For questions that need no math, answer directly."
)

QUESTIONS = [
    ("What is 48,723 × 9,617?", 48723 * 9617),
    ("I invest $15,000 at 6.5% interest compounded yearly. How much will I have after 12 years?",
     round(15000 * 1.065 ** 12, 2)),
    ("A team of 7 splits a $2,846.50 dinner bill equally. How much does each person pay?",
     round(2846.50 / 7, 2)),
]


if __name__ == "__main__":
    print(f"Model: {MODEL}")

    print("\n=== 0. SECURITY CHECK: the tool refuses dangerous input ===")
    print(calculate("__import__('os').system('echo hacked')"))
    print(calculate("2 ** 2 ** 2 ** 2 ** 2"))

    for question, correct in QUESTIONS:
        print("\n" + "=" * 70)
        print(f"Q: {question}")
        print(f"   ✔ Correct answer: {correct:,}")

        # WITHOUT the tool: the LLM does "mental math"
        r = chat([{"role": "user", "content": question + " Give just the final number."}])
        print(f"\n   WITHOUT calculator: {r.message.content.strip()}")

        # WITH the tool
        print("\n   WITH calculator:")
        print(f"   A: {run(question, [calculate], SYSTEM_PROMPT)}")
