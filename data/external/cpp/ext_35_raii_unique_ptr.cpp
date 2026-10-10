#include <memory>
#include <string>
std::unique_ptr<std::string> createManagedString(const std::string& input) {
    return std::make_unique<std::string>(input);
}
