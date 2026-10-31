import json
from dual_validator_v2 import validate_dual_conversion

PROGRAMS = {
    "nested_loops": (
        "n = int(input())\n"
        "for i in range(n):\n"
        "    for j in range(i + 1):\n"
        "        print(i + j)\n",
        ["0\n", "1\n", "3\n"]
    ),

    "recursion": (
        "def factorial(n: int) -> int:\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "    return n * factorial(n - 1)\n"
        "n = int(input())\n"
        "print(factorial(n))\n",
        ["0\n", "1\n", "5\n", "10\n"]
    ),

    "dictionary": (
        "scores = {'alice': 10, 'bob': 20}\n"
        "name = input()\n"
        "print(scores.get(name, 0))\n",
        ["alice\n", "bob\n", "unknown\n"]
    ),

    "string_operations": (
        "s = input()\n"
        "print(s.upper())\n"
        "print(len(s))\n",
        ["hello\n", "Python\n", "\n", "a b\n"]
    ),

    "exception_handling": (
        "try:\n"
        "    n = int(input())\n"
        "    print(10 // n)\n"
        "except ZeroDivisionError:\n"
        "    print('division by zero')\n",
        ["2\n", "0\n", "-3\n"]
    )
}


summary = {}

for name, (code, cases) in PROGRAMS.items():
    print("\nTesting:", name, flush=True)

    try:
        result = validate_dual_conversion(
            code,
            manual_cases=cases
        )

        summary[name] = {
            "status": result.get("status"),
            "method": result.get("method"),
            "ast": {
                "status": (result.get("ast_report") or {}).get("status"),
                "passed": (result.get("ast_report") or {}).get("passed"),
                "total": (result.get("ast_report") or {}).get("total")
            },
            "ollama": {
                "status": (result.get("ollama_report") or {}).get("status"),
                "passed": (result.get("ollama_report") or {}).get("passed"),
                "total": (result.get("ollama_report") or {}).get("total")
            },
            "errors": result.get("errors", {}),
            "repair_history": result.get("repair_history", [])
        }

    except Exception as e:
        summary[name] = {
            "status": "ERROR",
            "error": str(e)
        }

print("\n=== PHASE 7 SUMMARY ===")
print(json.dumps(summary, indent=2))

with open("phase7_results.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("\nResults saved to phase7_results.json")
