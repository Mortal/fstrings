import re
import ast
import sys
import contextlib


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.output_line = 1
        self.output_col = 0

    def print(self, s, l, c):
        if self.output_line < l:
            self.write('\n' * (l - self.output_line))
        if self.output_col < c:
            self.write(' ' * (c - self.output_col))
        self.write(s)

    def write(self, s):
        sys.stdout.write(s)
        lines = s.split('\n')
        if len(lines) <= 1:
            self.output_col += len(s)
        else:
            self.output_line += len(lines) - 1
            self.output_col = len(lines[-1])

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
        self.print(str(node), node.lineno, node.col_offset)

    def visit_Module(self, node):
        for child in node.body:
            self.visit(child)

    def visit_FunctionDef(self, node):
        self.print('def ', node.lineno, node.col_offset)
        self.write(node.name)
        self.write('(')
        self.visit_arguments(node.args)
        self.write('):')
        for child in node.body:
            self.visit(child)

    def visit_arguments(self, args):
        for i, a in enumerate(args.args):
            if i:
                self.write(',')
            self.print(a.arg, a.lineno, a.col_offset)

    def visit_Expr(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        self.visit(node.func)
        self.write('(')
        for i, arg in enumerate(node.args):
            if i:
                self.write(',')
            self.visit(arg)

        for j, (k, v) in enumerate(node.keywords):
            if j or node.args:
                self.write(',')
            if k is None:
                self.write('**')
            else:
                self.write(k + '=')
            self.visit(v)

        self.write(')')

    def visit_BinOp(self, node):
        if self.make_fstring(node):
            return
        ops = {
            ast.Mod: '%',
        }
        self.visit(node.left)
        self.write(' %s ' % (ops.get(type(node.op), '?'),))
        self.visit(node.right)

    @staticmethod
    def escape_string_part(s):
        return repr('"' + s)[2:-1]

    @contextlib.contextmanager
    def capture_write(self, f):
        l, c = self.output_line, self.output_col
        old_write, self.write = self.write, f
        try:
            yield
        finally:
            self.write = old_write
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
            self.write('f\'')
            for part in res:
                if isinstance(part, str):
                    self.write(self.escape_string_part(part))
                else:
                    a, t = part
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

    def visit_Name(self, node):
        self.print(node.id, node.lineno, node.col_offset)

    def visit_Num(self, node):
        self.print(repr(node.n), node.lineno, node.col_offset)

    def visit_Str(self, node):
        self.print(repr(node.s), node.lineno, node.col_offset)

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


def main():
    s = sys.stdin.read()
    o = ast.parse(s)
    v = Visitor()
    v._source_lines = s.splitlines()
    v.visit(o)
    if v.output_col > 0:
        v.write('\n')


if __name__ == "__main__":
    main()
