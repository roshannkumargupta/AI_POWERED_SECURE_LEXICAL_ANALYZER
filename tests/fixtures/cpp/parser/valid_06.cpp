#include <vector>
#include <iostream>

void printItems(const std::vector<int>& items) {
    for (size_t i = 0; i < items.size(); ++i) {
        std::cout << items[i] << std::endl;
    }
}
