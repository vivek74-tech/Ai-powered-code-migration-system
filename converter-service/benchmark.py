"""Run a benchmark manifest against the existing Docker worker.
Manifest: [{"id":"case1","python":"...","cpp":"...","inputs":["..."]}]
Do not run on untrusted benchmark data without the isolated worker.
"""
import json
import sys
from multi_validator import validate


def main():
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python benchmark.py benchmark.json report.json')
    with open(sys.argv[1], encoding='utf-8') as f:
        samples = json.load(f)
    reports = []
    for sample in samples:
        r = validate(sample['python'], sample['cpp'], sample.get('inputs'))
        reports.append({'id':sample['id'], **r})
    counts = {k:sum(r['status'] == k for r in reports) for k in ('PASS','FAIL','NOT VERIFIED')}
    summary = {'total_programs':len(reports), 'status_counts':counts,
               'verified_test_pass_rate': None if not reports else round(counts['PASS']/len(reports),4),
               'note':'Rate is benchmark program pass fraction, not universal conversion accuracy'}
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        json.dump({'summary':summary,'programs':reports}, f, indent=2)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
