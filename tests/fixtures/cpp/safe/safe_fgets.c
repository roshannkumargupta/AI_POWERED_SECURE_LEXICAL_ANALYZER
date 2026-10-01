#include <stdio.h>

int main() {
    char buf[64];
    fgets(buf, sizeof(buf), stdin);
    return 0;
}
