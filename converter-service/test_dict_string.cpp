#include <bits/stdc++.h>
using namespace std;

std::string py_input() { std::string s; if (!std::getline(std::cin, s)) throw std::runtime_error("input failed"); return s; }

int py_dict_get(const std::map<int, int>& m, int k, int fallback) { auto it = m.find(k); return it == m.end() ? fallback : it->second; }

long long py_dict_get(const std::map<std::string, long long>& m, const std::string& k, long long fallback) { auto it = m.find(k); return it == m.end() ? fallback : it->second; }

int main() {
    std::map<std::string, long long> data = std::map<std::string, long long>{{"alice", 10}};
    std::string name = py_input();
    std::cout << py_dict_get(data, name, 0) << std::endl;
    return 0;
}