import json
from dual_validator_v2 import validate_dual_conversion

PROGRAM = """
n = int(input())
a = list(map(int, input().split()))
print(sum(a))
"""

CASES = [
    "1\n2\n",
    "3\n2 5 1\n",
    "0\n\n",
    "3\n1 2\n",
    "2\n1 2 3\n",
    "4\n-3 0 7 -1\n",
    "1\n2147483648\n",
]

result = validate_dual_conversion(
    PROGRAM,
    manual_cases=CASES
)

summary = {
    "status": result["status"],
    "method": result["method"],
    "ast_report": {
        "status": (result.get("ast_report") or {}).get("status"),
        "passed": (result.get("ast_report") or {}).get("passed"),
        "total": (result.get("ast_report") or {}).get("total"),
        "tests": (result.get("ast_report") or {}).get("tests"),
    },
    "ollama_report": {
        "status": (result.get("ollama_report") or {}).get("status"),
        "passed": (result.get("ollama_report") or {}).get("passed"),
        "total": (result.get("ollama_report") or {}).get("total"),
        "tests": (result.get("ollama_report") or {}).get("tests"),
    },
    "repair_history": result.get("repair_history"),
    "errors": result.get("errors"),
}

print(json.dumps(summary, indent=2))
