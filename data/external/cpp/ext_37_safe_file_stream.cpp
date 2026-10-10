#include <fstream>
#include <string>
#include <vector>
std::vector<std::string> safeGrep(const std::string& path, const std::string& term) {
    std::ifstream file(path);
    std::vector<std::string> matches;
    std::string line;
    while (std::getline(file, line)) {
        if (line.find(term) != std::string::npos) matches.push_back(line);
    }
    return matches;
}
