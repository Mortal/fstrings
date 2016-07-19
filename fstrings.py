"""
>>> s = '''\\
... def say(greeting='hello', target='world'):
...     print("%s%s, %s!" % (greeting[0].upper(), greeting[1:], target))
... '''
>>> o = ast.parse(s)
>>> v = Visitor()
>>> v.visit(o)
def say(greeting='hello', target='world'):
    print(f'{greeting[0].upper()}{greeting[1:]}, {target}!')
"""

import re
import ast
import sys
import contextlib


PRECEDENCE = [
    [ast.Lambda],
    [ast.IfExp],
    [ast.Or],
    [ast.And],
    [ast.Not],
    [ast.In, ast.NotIn, ast.Is, ast.IsNot, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
     ast.NotEq, ast.Eq],
    [ast.BitOr],
    [ast.BitXor],
    [ast.BitAnd],
    [ast.LShift, ast.RShift],
    [ast.Add, ast.Sub],
    [ast.Mult, ast.MatMult, ast.Div, ast.FloorDiv, ast.Mod],
    [ast.UAdd, ast.USub, ast.Invert],
    [ast.Pow],
    [ast.Await],
    [ast.Subscript, ast.Call, ast.Attribute],
    [ast.Tuple, ast.List, ast.Dict, ast.Set],
]


