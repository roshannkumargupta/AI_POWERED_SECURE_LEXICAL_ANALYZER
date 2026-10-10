#include <string>
#include <cstdlib>
namespace Config {
    std::string getSecret() {
        const char* val = std::getenv("API_SECRET_KEY");
        return val ? std::string(val) : "";
    }
}
