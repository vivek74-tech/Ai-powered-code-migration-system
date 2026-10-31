# Phase 2: Hybrid validator integration

Copy `auto_tests.py`, `multi_validator.py`, `benchmark.py`, and `dual_validator_v2.py` into `converter-service/` alongside your existing `converter.py` and `ollama_converter.py`.

Do **not** overwrite your current `dual_validator.py` yet. In a test route or script, import:

```python
from dual_validator_v2 import validate_dual_conversion
report = validate_dual_conversion('print(2+3)')
print(report['status'], report['method'])
```

Set `WORKER_URL` and `WORKER_API_KEY` as for your current worker. Both AST and Ollama candidates are tested independently. The AI path can attempt up to two compilation repairs. Reports include per-test evidence. The validator does not run untrusted code on the host; execution goes through your authenticated Docker worker.

**Limitations:** Automatically generated inputs are heuristic and currently support only simple top-level input shapes. Dynamic/dependent inputs need `manual_cases=[...]`; otherwise status is `NOT VERIFIED`. Silent programs also remain `NOT VERIFIED` unless you add an observable-behavior test. The AI converter is invoked even if AST passes. A `PASS` means only that selected tests passed. The legacy `validated` field reflects this limited meaning. No real Docker/Ollama integration run has been performed in this package.

For benchmark evaluation, run `python benchmark.py benchmark.json report.json` using the format documented in `benchmark.py`.
