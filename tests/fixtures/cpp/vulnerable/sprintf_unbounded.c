#include <stdio.h>

int main(int argc, char *argv[]) {
    char buf[64];
    sprintf(buf, "User %s logged in", argv[1]);
    return 0;
}
