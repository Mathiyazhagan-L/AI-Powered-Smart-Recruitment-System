import sys
import os
import json
import re
import tempfile
import subprocess
from typing import Dict, Any, List

# Target folder for sandbox files
TEMP_DIR = r"c:\Recruitment\backend\uploads"

class Evaluator:
    @classmethod
    def run_code(cls, source_code: str, test_cases: List[Dict[str, str]], category: str = "", timeout: float = 2.0) -> Dict[str, Any]:
        """Runs the candidate code against the specified test cases in a subprocess sandbox."""
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR, exist_ok=True)

        # Sandbox script template
        sandbox_template = """
import sys
import json
import inspect
import ast
import io

# ── SECURITY: Block dangerous modules ──────────────────────────────────────
import builtins as _builtins_module

_BLOCKED_MODULES = frozenset([
    "os", "subprocess", "socket", "shutil", "requests",
    "pathlib", "glob", "urllib", "http", "ftplib", "smtplib",
    "paramiko", "fabric", "pexpect", "pty", "signal",
    "multiprocessing", "threading", "ctypes", "cffi",
    "importlib", "pkgutil", "zipimport", "zipfile", "tarfile",
])

_original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else _builtins_module.__import__

def _safe_import(name, *args, **kwargs):
    top = name.split(".")[0]
    if top in _BLOCKED_MODULES:
        raise ImportError(f"Module '{{name}}' is not allowed in the assessment sandbox.")
    return _original_import(name, *args, **kwargs)

# Override __import__ globally
if isinstance(__builtins__, dict):
    __builtins__['__import__'] = _safe_import
else:
    __builtins__.__import__ = _safe_import

# Block file system access via open()
_original_open = open
def _safe_open(file, mode="r", *args, **kwargs):
    if "w" in mode or "a" in mode or "x" in mode:
        raise PermissionError("File write operations are not allowed in the assessment sandbox.")
    file_str = str(file)
    blocked_prefixes = ["c:\\\\windows", "c:\\\\users", "/etc", "/var", "/sys", "/proc", "/home", "/root"]
    for prefix in blocked_prefixes:
        if file_str.lower().startswith(prefix):
            raise PermissionError(f"File read from '{{file_str}}' is not allowed in the assessment sandbox.")
    return _original_open(file, mode, *args, **kwargs)

if isinstance(__builtins__, dict):
    __builtins__['open'] = _safe_open
else:
    __builtins__.open = _safe_open
# ────────────────────────────────────────────────────────────────────────────

# Define standard JSON-like variables
null = None
true = True
false = False

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

# Helper to build TreeNode from list (LeetCode BFS style)
def deserialize_tree(lst):
    if not lst or not isinstance(lst, list):
        return lst
    root = TreeNode(lst[0]) if lst[0] is not None else None
    if not root:
        return None
    queue = [root]
    i = 1
    while queue and i < len(lst):
        curr = queue.pop(0)
        if curr:
            if i < len(lst):
                if lst[i] is not None:
                    curr.left = TreeNode(lst[i])
                    queue.append(curr.left)
                i += 1
            if i < len(lst):
                if lst[i] is not None:
                    curr.right = TreeNode(lst[i])
                    queue.append(curr.right)
                i += 1
    return root

# Helper to serialize TreeNode back to list (BFS style)
def serialize_tree(root):
    if not root:
        return []
    result = []
    queue = [root]
    while queue:
        curr = queue.pop(0)
        if curr:
            result.append(curr.val)
            queue.append(curr.left)
            queue.append(curr.right)
        else:
            result.append(None)
    # Strip trailing None values
    while result and result[-1] is None:
        result.pop()
    return result

# Helper to build ListNode list from Python list
def deserialize_list(lst):
    if not lst or not isinstance(lst, list):
        return lst
    dummy = ListNode(0)
    curr = dummy
    for val in lst:
        curr.next = ListNode(val)
        curr = curr.next
    return dummy.next

# Helper to serialize ListNode back to Python list
def serialize_list(head):
    result = []
    curr = head
    while curr:
        result.append(curr.val)
        curr = curr.next
    return result

category = "{category}"
category_lower = category.lower()

def convert_arg(val, name):
    if isinstance(val, list):
        # Tree conversion
        if "tree" in category_lower:
            if name in ("root", "p", "q", "node"):
                return deserialize_tree(val)
        # Linked list conversion
        if "list" in category_lower:
            if name in ("head", "l1", "l2", "list1", "list2"):
                return deserialize_list(val)
            if name == "lists":
                return [deserialize_list(item) for item in val]
    return val

def serialize_actual(val):
    if isinstance(val, TreeNode):
        return serialize_tree(val)
    if isinstance(val, ListNode):
        return serialize_list(val)
    return val

# Candidate Code
{candidate_code}

# Test Cases
test_cases_data = {test_cases_json}

def parse_lhs(lhs_str):
    expr = f"func({{lhs_str}})"
    tree = ast.parse(expr)
    call_node = tree.body[0].value
    
    ctx = {{
        'null': None,
        'true': True,
        'false': False,
        'True': True,
        'False': False,
        'TreeNode': TreeNode,
        'ListNode': ListNode
    }}
    
    args = []
    for arg in call_node.args:
        val = eval(compile(ast.Expression(arg), '<string>', 'eval'), {{}}, ctx)
        args.append(val)
        
    kwargs = {{}}
    for kw in call_node.keywords:
        val = eval(compile(ast.Expression(kw.value), '<string>', 'eval'), {{}}, ctx)
        kwargs[kw.arg] = val
        
    return args, kwargs

def run_tests():
    local_scope = globals()
    func = None
    if 'solve' in local_scope and callable(local_scope['solve']):
        func = local_scope['solve']
    else:
        # Find first custom callable function
        for name, val in list(local_scope.items()):
            if callable(val) and not name.startswith('_') and val.__class__.__name__ == 'function':
                func = val
                break
                
    if not func:
        print(json.dumps({{"status": "ERROR", "error": "No callable function found. Please define a function (e.g. solve)."}}))
        return

    results = []
    
    # Capture candidate prints
    original_stdout = sys.stdout
    captured_stdout = io.StringIO()
    sys.stdout = captured_stdout
    
    ctx = {{
        'null': None,
        'true': True,
        'false': False,
        'True': True,
        'False': False,
        'TreeNode': TreeNode,
        'ListNode': ListNode
    }}

    for i, tc in enumerate(test_cases_data):
        lhs_str = tc['lhs']
        rhs_str = tc['rhs']
        
        try:
            args, kwargs = parse_lhs(lhs_str)
            expected = eval(rhs_str, {{}}, ctx)
            
            # Inspect signature to handle tuple unpacking if required
            sig = inspect.signature(func)
            params = [p for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
            param_names = list(sig.parameters.keys())
            
            if len(args) == 1 and isinstance(args[0], tuple) and len(params) > 1:
                run_args = list(args[0])
            else:
                run_args = args
                
            # Convert args/kwargs based on parameter names
            run_args_converted = []
            for idx, val in enumerate(run_args):
                p_name = param_names[idx] if idx < len(param_names) else ""
                run_args_converted.append(convert_arg(val, p_name))
            
            run_kwargs_converted = {{}}
            for k, v in kwargs.items():
                run_kwargs_converted[k] = convert_arg(v, k)
                
            # Call candidate function
            actual = func(*run_args_converted, **run_kwargs_converted)
            actual_serialized = serialize_actual(actual)
            
            passed = (actual_serialized == expected)
            
            results.append({{
                "test_case_index": i,
                "input": lhs_str,
                "expected": str(expected),
                "actual": str(actual_serialized),
                "passed": passed
            }})
        except Exception as e:
            results.append({{
                "test_case_index": i,
                "input": lhs_str,
                "expected": rhs_str,
                "passed": False,
                "error": str(e)
            }})
            
    # Restore stdout
    sys.stdout = original_stdout
    
    print(json.dumps({{
        "status": "SUCCESS",
        "results": results,
        "stdout": captured_stdout.getvalue()
    }}))

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(json.dumps({{"status": "ERROR", "error": f"Execution Error: {{e}}"}}))
"""

        # Populate the script with candidate code and test cases
        script_content = sandbox_template.format(
            candidate_code=source_code,
            test_cases_json=json.dumps(test_cases),
            category=category
        )

        # Write to a temporary file inside uploads
        fd, temp_file_path = tempfile.mkstemp(suffix=".py", dir=TEMP_DIR)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # Execute the script in a subprocess using the current Python interpreter
            # Use sys.executable to ensure we run under the same venv
            res = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse results
            if res.returncode != 0:
                # Syntax error or crash before reaching our print statements
                stderr_output = res.stderr or res.stdout
                error_msg = cls._clean_error_message(stderr_output)
                return {
                    "status": "COMPILE_ERROR",
                    "error": error_msg,
                    "results": [],
                    "stdout": ""
                }

            # Attempt to parse json from stdout
            try:
                output_data = json.loads(res.stdout.strip())
                return output_data
            except json.JSONDecodeError:
                return {
                    "status": "ERROR",
                    "error": f"Execution output could not be parsed: {res.stdout[:500]}",
                    "results": [],
                    "stdout": res.stdout
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "error": f"Time Limit Exceeded ({timeout}s). Check for infinite loops in your code.",
                "results": [],
                "stdout": ""
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": f"Sandbox failed: {str(e)}",
                "results": [],
                "stdout": ""
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass

    @classmethod
    def _clean_error_message(cls, raw_error: str) -> str:
        """Cleans Python tracebacks to show only the relevant lines of the syntax/runtime error."""
        lines = raw_error.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove paths referring to temp file to hide sandbox implementation details
            if "temp" in line or "uploads" in line:
                line = re.sub(r'File ".*?", line', 'File "solution.py", line', line)
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)
