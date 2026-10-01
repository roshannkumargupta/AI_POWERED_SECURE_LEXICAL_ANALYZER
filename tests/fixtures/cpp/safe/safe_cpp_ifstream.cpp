#include <fstream>
#include <string>

void read_file() {
    std::ifstream f("config.txt");
    std::string line;
    if (f) {
        std::getline(f, line);
    }
}
