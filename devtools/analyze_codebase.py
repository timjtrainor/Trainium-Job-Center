import os
import ast
import json
import re
import sys
from collections import defaultdict

IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', 'DB Scripts', 'dist', 'build', 'venv', 'env', '.idea', '.vscode'}
IGNORE_FILES = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'}

def is_ignored(path):
    parts = path.split(os.sep)
    for part in parts:
        if part in IGNORE_DIRS:
            return True
    return False

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions = []

    def visit_FunctionDef(self, node):
        self._check_complexity(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_complexity(node)
        self.generic_visit(node)

    def _check_complexity(self, node):
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        self.functions.append({
            'name': node.name,
            'lineno': node.lineno,
            'complexity': complexity,
            'end_lineno': getattr(node, 'end_lineno', node.lineno)
        })

def analyze_python_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        visitor = ComplexityVisitor()
        visitor.visit(tree)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return {
            'functions': visitor.functions,
            'imports': imports,
            'loc': len(content.splitlines())
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_ts_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        content = ''.join(lines)
        loc = len(lines)

        # Heuristic for imports
        imports = []
        import_pattern = re.compile(r'import\s+.*?from\s+[\'"](.*?)[\'"]', re.DOTALL)
        for match in import_pattern.finditer(content):
            imports.append(match.group(1))

        # Heuristic for "long functions" / complexity (indentation)
        max_indent = 0
        functions = [] # Placeholder, hard to parse names without proper parser

        # Simple check for very long files as a proxy
        if loc > 300:
             functions.append({'name': 'FILE_LEVEL_CHECK', 'complexity': loc // 20, 'lineno': 1, 'info': 'Approximated by LOC'})

        return {
            'functions': functions,
            'imports': imports,
            'loc': loc
        }
    except Exception as e:
        return {'error': str(e)}

def get_all_files(root_dir):
    file_list = []
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip ignored
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in IGNORE_FILES:
                continue
            filepath = os.path.join(root, file)
            if not is_ignored(filepath):
                file_list.append(filepath)
    return file_list

def analyze_codebase():
    root_dir = '.'
    all_files = get_all_files(root_dir)

    results = {
        'directory_stats': defaultdict(int),
        'files': {},
        'dependency_graph': defaultdict(list)
    }

    for filepath in all_files:
        dirname = os.path.dirname(filepath)
        results['directory_stats'][dirname] += 1

        if filepath.endswith('.py'):
            analysis = analyze_python_file(filepath)
            results['files'][filepath] = analysis
            if 'imports' in analysis:
                results['dependency_graph'][filepath] = analysis['imports']

        elif filepath.endswith(('.ts', '.tsx', '.js', '.jsx')):
            analysis = analyze_ts_file(filepath)
            results['files'][filepath] = analysis
            if 'imports' in analysis:
                 results['dependency_graph'][filepath] = analysis['imports']

    # Detect cycles (simplistic, node-based)
    # We need to resolve imports to filepaths to do this properly, which is hard without a full resolver.
    # We will just report the raw dependency graph and do a "module level" analysis if possible,
    # or just list the raw strings.

    return results

if __name__ == "__main__":
    data = analyze_codebase()
    print(json.dumps(data, indent=2))
