#include <stdio.h>

int main(int argc, char *argv[]) {
    char buf[64];
    fgets(buf, sizeof(buf), stdin);
    printf(buf);
    return 0;
}
