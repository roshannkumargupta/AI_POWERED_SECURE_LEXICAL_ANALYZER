#include <string.h>

int main() {
    char buf[64];
    strncpy(buf, "hello", 5);
    buf[5] = '\0';
    return 0;
}
