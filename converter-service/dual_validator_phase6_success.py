from output_repair import repair_missing_newline
"""Dual converter with bounded compilation and stdout-mismatch repair.
Requires existing converter.py, ollama_converter.py and authenticated worker.
"""
from converter import PythonToCppConverter
from ollama_converter import convert_with_ollama, repair_cpp_with_ollama
from multi_validator import validate


def repair_missing_numeric_header(cpp_code, report):
    tests = report.get("tests", [])

    missing_accumulate = any(
        t.get("status") == "FAIL"
        and t.get("cpp_stage") == "compilation"
        and "accumulate" in str(t.get("cpp_error", ""))
        and "not declared" in str(t.get("cpp_error", ""))
        for t in tests
    )

    if not missing_accumulate:
        return cpp_code, False

    if "#include <numeric>" in cpp_code:
        return cpp_code, False

    return "#include <numeric>\n" + cpp_code, True


MAX_REPAIRS = 2


def _repair_diagnostic(report):
    """Only repair a proven C++ failure with a successful Python reference."""
    for test in report.get('tests', []):
        if test.get('status') != 'FAIL':
            continue
        if test.get('cpp_stage') == 'compilation':
            return 'C++ compilation error:\n' + str(test.get('cpp_error', ''))[:2500]
        if test.get('reason') == 'stdout mismatch':
            return (
                'C++ stdout differs from Python stdout. Preserve whitespace, '
                'spaces, and trailing newlines exactly.\n'
                'stdin: ' + repr(test.get('stdin', ''))[:500] + '\n'
                'expected Python stdout: ' + repr(test.get('python_output', ''))[:1000] + '\n'
                'actual C++ stdout: ' + repr(test.get('cpp_output', ''))[:1000]
            )
        if test.get('reason') == 'C++ compilation or execution failed':
            return ('C++ execution failed at stage ' + str(test.get('cpp_stage')) +
                    ':\n' + str(test.get('cpp_error', ''))[:2500])
    return None


def validate_dual_conversion(python_code, stdin='', manual_cases=None):
    cases = manual_cases if manual_cases is not None else ([stdin] if stdin else None)
    result = {'validated': False, 'status': 'NOT VERIFIED', 'method': None,
              'ast_cpp': None, 'ollama_cpp': None, 'ast_report': None,
              'ollama_report': None, 'errors': {}, 'repair_history': []}
    try:
        result['ast_cpp'] = PythonToCppConverter().convert(python_code, use_ai_fallback=False)
        result['ast_report'] = validate(python_code, result['ast_cpp'], cases)
    except Exception as exc:
        result['errors']['ast'] = str(exc)
    try:
        code = convert_with_ollama(python_code)
        for attempt in range(MAX_REPAIRS + 1):
            report = validate(python_code, code, cases)
            if report.get('status') != 'FAIL' or attempt == MAX_REPAIRS:
                break
            if report.get("status") == "FAIL":
                fixed_code, changed = repair_missing_newline(code, report)

                if changed:
                    fixed_report = validate(python_code, fixed_code, cases)

                    if fixed_report.get("status") == "PASS":
                        result["repair_history"].append({
                            "attempt": attempt + 1,
                            "type": "deterministic-newline-fix",
                            "before_status": "FAIL",
                            "outcome": "PASS after revalidation"
                        })
                        code = fixed_code
                        report = fixed_report
                        break

            fixed_code, changed = repair_missing_numeric_header(code, report)

            if changed:
                fixed_report = validate(python_code, fixed_code, cases)

                result["repair_history"].append({
                    "attempt": attempt + 1,
                    "type": "missing-numeric-header",
                    "before_status": report["status"],
                    "outcome": fixed_report["status"]
                })

                code = fixed_code
                report = fixed_report

                if report["status"] == "PASS":
                    break

            diagnostic = _repair_diagnostic(report)
            if not diagnostic:
                break
            history = {'attempt': attempt + 1, 'before_status': report['status'],
                       'diagnostic': diagnostic}
            result['repair_history'].append(history)
            try:
                repaired = repair_cpp_with_ollama(python_code, code, diagnostic)
                if not isinstance(repaired, str) or not repaired.strip() or repaired == code:
                    history['outcome'] = 'no usable change'
                    break
                code = repaired
                history['outcome'] = 'candidate generated; revalidation required'
            except Exception as exc:
                history['outcome'] = 'repair error: ' + str(exc)
                break
        result['ollama_cpp'] = code
        result['ollama_report'] = report
    except Exception as exc:
        result['errors']['ollama'] = str(exc)
    ast_status = (result['ast_report'] or {}).get('status')
    ai_status = (result['ollama_report'] or {}).get('status')
    if ast_status == 'PASS' and ai_status == 'PASS':
        result.update(status='PASS', validated=True, method='dual-validated')
    elif ast_status == 'PASS':
        result.update(status='PASS', validated=True, method='ast-based')
    elif ai_status == 'PASS':
        result.update(status='PASS', validated=True, method='ollama-fallback')
    elif ast_status == 'FAIL' and ai_status == 'FAIL':
        result['status'] = 'FAIL'
    result['validation_scope'] = 'selected tests only; not proof of semantic equivalence'
    return result
