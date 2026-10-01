#include <random>

int get_rand() {
    std::random_device rd;
    std::mt19937 gen(rd());
    return gen();
}
