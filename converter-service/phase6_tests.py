import json
from dual_validator_v2 import validate_dual_conversion

PROGRAMS = {
    "if_else": (
        "n = int(input())\n"
        "if n % 2 == 0:\n"
        "    print('even')\n"
        "else:\n"
        "    print('odd')\n",
        ["2\n", "7\n", "0\n", "-3\n"]
    ),
    "for_loop": (
        "n = int(input())\n"
        "for i in range(n):\n"
        "    print(i)\n",
        ["0\n", "1\n", "4\n"]
    ),
    "while_loop": (
        "n = int(input())\n"
        "while n > 0:\n"
        "    print(n)\n"
        "    n = n - 1\n",
        ["0\n", "1\n", "3\n"]
    ),
    "function": (
        "def square(x: int) -> int:\n"
        "    return x * x\n"
        "n = int(input())\n"
        "print(square(n))\n",
        ["0\n", "3\n", "-4\n"]
    ),
    "list_sum": (
        "a = list(map(int, input().split()))\n"
        "print(sum(a))\n",
        ["1 2 3\n", "\n", "-5 2 3\n", "2147483648\n"]
    )
}

results = {}

for name, (program, cases) in PROGRAMS.items():
    print(f"\nTesting: {name}", flush=True)
    try:
        result = validate_dual_conversion(
            program,
            manual_cases=cases
        )
        ast = result.get("ast_report") or {}
        ollama = result.get("ollama_report") or {}

        results[name] = {
            "status": result.get("status"),
            "method": result.get("method"),
            "ast": {
                "status": ast.get("status"),
                "passed": ast.get("passed"),
                "total": ast.get("total")
            },
            "ollama": {
                "status": ollama.get("status"),
                "passed": ollama.get("passed"),
                "total": ollama.get("total")
            },
            "errors": result.get("errors"),
            "repair_history": result.get("repair_history")
        }
    except Exception as exc:
        results[name] = {
            "status": "ERROR",
            "error": str(exc)
        }

print("\n=== PHASE 6 SUMMARY ===")
print(json.dumps(results, indent=2))

