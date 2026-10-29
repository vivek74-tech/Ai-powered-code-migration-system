import os


def ollama_post(url, **kwargs):
    proxies = None
    if os.getenv("TS_AUTHKEY"):
        proxies = {
            "http": "socks5h://127.0.0.1:1055",
            "https": "socks5h://127.0.0.1:1055"
        }
    return requests.post(url, proxies=proxies, **kwargs)
import re
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = "qwen2.5-coder:1.5b"


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
Python code:
{python_code}
"""

    response = ollama_post(
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

    # Remove Markdown code fences if Ollama adds them.
    cpp_code = re.sub(
        r"^```(?:cpp|c\+\+)?\s*|\s*```$",
        "",
        cpp_code,
        flags=re.IGNORECASE
    ).strip()

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
"""

    response = ollama_post(
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

    fixed_cpp = re.sub(
        r"^```(?:cpp|c\+\+)?\s*|\s*```$",
        "",
        fixed_cpp,
        flags=re.IGNORECASE
    ).strip()

    return fixed_cpp

