#include <bits/stdc++.h>
using namespace std;

int main() {
    long long n;
    cin >> n;

    std::vector<long long> arr(n);
    for (long long i = 0; i < n; i++) {
        cin >> arr[i];
    }

    for (int x : arr) {
        cout << x << endl;
    }

    return 0;
}
