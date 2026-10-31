"""Phase 3 conservative AST-based input generator.

Recognizes simple top-level n=int(input()) followed immediately by an integer
array from input().split(). No claim of general dependency inference.
"""
import ast
from dataclasses import dataclass

@dataclass
class TestCase:
    name: str
    stdin: str

@dataclass
class TestPlan:
    cases: list[TestCase]
    supported: bool
    reason: str


def _is_input(node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'input' and not node.args and not node.keywords


def _kind(node):
    if _is_input(node):
        return 'str'
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1:
        if node.func.id in ('int', 'float', 'str') and _is_input(node.args[0]):
            return node.func.id
        if node.func.id in ('list', 'tuple'):
            return _kind(node.args[0])
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'split' and _is_input(node.func.value):
        return 'tokens'
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'map' and len(node.args) == 2:
        fn, arg = node.args
        if isinstance(fn, ast.Name) and fn.id in ('int', 'float') and _kind(arg) == 'tokens':
            return fn.id + '_tokens'
    return None


def _assignment_name(stmt):
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id
    return None


def generate_tests(source: str) -> TestPlan:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return TestPlan([], False, f'Invalid Python syntax: {exc.msg}')

    items = []
    for stmt in tree.body:
        calls = [node for node in ast.walk(stmt) if _is_input(node)]
        if not calls:
            continue
        if not isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.Expr)) or len(calls) != 1:
            return TestPlan([], False, 'Dynamic or multiple input() calls; supply manual cases')
        kind = _kind(stmt.value)
        if kind is None:
            return TestPlan([], False, 'Unsupported input expression; supply manual cases')
        items.append((kind, _assignment_name(stmt), stmt))

    if not items:
        return TestPlan([TestCase('no-input', '')], True, 'No input() calls detected')
    if len(items) > 8:
        return TestPlan([], False, 'Too many input statements')

    # Special case: a size variable immediately followed by a single integer
    # list. Restrict to common names; never assume every integer controls length.
    if (len(items) == 2 and items[0][0] == 'int'
            and items[0][1] in ('n', 'N', 'size', 'length', 'count')
            and items[1][0] == 'int_tokens'):
        count_name = items[0][1]
        # Avoid generating empty-array tests for algorithms that require n > 0.
        presets = [
            ('singleton', [2]),
            ('small-positive', [2, 5, 1]),
            ('all-zero', [0, 0, 0]),
            ('mixed-sign', [-3, 0, 7, -1]),
            ('repeated', [4, 4, 4, 4, 4]),
            ('larger', list(range(1, 11))),
        ]
        cases = [TestCase(name, f'{len(arr)}\n' + ' '.join(map(str, arr)) + '\n')
                 for name, arr in presets]
        return TestPlan(cases, True,
                        f'Heuristic: assumed {count_name} is the length of the next integer array; constraints not guaranteed')

    presets = [
        ('small-positive', {'int':'2','float':'2.5','str':'hello','tokens':'2 3','int_tokens':'2 3','float_tokens':'2.5 3.5'}),
        ('other-positive', {'int':'5','float':'5.25','str':'world','tokens':'5 7','int_tokens':'5 7','float_tokens':'5.25 7.75'}),
        ('zero', {'int':'0','float':'0.0','str':'zero','tokens':'0 0','int_tokens':'0 0','float_tokens':'0.0 0.0'}),
        ('negative', {'int':'-3','float':'-3.5','str':'sample','tokens':'-3 -1','int_tokens':'-3 -1','float_tokens':'-3.5 -1.5'}),
    ]
    cases = [TestCase(name, '\n'.join(values[kind] for kind, _, _ in items) + '\n')
             for name, values in presets]
    return TestPlan(cases, True, 'Independent heuristic inputs; constraints not guaranteed')
