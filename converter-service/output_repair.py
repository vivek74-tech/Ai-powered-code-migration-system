
import re

def repair_missing_newline(cpp_code, report):
    """Fix a simple missing trailing newline only when tests prove it."""

    tests = report.get("tests", [])
    if not tests:
        return cpp_code, False

    failures = [t for t in tests if t.get("status") == "FAIL"]

    if not failures:
        return cpp_code, False

    for test in failures:
        if test.get("reason") != "stdout mismatch":
            return cpp_code, False

        expected = test.get("python_output")
        actual = test.get("cpp_output")

        if not isinstance(expected, str) or not isinstance(actual, str):
            return cpp_code, False

        if expected != actual + "\n":
            return cpp_code, False

    pattern = r"(std::cout|cout)\s*<<\s*([^;\n]+);"
    matches = list(re.finditer(pattern, cpp_code))

    # Avoid modifying programs with multiple output statements.
    if len(matches) != 1:
        return cpp_code, False

    match = matches[0]

    if re.search(r"\bendl\b|['\"]\\n['\"]", match.group(0)):
        return cpp_code, False

    repaired = (
        cpp_code[:match.start()]
        + match.group(1)
        + " << "
        + match.group(2).strip()
        + " << '\\n';"
        + cpp_code[match.end():]
    )

    return repaired, repaired != cpp_code
