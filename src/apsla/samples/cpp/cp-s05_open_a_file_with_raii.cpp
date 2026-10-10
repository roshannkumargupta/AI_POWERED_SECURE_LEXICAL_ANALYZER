#include <filesystem>
#include <fstream>
#include <string>
int main() { const std::filesystem::path path{"README.md"}; if (std::filesystem::exists(path)) { std::ifstream file(path); std::string line; std::getline(file, line); } }
