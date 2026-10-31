#include <bits/stdc++.h>
using namespace std;
int main() {
    string s;
    getline(cin, s);
    string upper = s;
    for (char &c : upper) {
        if (c >= 'a' && c <= 'z')
            c = static_cast<char>(c - 'a' + 'A');
    }
    cout << upper << '\n';
    cout << s.size() << '\n';
}
