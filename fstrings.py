import ast
import sys


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
        self.write(':')
        for child in node.body:
            self.visit(child)

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
        ops = {
            ast.Mod: '%',
        }
        self.visit(node.left)
        self.write(' %s ' % (ops.get(type(node.op), '?'),))
        self.visit(node.right)

    def visit_Str(self, node):
        self.print(repr(node.s), node.lineno, node.col_offset)


def main():
    s = sys.stdin.read()
    o = ast.parse(s)
    v = Visitor()
    v.visit(o)
    if v.output_col > 0:
        v.write('\n')


if __name__ == "__main__":
    main()
