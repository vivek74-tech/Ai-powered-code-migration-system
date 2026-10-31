import json
from dual_validator_v2 import validate_dual_conversion

PROGRAMS = {
    "negative_floor_division": (
        "a = int(input())\nb = int(input())\nprint(a // b)\n",
        ["10\n3\n", "-10\n3\n", "10\n-3\n", "-10\n-3\n"]
    ),
    "modulo_negative": (
        "a = int(input())\nb = int(input())\nprint(a % b)\n",
        ["10\n3\n", "-10\n3\n", "10\n-3\n", "-10\n-3\n"]
    ),
    "large_integer": (
        "n = int(input())\nprint(n + 1)\n",
        ["0\n", "-1\n", "2147483647\n", "1000000000000\n"]
    ),
    "nested_conditions": (
        "n = int(input())\nif n > 0:\n    if n % 2 == 0:\n        print('positive even')\n    else:\n        print('positive odd')\nelse:\n    print('non-positive')\n",
        ["0\n", "-2\n", "3\n", "4\n"]
    ),
    "string_whitespace": (
        "s = input()\nprint(s.upper())\nprint(len(s))\n",
        ["\n", "hello world\n", "  hi  \n", "a b c\n"]
    ),
}

def main():
    results = {}
    for name, (code, cases) in PROGRAMS.items():
        print(f"\nTesting: {name}", flush=True)
        try:
            result = validate_dual_conversion(code, manual_cases=cases)
            results[name] = result
            print("Status:", result.get("status"))
            print("Method:", result.get("method"))
        except Exception as exc:
            results[name] = {"status": "ERROR", "error": str(exc)}
            print("ERROR:", exc)

    with open("phase8_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n=== PHASE 8 SUMMARY ===")
    for name, result in results.items():
        print(name, ":", result.get("status"))

    print("\nResults saved to phase8_results.json")

if __name__ == "__main__":
    main()

