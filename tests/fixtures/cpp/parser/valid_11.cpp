#include <cstdlib>

char* allocateBuffer(size_t size) {
    char* buf = (char*)malloc(size);
    if (!buf) {
        return nullptr;
    }
    return buf;
}
