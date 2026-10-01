#include <stdio.h>

int main(int argc, char *argv[]) {
    char dest[32];
    if (argc > 1) {
        snprintf(dest, sizeof(dest), "%s", argv[1]);
    }
    return 0;
}
