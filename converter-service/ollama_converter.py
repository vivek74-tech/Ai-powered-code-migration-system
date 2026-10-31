
import re
import requests
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:1.5b"
FALLBACK_MODEL = "qwen2.5-coder:7b"


def extract_cpp(text: str) -> str:
    """Extract fenced C++ or trim trailing model commentary."""
    text = text.strip()
    blocks = re.findall(r"```(?:cpp|c\+\+|cxx)?\s*\n(.*?)```", text, flags=re.I | re.S)
    if blocks:
        text = next((x for x in blocks if "#include" in x or "int main" in x), blocks[0]).strip()
    else:
        text = re.sub(r"^```(?:cpp|c\+\+|cxx)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```.*$", "", text, flags=re.S)
        text = re.split(r"\n(?:Explanation:|This code |The code |Here is |Note:)", text, maxsplit=1)[0].strip()
    return text


ARRAY_RULES = 'IMPORTANT PYTHON SEMANTICS:\nFor this pattern:\nn = int(input())\na = list(map(int, input().split()))\nprint(sum(a))\n\nThe first input line is ONLY n.\nRead the second input line separately.\nSum ONLY the numbers from the second line.\nNEVER add n to the sum.\nNEVER limit array length to n.\nAn empty second line means an empty array and sum zero.\nUse long long and stoll for large integers.\nUse valid C++17 syntax.\nDeclare std::string line BEFORE calling std::getline(std::cin, line).'


def semantic_rules(python_code: str) -> str:
    if "ZeroDivisionError" in python_code and "//" in python_code:
        return """
PYTHON EXCEPTION AND FLOOR DIVISION:
Python // means mathematical floor, not C++ truncation.
For signed long long a and nonzero b:
long long q = a / b;
long long r = a % b;
if (r != 0 && ((r > 0) != (b > 0))) --q;
Use q as the result.

Before division, check whether b == 0.
If zero, execute the Python ZeroDivisionError handler.
Never rely on C++ integer division throwing exceptions.
Use cin >> value for int(input()).
Every print() must end with a newline.
"""

    if "%" in python_code:
        return """
PYTHON MODULO SEMANTICS:
Python a % b differs from C++ remainder for negative operands.
For signed long long a and nonzero b:
long long r = a % b;
if (r != 0 && ((r > 0) != (b > 0))) r += b;
Use r as the modulo result.
Never directly print a % b when operands may be negative.

For Python int(input()), use:
long long value;
cin >> value;
Never generate input() or stoll(input()) in C++.
Every Python print() must produce a trailing newline.
Generate valid C++17 code.
"""
    if "ZeroDivisionError" in python_code and "//" in python_code:
        return """
PYTHON EXCEPTION AND FLOOR DIVISION SEMANTICS:
Python a // b uses mathematical floor, NOT C++ integer truncation.
For signed long long operands a and b, with b != 0:
long long q = a / b;
long long r = a % b;
if (r != 0 && ((r > 0) != (b > 0))) --q;
Use q as the result.

Python ZeroDivisionError must be handled by explicitly checking
whether the divisor is zero BEFORE division.
C++ integer division by zero does not throw std::invalid_argument
or std::out_of_range. Never rely on C++ catch blocks for this.
For the supplied Python try/except, execute the except branch
when the divisor is zero.
Every Python print() must end with a newline (std::endl or '\\n').
Generate valid C++17 code.
"""
    if ".upper()" in python_code:
        return """
PYTHON STRING SEMANTICS:
Python input() reads an entire line without its trailing newline.
Use std::getline(std::cin, s), NOT std::cin >> s.
Preserve leading spaces, trailing spaces, and empty input lines.

Python s.upper() MUST convert lowercase letters to uppercase.
For ASCII input, use:
std::string upper = s;
for (char &c : upper) {
    if (c >= 'a' && c <= 'z') {
        c = static_cast<char>(c - 'a' + 'A');
    }
}
std::cout << upper << '\\n';
std::cout << s.size() << '\\n';

IMPORTANT:
Do not print the original lowercase string instead of upper.
Do not trim whitespace.
Do not count the newline as part of the string.
Every Python print() must produce a trailing newline.
Use valid C++17.
"""

    if "list(map(int, input().split()))" in python_code:
        return ARRAY_RULES
    return """
GENERAL PYTHON SEMANTICS:
Translate ONLY the supplied Python program.
Do not introduce arrays, sums, or additional input.
Preserve if/else branches exactly.
For range(n), iterate i from 0 to n-1.
For range(0), print nothing.
For while n > 0, execute zero iterations when n <= 0.
Preserve function definitions, return values, and calls.
Use long long for Python integer inputs.
Never use stoll(getline(cin)) or getline(cin, vector).
Use valid C++17 with all necessary headers.
"""


