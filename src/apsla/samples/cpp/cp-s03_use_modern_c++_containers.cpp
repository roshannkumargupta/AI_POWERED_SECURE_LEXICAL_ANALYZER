#include <memory>
#include <string>
#include <vector>
int main() { std::vector<std::unique_ptr<std::string>> items; items.push_back(std::make_unique<std::string>("ready")); for (const auto &item : items) (void)*item; }
