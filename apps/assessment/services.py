import ast
import operator
from math import ceil

class FormulaValidator:
    """
    Securely validates and evaluates mathematical formulas for Assessment Components.
    Supports basic arithmetic (+, -, *, /) and parentheses.
    """
    
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg
    }

    def __init__(self, formula_string, variables_dict):
        """
        formula_string: e.g. "(I1 + I2)/2 + FE"
        variables_dict: e.g. {"I1": 30, "I2": 30, "FE": 10} mapping var name to max_marks
        """
        self.formula_string = formula_string
        self.variables_dict = variables_dict
        self.errors = []

    def validate(self, expected_max):
        """
        Returns True if the formula parses successfully and its maximum possible
        evaluation exactly matches the expected_max.
        """
        if not self.formula_string:
            self.errors.append("Formula cannot be empty.")
            return False

        try:
            tree = ast.parse(self.formula_string, mode='eval')
        except SyntaxError as e:
            self.errors.append(f"Syntax error in formula: {str(e)}")
            return False

        # 1. Validate variables and allowed nodes
        if not self._check_nodes(tree.body):
            return False

        # 2. Evaluate maximum possible score
        try:
            max_score = self._eval_node(tree.body)
        except Exception as e:
            self.errors.append(f"Evaluation error: {str(e)}")
            return False

        # Math division can result in floats, we should round or use ceiling.
        # Most universities round up for max possible marks, but let's allow a tiny float tolerance.
        if abs(max_score - expected_max) > 0.01:
            self.errors.append(f"Formula max evaluates to {max_score}, but parent max is {expected_max}.")
            return False

        return True

    def _check_nodes(self, node):
        """Recursively checks if all AST nodes are allowed (constants, binops, variables)."""
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                self.errors.append(f"Invalid constant type: {type(node.value).__name__}")
                return False
            return True
        elif isinstance(node, ast.Name):
            if node.id not in self.variables_dict:
                self.errors.append(f"Unknown variable: '{node.id}'")
                return False
            return True
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self.ALLOWED_OPERATORS:
                self.errors.append(f"Unsupported operator: {type(node.op).__name__}")
                return False
            return self._check_nodes(node.left) and self._check_nodes(node.right)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.ALLOWED_OPERATORS:
                self.errors.append(f"Unsupported unary operator: {type(node.op).__name__}")
                return False
            return self._check_nodes(node.operand)
        else:
            self.errors.append(f"Unsupported expression construct: {type(node).__name__}")
            return False

    def _eval_node(self, node):
        """Recursively evaluates the maximum value of the expression."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return self.variables_dict[node.id]
        elif isinstance(node, ast.BinOp):
            left_val = self._eval_node(node.left)
            right_val = self._eval_node(node.right)
            op_func = self.ALLOWED_OPERATORS[type(node.op)]
            return op_func(left_val, right_val)
        elif isinstance(node, ast.UnaryOp):
            val = self._eval_node(node.operand)
            op_func = self.ALLOWED_OPERATORS[type(node.op)]
            return op_func(val)
        else:
            raise ValueError(f"Cannot evaluate node type {type(node).__name__}")
