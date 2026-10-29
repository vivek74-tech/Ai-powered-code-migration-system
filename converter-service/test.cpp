#include <bits/stdc++.h>
using namespace std;

int main() {
    std::cout << [&]() { auto values = std::vector<int>{1, 2, 3, 4}; return std::accumulate(values.begin(), values.end(), 0); }() << std::endl;
    return 0;
}