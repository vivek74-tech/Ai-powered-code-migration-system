#include <bits/stdc++.h>
using namespace std;

int py_dict_get(const std::map<int, int>& m, int k, int fallback) { auto it = m.find(k); return it == m.end() ? fallback : it->second; }

long long py_dict_get(const std::map<std::string, long long>& m, const std::string& k, long long fallback) { auto it = m.find(k); return it == m.end() ? fallback : it->second; }

int main() {
    std::map<std::string, long long> data = {};
    std::cout << py_dict_get(data, "alice", 0) << std::endl;
    return 0;
}