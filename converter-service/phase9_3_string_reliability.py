import json
import time
from pathlib import Path
from datetime import datetime

from dual_validator_v2 import validate_dual_conversion


PYTHON_CODE = """
s = input()
print(s.upper())
print(len(s))
"""

TEST_CASES = [
    "\n",
    "hello world\n",
    "  hello  \n",
    "hello@123! test_C++\n",
]

REPEATS = 3

OUTPUT_FILE = Path("phase9_3_string_reliability_results.json")


def main():
    records = []

    print("=== PHASE 9.3 STRING RELIABILITY TEST ===")
    print(f"Generation attempts: {REPEATS}")
    print(f"Test cases per attempt: {len(TEST_CASES)}")

    for round_number in range(1, REPEATS + 1):
        print(f"\n=== ROUND {round_number}/{REPEATS} ===")

        start_time = time.perf_counter()

        try:
            result = validate_dual_conversion(
                PYTHON_CODE,
                manual_cases=TEST_CASES
            )

        except Exception as exc:
            result = {
                "status": "ERROR",
                "error": str(exc)
            }

        duration = round(time.perf_counter() - start_time, 2)

        ollama_report = result.get("ollama_report") or {}

        record = {
            "round": round_number,
            "status": result.get("status", "ERROR"),
            "method": result.get("method"),
            "duration_seconds": duration,
            "passed": ollama_report.get("passed", 0),
            "total": ollama_report.get("total", 0),
            "generated_cpp": result.get("ollama_cpp"),
            "ollama_report": ollama_report,
            "repair_history": result.get("repair_history", []),
            "errors": result.get("errors", {}),
            "error": result.get("error")
        }

        records.append(record)

        print("Status:", record["status"])
        print("Method:", record["method"])
        print(
            f"Test cases: {record['passed']}/{record['total']}"
        )
        print("Duration:", duration, "seconds")

        OUTPUT_FILE.write_text(
            json.dumps(
                {
                    "updated_at": datetime.now().isoformat(),
                    "completed_rounds": len(records),
                    "total_rounds": REPEATS,
                    "records": records
                },
                indent=2
            ),
            encoding="utf-8"
        )

    successful_rounds = sum(
        record["status"] == "PASS"
        and record["passed"] == len(TEST_CASES)
        and record["total"] == len(TEST_CASES)
        for record in records
    )

    print("\n=== PHASE 9.3 SUMMARY ===")
    print(f"Successful rounds: {successful_rounds}/{REPEATS}")
    print(f"Total test executions: {REPEATS * len(TEST_CASES)}")
    print(f"Results saved to: {OUTPUT_FILE}")

    if successful_rounds == REPEATS:
        print("OVERALL: PASS")
    else:
        print("OVERALL: FAIL / NOT FULLY RELIABLE")


if __name__ == "__main__":
    main()
