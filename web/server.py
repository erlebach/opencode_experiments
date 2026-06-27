"""Arithmetic expression evaluator — Flask backend."""

import ast
import operator
import sys
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Supported operators
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(node):
    """Recursively evaluate an AST node containing only numeric literals and
    supported binary/unary arithmetic operators. Raises ValueError on
    anything else."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        op_type = type(node.op)
        if op_type not in _OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _OPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = safe_eval(node.operand)
        op_type = type(node.op)
        if op_type not in _OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _OPS[op_type](operand)
    raise ValueError("Expression contains unsupported constructs")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/eval", methods=["POST"])
def evaluate():
    data = request.get_json(silent=True) or {}
    expr = (data.get("expression") or "").strip()

    if not expr:
        return jsonify({"error": "Empty expression"}), 400

    try:
        tree = ast.parse(expr, mode="eval")
        result = safe_eval(tree.body)
        # Clean up float formatting
        if isinstance(result, float):
            result = float(f"{result:.10g}")
        return jsonify({"expression": expr, "result": result})
    except SyntaxError as e:
        return jsonify({"error": f"Syntax error: {e.msg}"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except ZeroDivisionError:
        return jsonify({"error": "Division by zero"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
