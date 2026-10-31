
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:1.5b"


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


def convert_with_ollama(python_code: str) -> str:
    prompt = f"""
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
- Use #include <bits/stdc++.h>.
- Return only compilable C++17 code.
- IMPORTANT: Python list(map(int, input().split())) consumes EVERY integer on exactly ONE input line, regardless of n. Use getline(cin, line), istringstream iss(line), and while (iss >> value) to fill vector<long long>. Never read only n elements unless Python explicitly slices to n.
- Python int is not a 32-bit C++ int. Use long long, stoll, vector<long long>, and accumulate(..., 0LL) for integer input and sums.
- C++ getline(cin) with one argument is invalid. Use string line; getline(cin, line); never stoi(getline(cin)).
- Preserve blank input lines and do not skip them with std::ws.

Python code:
{python_code}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=180
    )

    response.raise_for_status()

    cpp_code = response.json()["response"].strip()

    cpp_code = extract_cpp(cpp_code)

    return cpp_code


def repair_cpp_with_ollama(python_code: str, cpp_code: str, compiler_error: str) -> str:
    prompt = f"""
Fix the following C++17 code so that it compiles successfully.

Original Python:
{python_code}

Incorrect C++:
{cpp_code}

Compiler error:
{compiler_error}

Rules:
- Return only corrected C++17 code.
- Include all necessary headers.
- Preserve the original Python behavior.
- For Python sum(), use a valid C++17 implementation.
- If using std::accumulate(), always provide three arguments:
  std::accumulate(values.begin(), values.end(), 0)
- Example:
  std::vector<int> values = {{10, 20}};
  std::cout << std::accumulate(values.begin(), values.end(), 0) << std::endl;
- NEVER use std::accumulate({{10, 20}}) or std::accumulate({{10, 20}}, 0).
- For simple arithmetic like print(10 + 20), prefer std::cout << (10 + 20) << std::endl.
- Check that every C++ function call has the correct number of arguments.
- Do not include Markdown or explanations.
- IMPORTANT: Python list(map(int, input().split())) consumes EVERY integer on exactly ONE input line, regardless of n. Use getline(cin, line), istringstream iss(line), and while (iss >> value) to fill vector<long long>. Never read only n elements unless Python explicitly slices to n.
- Python int is not a 32-bit C++ int. Use long long, stoll, vector<long long>, and accumulate(..., 0LL) for integer input and sums.
- C++ getline(cin) with one argument is invalid. Use string line; getline(cin, line); never stoi(getline(cin)).
- Preserve blank input lines and do not skip them with std::ws.

"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=180
    )

    response.raise_for_status()

    fixed_cpp = response.json()["response"].strip()

    fixed_cpp = extract_cpp(fixed_cpp)

    return fixed_cpp