def fix_generated_cpp(code: str) -> str:
    # Fix incorrect trailing return type.
    code = re.sub(
        r'\blong long(\s+\w+\s*\([^;{}]*\)\s*->\s*long long\s*\{)',
        r'auto\1',
        code
    )

    # Fix missing newline consumption before getline.
    code = re.sub(
        r'(cin\s*>>\s*\w+\s*;)(\s*)(?=(?:string|std::string)\s+\w+\s*;\s*(?:std::)?getline\s*\()',
        lambda m: m.group(1)
        + "\n    cin.ignore(numeric_limits<streamsize>::max(), '\\n');"
        + m.group(2),
        code
    )

    return code

def _request_cpp(prompt: str, model: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m"
        },
        timeout=180
    )

    response.raise_for_status()

    cpp_code = response.json().get("response", "").strip()
    cpp_code = extract_cpp(cpp_code)
    cpp_code = fix_generated_cpp(cpp_code)

    if not cpp_code:
        raise ValueError(f"{model} returned an empty C++ response")

    return cpp_code


def convert_with_ollama(python_code: str) -> str:
    prompt = f"""
{semantic_rules(python_code)}

Convert the following Python code to valid C++17.

Rules:
- Return only C++ code.
- Use #include <bits/stdc++.h>
- Use using namespace std;
- Include int main() when appropriate.
- Preserve the original Python program's behavior.
- Do not include explanations or Markdown.
- Generate strictly valid C++17 code.
- Never use Python built-in functions directly in C++.
- For Python sum(), use std::accumulate().
- Store lists in a named std::vector before using begin() and end().
- Never use iterators from different temporary containers.
- Use long long for Python integer variables and input values.
- For Python int(input()), use: long long n; cin >> n;
- Never use stoll() for simple numeric input.
- For Python list(map(int, input().split())), use vector<long long>.
- Use accumulate(values.begin(), values.end(), 0LL) for long long sums.
- For complete text lines, declare string line and use getline(cin, line).
- Never use getline(cin) with only one argument.
- Never use stoi(getline(cin)).

Python code:
{python_code}
"""

    try:
        print("[OLLAMA] Trying primary model: " + MODEL, flush=True)
        return _request_cpp(prompt, MODEL)

    except Exception as primary_error:
        print(
            f"[OLLAMA] Primary model failed: {primary_error}",
            flush=True
        )
        print("[OLLAMA] Trying fallback model: " + FALLBACK_MODEL, flush=True)

        try:
            return _request_cpp(prompt, FALLBACK_MODEL)
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both Ollama models failed. "
                f"Primary ({MODEL}): {primary_error}. "
                f"Fallback ({FALLBACK_MODEL}): {fallback_error}"
            ) from fallback_error


def repair_cpp_with_ollama(
    python_code: str,
    cpp_code: str,
    compiler_error: str
) -> str:
    prompt = f"""
{semantic_rules(python_code)}

Repair the following C++17 code so that it compiles AND matches
the original Python behavior. The diagnostic may describe a
compilation error, runtime error, or stdout mismatch.

Original Python:
{python_code}

Incorrect C++:
{cpp_code}

Diagnostic:
{compiler_error}

Rules:
- Return only corrected C++17 code.
- Include all necessary headers.
- Preserve the original Python behavior.
- For Python sum(), use std::accumulate() with three arguments.
- For long long values, use:
  std::accumulate(values.begin(), values.end(), 0LL)
- Store values in a named vector before using begin() and end().
- Never use std::accumulate({{10, 20}}).
- For simple arithmetic like print(10 + 20), use:
  cout << (10 + 20) << endl;
- Check that every C++ function call has the correct arguments.
- Use long long for Python integer inputs and sums.
- For complete text lines, declare string line and use getline(cin, line).
- Never use getline(cin) with only one argument.
- Never use stoi(getline(cin)).
- Return valid C++17 code only. No Markdown or explanations.
"""

    print("[OLLAMA] Repairing with fallback model: " + FALLBACK_MODEL, flush=True)
    return _request_cpp(prompt, FALLBACK_MODEL)
