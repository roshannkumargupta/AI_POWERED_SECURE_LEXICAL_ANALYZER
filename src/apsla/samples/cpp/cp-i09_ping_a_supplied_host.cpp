#include <cstdlib>
#include <iostream>
#include <string>
int main() { std::string host; std::getline(std::cin, host); std::system(("ping " + host).c_str()); }
