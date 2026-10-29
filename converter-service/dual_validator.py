import requests
from private_network import private_post

from converter import PythonToCppConverter
from ollama_converter import convert_with_ollama, repair_cpp_with_ollama

import os

WORKER_URL = os.getenv(
    "WORKER_URL",
    "http://127.0.0.1:8002/execute"
)

def fix_cpp_headers(code):
    import re

    if "#include <bits/stdc++.h>" not in code:
        code = "#include <bits/stdc++.h>\\n" + code

    if "using namespace std;" not in code:
        lines = code.splitlines()
        index = 0

        for i, line in enumerate(lines):
            if line.strip().startswith("#include"):
                index = i + 1

        lines.insert(index, "using namespace std;")
        code = "\\n".join(lines)

    code = re.sub(
        r"\\bstd::(?=[A-Za-z_])",
        "",
        code
    )

    return code


def execute(language, code, stdin=''):
    response = private_post(
        WORKER_URL,
        payload={"language": language, "code": code, "stdin": stdin},
        headers={"X-Worker-Key": os.getenv("WORKER_API_KEY", "")},
        timeout=35
    )
    response.raise_for_status()
    return response.json()


def validate_dual_conversion(python_code, stdin=''):
    result = {
        "validated": False,
        "ast_cpp": None,
        "ollama_cpp": None,
        "python_output": None,
        "ast_output": None,
        "ollama_output": None,
        "method": None,
        "error": None,
        "failed_converter": None
    }

    try:
        py = execute("python", python_code, stdin)
        if not py.get("success"):
            raise RuntimeError(py.get("error") or "Python execution failed")
        result["python_output"] = py.get("output", "").strip()
    except Exception as e:
        result.update(error=str(e), failed_converter="python")
        return result

    try:
        ast_code = PythonToCppConverter().convert(
            python_code, use_ai_fallback=False
        )
        result["ast_cpp"] = fix_cpp_headers(ast_code)

        ast_run = execute("cpp", result["ast_cpp"], stdin)
        if ast_run.get("success"):
            result["ast_output"] = ast_run.get("output", "").strip()
    except Exception:
        pass

    try:
        ai_code = fix_cpp_headers(convert_with_ollama(python_code))
        result["ollama_cpp"] = ai_code

        for attempt in range(3):
            ai_run = execute("cpp", ai_code, stdin)

            if ai_run.get("success"):
                result["ollama_output"] = ai_run.get("output", "").strip()
                break

            error = ai_run.get("error") or "C++ execution failed"

            if ai_run.get("stage") != "compilation" or attempt == 2:
                raise RuntimeError(error)

            ai_code = fix_cpp_headers(
                repair_cpp_with_ollama(python_code, ai_code, error)
            )
            result["ollama_cpp"] = ai_code

    except Exception as e:
        result["error"] = str(e)
        result["failed_converter"] = "ollama"

    expected = result["python_output"]

    ast_ok = (
        result["ast_output"] is not None
        and result["ast_output"] == expected
    )
    ai_ok = (
        result["ollama_output"] is not None
        and result["ollama_output"] == expected
    )

    if ast_ok and ai_ok:
        result.update(validated=True, method="dual-validated", error=None)
    elif ai_ok:
        result.update(validated=True, method="ollama-fallback", error=None)
    elif ast_ok:
        result.update(validated=True, method="ast-based", error=None)
    else:
        result["error"] = result["error"] or "No converter produced matching output"

    return result