def precedence(op):
    for i in range(len(PRECEDENCE)):
        if op in PRECEDENCE[i]:
            return i


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.output_line = 1
        self.output_col = 0
        self.first_line = 0
        self.last_line = float('inf')
        self.p_level = 0
        self.precedence = [-1]

    def print(self, s, l, c):
        if self.output_line < l:
            self.write('\n' * (l - self.output_line))
        if self.output_col < c:
            self.write(' ' * (c - self.output_col))
        self.write(s)

    def write(self, s):
        lines = s.splitlines(True)
        for line in lines:
            if self.first_line <= self.output_line <= self.last_line:
                sys.stdout.write(line)
            if line.endswith('\n'):
                self.output_line += 1
                self.output_col = 0
            else:
                self.output_col += len(line)

    def visit(self, node):
        try:
            return super(Visitor, self).visit(node)
        except Exception:
            self.source_backtrace(node, sys.stderr)
            raise

    def source_backtrace(self, node, file):
        try:
            lineno = node.lineno
            col_offset = node.col_offset
        except AttributeError:
            lineno = col_offset = None
        print('At node %s' % node, file=file)
        if lineno is not None and lineno > 0:
            print(self._source_lines[lineno - 1], file=file)
            print(' ' * col_offset + '^', file=file)

    def generic_visit(self, node):
        self.print(str(node), getattr(node, 'lineno', 0), getattr(node, 'col_offset', 0))

    def visit_Module(self, node):
        for child in node.body:
            self.visit(child)

    def visit_Import(self, node):
        self.print('import ', node.lineno, node.col_offset)
        for i, n in enumerate(node.names):
            if i:
                self.write(', ')
            self.write(n.name)
            if n.asname:
                self.write(' as ')
                self.write(n.asname)

    def visit_FunctionDef(self, node):
        self.print('def ', node.lineno, node.col_offset)
        self.write(node.name)
        self.write('(')
        self.visit_arguments(node.args)
        self.write('):')
        for child in node.body:
            self.visit(child)

    def visit_ClassDef(self, node):
        self.print('class ', node.lineno, node.col_offset)
        self.write(node.name)
        self.write('(')
        self.visit_commasep(node.bases)
        self.write('):')
        for child in node.body:
            self.visit(child)

    def visit_While(self, node):
        self.print('while ', node.lineno, node.col_offset)
        self.visit(node.test)
        self.write(':')
        for child in node.body:
            self.visit(child)

    def visit_With(self, node):
        self.print('with ', node.lineno, node.col_offset)
        for v in node.items:
            self.visit(v.context_expr)
            if v.optional_vars:
                self.write(' as ')
                self.visit(v.optional_vars)
        self.write(':')
        for child in node.body:
            self.visit(child)

    def visit_If(self, node, keyword='if', col=None):
        if col is None:
            col = node.col_offset
        self.print(keyword + ' ', node.lineno, col)
        self.visit(node.test)
        self.write(':')
        for child in node.body:
            self.visit(child)
        if len(node.orelse) > 0:
            if (len(node.orelse) == 1 and
                    isinstance(node.orelse[0], ast.If)):
                self.visit_If(node.orelse[0], 'elif', col)
            else:
                self.print('else:', self.output_line + 1, col)
                for tail in node.orelse:
                    self.visit(tail)

    def visit_Try(self, node):
        self.print('try:', node.lineno, node.col_offset)
        for child in node.body:
            self.visit(child)
        for excepthandler in node.handlers:
            self.print('except',
                       excepthandler.lineno, excepthandler.col_offset)
            if excepthandler.type:
                self.visit(excepthandler.type)
            if excepthandler.name:
                self.write(' as ')
                self.write(excepthandler.name)
            self.write(':')
            for child in excepthandler.body:
                self.visit(child)
        if node.orelse:
            self.print('else:', self.output_line + 1, node.col_offset)
            for tail in node.orelse:
                self.visit(tail)
        if node.finalbody:
            self.print('finally:', self.output_line + 1, node.col_offset)
            for tail in node.finalbody:
                self.visit(tail)

    def visit_For(self, node):
        self.print('for ', node.lineno, node.col_offset)
        self.visit(node.target)
        self.write(' in ')
        self.visit(node.iter)
        self.write(':')
        for child in node.body:
            self.visit(child)

    def visit_arguments(self, args):
        for i, (a, d) in enumerate(zip(args.args, args.defaults)):
            if i:
                self.write(',')
            self.print(a.arg, a.lineno, a.col_offset)
            if d is not None:
                self.write('=')
                self.visit(d)

    def visit_commasep(self, elts):
        for i, arg in enumerate(elts):
            if i:
                self.write(',')
            self.visit(arg)

    def visit_Pass(self, node):
        self.print('pass', node.lineno, node.col_offset)

    def visit_Expr(self, node):
        self.visit(node.value)

    def visit_Return(self, node):
        self.print('return', node.lineno, node.col_offset)
        if node.value:
            self.visit(node.value)

    def visit_Yield(self, node):
        self.print('yield', node.lineno, node.col_offset)
        if node.value:
            self.visit(node.value)

    def visit_Raise(self, node):
        self.print('raise', node.lineno, node.col_offset)
        if node.exc:
            self.visit(node.exc)
        if node.cause:
            self.write(' from')
            self.visit(node.cause)

    def visit_Assign(self, node):
        for t in node.targets:
            if isinstance(t, ast.Tuple):
                t.col_offset = node.col_offset + 1  # for Tuple
            self.visit(t)
            self.write(' = ')
        self.visit(node.value)

    def visit_AugAssign(self, node):
        ops = {
            ast.Mod: '%',
            ast.Sub: '-',
            ast.Add: '+',
            ast.Mult: '*',
        }
        if isinstance(node.target, ast.Tuple):
            node.target.col_offset = node.col_offset + 1  # for Tuple
        self.visit(node.target)
        self.write(' ')
        self.write(ops.get(type(node.op), str(node.op)))
        self.write('=')
        self.write(' ')
        self.visit(node.value)

    def visit_Call(self, node):
        self.visit(node.func)
        self.write('(')
        self.visit_commasep(node.args)
        for j, kw in enumerate(node.keywords):
            k = kw.arg
            v = kw.value
            if j or node.args:
                self.write(',')
            if k is None:
                self.write('**')
            else:
                self.write(k + '=')
            self.visit(v)

        self.write(')')

    @contextlib.contextmanager
    def auto_parens(self, node, op, left, right):
        prec = precedence(type(op))
        if (left.lineno != right.lineno and self.p_level == 0 and
                (node.lineno, node.col_offset) >
                (self.output_line, self.output_col)):
            self.write('(')
            self.precedence.append(-1)
            p = True
            self.p_level += 1
        elif self.precedence[-1] > prec:
            self.write('(')
            self.precedence.append(-1)
            p = True
            self.p_level += 1
        else:
            self.precedence.append(prec)
            p = False
        yield
        if p:
            self.write(')')
            self.p_level -= 1
        self.precedence.pop()

    def visit_BinOp(self, node):
        if self.make_fstring(node):
            return
        ops = {
            ast.Mod: '%',
            ast.Sub: '-',
            ast.Add: '+',
            ast.Mult: '*',
        }
        with self.auto_parens(node, node.op, node.left, node.right):
            self.visit(node.left)
            self.write(' %s ' % (ops.get(type(node.op), str(node.op)),))
            self.visit(node.right)

    def visit_UnaryOp(self, node):
        ops = {
            ast.USub: '-',
            ast.UAdd: '+',
        }
        self.print(ops.get(type(node.op), str(node.op)),
                   node.lineno, node.col_offset)
        self.visit(node.operand)

    def visit_Compare(self, node):
        self.visit(node.left)
        ops = {
            ast.Lt: '<',
            ast.Gt: '>',
            ast.LtE: '<=',
            ast.GtE: '>=',
            ast.Eq: '==',
            ast.NotEq: '!=',
            ast.In: ' in ',
            ast.Is: ' is ',
            ast.IsNot: ' is not ',
        }
        for op, right in zip(node.ops, node.comparators):
            self.write(' %s ' % (ops.get(type(op), '?'),))
            self.visit(right)

    def visit_BoolOp(self, node):
        ops = {
            ast.And: ' and ',
            ast.Or: ' or ',
        }
        with self.auto_parens(node, node.op, node.values[0], node.values[-1]):
            for i, v in enumerate(node.values):
                if i:
                    self.write(ops[type(node.op)])
                self.visit(v)

    def visit_Lambda(self, node):
        self.print('lambda', node.lineno, node.col_offset)
        self.visit_arguments(node.args)
        self.write(':')
        self.visit(node.body)

    @staticmethod
    def escape_string_part(s):
        return repr('"' + s)[2:-1]

    @contextlib.contextmanager
    def capture_write(self, f):
        l, c = self.output_line, self.output_col
        old_write, self.write = self.write, f
        old_print, self.print = self.print, (lambda s, l, c: self.write(s))
        try:
            yield
        finally:
            self.write = old_write
            self.print = old_print
            self.output_line, self.output_col = l, c

    def make_fstring(self, node):
        if (isinstance(node, ast.BinOp) and
                isinstance(node.op, ast.Mod) and
                isinstance(node.left, ast.Str)):
            if isinstance(node.right, ast.Tuple):
                arguments = list(node.right.elts)
            else:
                arguments = [node.right]
            pattern = (
                r'%(?P<key>\([^)]*\))?' +
                r'(?P<flag>[#0 +-]*)' +
                r'(?P<width>\*|\d+)?' +
                r'(?:\.(?P<prec>\*|\d+))?' +
                r'(?P<length>[hlL])?' +
                r'(?P<type>.)')
            conversions = re.finditer(pattern, node.left.s)
            res = []
            i = 0
            for mo in conversions:
                j = mo.start(0)
                res.append(node.left.s[i:j])
                i = mo.end(0)
                t = mo.group('type')
                if t == '%':
                    res.append('%')
                elif t in ('s', 'r'):
                    res.append((arguments.pop(0), t))
                else:
                    return
            res.append(node.left.s[i:])
            if arguments:
                return
            self.print('f\'', node.lineno, node.col_offset)
            for part in res:
                if isinstance(part, str):
                    self.write(self.escape_string_part(part))
                else:
                    (a, t) = part
                    self.write('{')
                    a.lineno = self.output_line
                    a.col_offset = self.output_col
                    a_ = []
                    with self.capture_write(a_.append):
                        self.visit(a)
                    self.write(self.escape_string_part(''.join(a_)))
                    if t != 's':
                        self.write('!' + t)
                    self.write('}')
            self.write('\'')
            return True

    def visit_Attribute(self, node):
        self.visit(node.value)
        self.write('.')
        self.write(node.attr)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.write('[')
        self.visit(node.slice)
        self.write(']')

    def visit_Index(self, node):
        self.visit(node.value)

    def visit_IfExp(self, node):
        self.visit(node.body)
        self.write(' if ')
        self.visit(node.test)
        self.write(' else ')
        self.visit(node.orelse)

    def visit_Slice(self, node):
        if node.lower:
            self.visit(node.lower)
        self.write(':')
        if node.upper:
            self.visit(node.upper)
        if node.step:
            self.write(':')
            self.visit(node.step)

    def visit_Name(self, node):
        self.print(node.id, node.lineno, node.col_offset)

    def visit_NameConstant(self, node):
        self.print(repr(node.value), node.lineno, node.col_offset)

    def visit_Num(self, node):
        self.print(repr(node.n), node.lineno, node.col_offset)

    def visit_Str(self, node):
        self.print(repr(node.s), node.lineno, node.col_offset)

    def visit_JoinedStr(self, node):
        self.print(repr(node.values), node.lineno, node.col_offset)

    def visit_Tuple(self, node):
        if len(node.elts) > 0:
            self.print('(', node.lineno, node.col_offset - 1)
            self.visit(node.elts[0])
            for e in node.elts[1:]:
                self.write(',')
                self.visit(e)
            if len(node.elts) == 1:
                self.write(',')
            self.write(')')
        else:
            self.print('()', node.lineno, node.col_offset)

    def visit_List(self, node):
        self.print('[', node.lineno, node.col_offset)
        self.visit_commasep(node.elts)
        self.write(']')

    def visit_Dict(self, node):
        self.print('{', node.lineno, node.col_offset)
        for k, v in zip(node.keys, node.values):
            self.visit(k)
            self.write(': ')
            self.visit(v)
            self.write(',')
        self.write('}')


def main():
    s = sys.stdin.read()
    o = ast.parse(s)
    v = Visitor()
    try:
        a, b = sys.argv[1:]
        a = int(a)
        b = int(b)
    except ValueError:
        pass
    else:
        v.first_line = a
        v.last_line = b
    v._source_lines = s.splitlines()
    v.visit(o)
    if v.output_col > 0:
        v.write('\n')


if __name__ == "__main__":
    main()
