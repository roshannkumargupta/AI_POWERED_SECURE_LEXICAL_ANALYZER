#include <stdexcept>
#include <iostream>

void riskyOp() {
    try {
        throw std::runtime_error("failed");
    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
    }
}
