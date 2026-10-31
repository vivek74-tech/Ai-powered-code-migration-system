"""Multi-test validation using the existing authenticated Docker worker.

Never runs untrusted user code on the API host. Worker must enforce isolation.
"""
import os
import time
import requests
from auto_tests import generate_tests, TestCase
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from converter-service/.env
env_path = Path(__file__).resolve().parent / ".env"

load_dotenv(dotenv_path=env_path)

WORKER_URL = os.getenv('WORKER_URL', 'http://127.0.0.1:8002/execute')

WORKER_API_KEY = os.getenv("WORKER_API_KEY", "")

def log_time(stage, start_time):
    elapsed = time.time() - start_time
    print(f"[TIMING] {stage}: {elapsed:.2f} seconds", flush=True)

def execute(language, code, stdin=''):

    start_time = time.time()

    if not WORKER_API_KEY:
        raise RuntimeError("WORKER_API_KEY is missing")

    response = requests.post(
        WORKER_URL,
        json={
            "language": language,
            "code": code,
            "stdin": stdin
        },
        headers={
            "X-Worker-Key": WORKER_API_KEY
        },
        timeout=35
    )

    response.raise_for_status()

    result = response.json()

    log_time("Worker Execution", start_time)

    return result

def validate(python_code, cpp_code, manual_cases=None):
    plan = generate_tests(python_code)
    if manual_cases is not None:
        cases = [TestCase(f'manual-{i+1}', s) for i, s in enumerate(manual_cases)]
        source = 'manual'
    elif plan.supported:
        cases = plan.cases
        source = 'automatic'
    else:
        cases = []
        source = 'none'
    if not cases:
        return {'status':'NOT VERIFIED', 'reason':plan.reason if source == 'none' else 'No test cases provided', 'test_source':source, 'tests':[], 'passed':0, 'total':0}
    results = []
    for case in cases:
        record = {'name':case.name, 'stdin':case.stdin}
        try:
            start = time.monotonic()
            py = execute('python', python_code, case.stdin)
            record['python_seconds'] = round(time.monotonic() - start, 3)
            if not py.get('success'):
                record.update(status='NOT VERIFIED', reason='Python reference failed', python_error=py.get('error',''), python_stage=py.get('stage'))
            else:
                start = time.monotonic()
                cpp = execute('cpp', cpp_code, case.stdin)
                record['cpp_seconds'] = round(time.monotonic() - start, 3)
                if not cpp.get('success'):
                    record.update(status='FAIL', reason='C++ compilation or execution failed', cpp_error=cpp.get('error',''), cpp_stage=cpp.get('stage'))
                elif py.get('output','') != cpp.get('output',''):
                    record.update(status='FAIL', reason='stdout mismatch', python_output=py.get('output',''), cpp_output=cpp.get('output',''))
                else:
                    record.update(status='PASS', reason='Matching stdout and successful exit for this test')
        except requests.exceptions.Timeout:
            record.update(status='NOT VERIFIED', reason='Worker request timed out')
        except requests.exceptions.RequestException as exc:
            record.update(status='NOT VERIFIED', reason=f'Worker unavailable: {type(exc).__name__}')
        results.append(record)
    statuses = [r['status'] for r in results]
    status = 'FAIL' if 'FAIL' in statuses else 'PASS' if all(s == 'PASS' for s in statuses) else 'NOT VERIFIED'
    return {
        'status':status,
        'reason':'PASS means only that all selected tests passed; it does not prove equivalence',
        'test_source':source,
        'generation_note':plan.reason,
        'passed':statuses.count('PASS'),
        'total':len(results),
        'tests':results,
    }
