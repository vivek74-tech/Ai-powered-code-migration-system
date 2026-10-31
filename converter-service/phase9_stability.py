import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from phase9_runner import PHASES, get_status, run_phase

REPEATS = 3
OUTPUT = Path("phase9_stability_results.json")


def main():
    records = []
    total = len(PHASES) * REPEATS

    print("=== PHASE 9.2 STABILITY TEST ===", flush=True)
    print(f"Total phase executions: {total}", flush=True)

    for iteration in range(1, REPEATS + 1):
        print(f"\n=== ROUND {iteration}/{REPEATS} ===", flush=True)

        for name, script in PHASES.items():
            print(f"\nRunning {name}...", flush=True)

            # Avoid reading old JSON results.
            result_file = Path(f"{name}_results.json")
            if result_file.exists():
                result_file.unlink()

            if not Path(script).exists():
                result = {
                    "phase": name,
                    "status": "FAIL",
                    "error": f"Missing script: {script}",
                    "duration_seconds": 0,
                }
            else:
                result = run_phase(name, script)
                result["status"] = get_status(name, result)

            result["round"] = iteration
            records.append(result)

            print(
                f"{name}: {result['status']} "
                f"({result.get('duration_seconds', 0)}s)",
                flush=True,
            )

            # Save after each phase, even if later runs fail.
            OUTPUT.write_text(
                json.dumps(
                    {
                        "updated_at": datetime.now(
                            timezone.utc
                        ).isoformat(),
                        "completed": len(records),
                        "total": total,
                        "records": records,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

    print("\n=== PHASE 9.2 SUMMARY ===")

    all_passed = True

    for name in PHASES:
        phase_runs = [
            r for r in records if r["phase"] == name
        ]

        passed = sum(
            r["status"] == "PASS" for r in phase_runs
        )

        percentage = 100 * passed / len(phase_runs)

        print(
            f"{name}: {passed}/{len(phase_runs)} PASS "
            f"({percentage:.1f}%)"
        )

        if passed != len(phase_runs):
            all_passed = False

    passed_total = sum(
        r["status"] == "PASS" for r in records
    )

    print(
        f"\nOverall stability: "
        f"{passed_total}/{total} "
        f"({100 * passed_total / total:.1f}%)"
    )

    print(f"Results saved to {OUTPUT}")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
