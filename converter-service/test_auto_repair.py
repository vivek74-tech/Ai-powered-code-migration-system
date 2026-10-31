
import json
from unittest.mock import patch

import dual_validator_v2

python_code = "n = int(input()); print(n * 2)"

wrong_cpp = """
#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    cout << n * 2;
    return 0;
}
"""

fixed_cpp = """
#include <iostream>
using namespace std;

int main() {
    int n;
    cin >> n;
    cout << n * 2 << endl;
    return 0;
}
"""

with patch.object(
    dual_validator_v2,
    "convert_with_ollama",
    return_value=wrong_cpp
), patch.object(
    dual_validator_v2,
    "repair_cpp_with_ollama",
    return_value=fixed_cpp
) as repair_mock:

    result = dual_validator_v2.validate_dual_conversion(
        python_code
    )

    print(json.dumps(result, indent=2))
    print("Repair calls:", repair_mock.call_count)

    assert result["ollama_report"]["status"] == "PASS"
    assert repair_mock.call_count >= 1

print("AUTO REPAIR TEST PASSED")
