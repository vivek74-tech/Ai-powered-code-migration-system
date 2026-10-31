import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PHASES = {
    "phase5": "phase5_tests.py",
    "phase6": "phase6_tests.py",
    "phase7": "phase7_tests.py",
    "phase8": "phase8_tests.py",
}

TIMEOUT_SECONDS = 900


def run_phase(name, script):
    print(f"\nRunning {name}: {script}", flush=True)
    start = time.perf_counter()

    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )

        elapsed = round(time.perf_counter() - start, 2)

        return {
            "phase": name,
            "script": script,
            "exit_code": result.returncode,
            "duration_seconds": elapsed,
            "stdout": result.stdout[-12000:],
            "stderr": result.stderr[-4000:],
            "timed_out": False,
        }

    except subprocess.TimeoutExpired:
        return {
            "phase": name,
            "script": script,
            "exit_code": None,
            "duration_seconds": round(
                time.perf_counter() - start, 2
            ),
            "stdout": "",
            "stderr": "Phase execution timed out",
            "timed_out": True,
        }


def get_status(name, result):
    if result["exit_code"] != 0 or result["timed_out"]:
        return "FAIL"

    # Phase 6 prints its results after a summary heading.
    if name == "phase6":
        marker = "=== PHASE 6 SUMMARY ==="
        output = result.get("stdout", "")
        if marker not in output:
            return "FAIL"
        try:
            reports = json.loads(output.split(marker, 1)[1].strip())
            return (
                "PASS"
                if reports and all(
                    isinstance(r, dict) and r.get("status") == "PASS"
                    for r in reports.values()
                )
                else "FAIL"
            )
        except (json.JSONDecodeError, AttributeError):
            return "FAIL"

    # Phase 5 prints JSON directly.
    if name == "phase5":
        try:
            report = json.loads(result["stdout"])
            return "PASS" if report.get("status") == "PASS" else "FAIL"
        except json.JSONDecodeError:
            return "FAIL"

    # Phases 6–8 write structured JSON result files.
    path = Path(f"{name}_results.json")

    if not path.exists():
        return "FAIL"

    try:
        reports = json.loads(path.read_text(encoding="utf-8-sig"))
        return (
            "PASS"
            if reports and all(
                isinstance(r, dict) and r.get("status") == "PASS"
                for r in reports.values()
            )
            else "FAIL"
        )
    except (json.JSONDecodeError, OSError, AttributeError):
        return "FAIL"


def main():
    results = {}
    started_at = datetime.now(timezone.utc).isoformat()

    for name, script in PHASES.items():
        result_file = Path(f"{name}_results.json")

        # Prevent stale results from appearing as fresh successes.
        if name != "phase5" and result_file.exists():
            result_file.unlink()

        if not Path(script).exists():
            results[name] = {
                "status": "FAIL",
                "error": f"Missing script: {script}",
            }
            continue

        result = run_phase(name, script)
        result["status"] = get_status(name, result)
        results[name] = result

        print(
            f"{name}: {result['status']} "
            f"({result['duration_seconds']}s)",
            flush=True,
        )

        if result["status"] != "PASS":
            print(result.get("stderr") or result.get("stdout", "")[-2000:])

    summary = {
        "started_at": started_at,
        "total_phases": len(PHASES),
        "passed_phases": sum(
            r["status"] == "PASS" for r in results.values()
        ),
        "failed_phases": sum(
            r["status"] != "PASS" for r in results.values()
        ),
        "results": results,
    }

    Path("phase9_results.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\n=== PHASE 9 SUMMARY ===")
    print(
        f"PASS: {summary['passed_phases']}/{summary['total_phases']}"
    )
    print(f"FAIL: {summary['failed_phases']}")
    print("Results saved to phase9_results.json")

    if summary["failed_phases"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
