#include "utils.h"
#include <string>

std::string stripBOM(const std::string& src) {
    if (src.rfind("\xEF\xBB\xBF", 0) == 0) {
        return src.substr(3);
    }
    return src;
}
