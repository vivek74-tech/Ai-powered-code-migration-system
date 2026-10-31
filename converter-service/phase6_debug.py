from dual_validator_v2 import validate_dual_conversion

programs = {
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
    )
}

for name, (code, cases) in programs.items():
    print("\nPROGRAM:", name, flush=True)

    result = validate_dual_conversion(
        code,
        manual_cases=cases
    )

    for method in ("ast_report", "ollama_report"):
        report = result.get(method) or {}

        for test in report.get("tests", []):
            if test.get("status") != "PASS":
                print(method, test)
